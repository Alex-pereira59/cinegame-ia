"""Herramientas que pueden usar los agentes.

- buscar_catalogo: consulta la base de datos propia.
- consultar_wikipedia: ficha y sección de recepción/crítica (reseñas) de un título.
- buscar_noticias: noticias recientes desde Google News (RSS, sin API key).

Cada herramienta devuelve {"datos": ..., "fuentes": [...]} para poder citar fuentes.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.parse import quote

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Titulo
from .retrieval import normalize

HEADERS = {"User-Agent": "CineGameAI/1.0 (alex59@umes.edu.gt; proyecto universitario UMES) python-httpx"}
TIMEOUT = 12


# ---------------------------------------------------------------- catálogo (BD)
def buscar_catalogo(db: Session, tipo: str | None = None, genero: str | None = None,
                    texto: str | None = None, calificacion_minima: float | None = None,
                    limite: int = 8) -> dict[str, Any]:
    stmt = select(Titulo)
    if tipo in ("pelicula", "videojuego"):
        stmt = stmt.where(Titulo.tipo == tipo)
    if calificacion_minima is not None:
        stmt = stmt.where(Titulo.calificacion >= float(calificacion_minima))
    rows = list(db.scalars(stmt))

    def contains(field: str | None, needle: str) -> bool:
        return normalize(needle)[:5] in normalize(field or "")

    if genero:
        rows = [t for t in rows if contains(t.genero, genero)]
    if texto:
        words = [w for w in re.findall(r"\w+", texto) if len(w) > 2]
        rows = [t for t in rows if any(
            contains(t.titulo, w) or contains(t.descripcion, w) or contains(t.creador, w)
            or contains(t.plataforma, w) for w in words
        )] if words else rows
    rows.sort(key=lambda t: t.calificacion, reverse=True)
    rows = rows[: max(1, min(int(limite or 8), 15))]
    datos = [
        {"id": t.id, "titulo": t.titulo, "tipo": t.tipo, "genero": t.genero, "anio": t.anio,
         "calificacion": t.calificacion, "creador": t.creador, "plataforma": t.plataforma,
         "descripcion": t.descripcion[:200]}
        for t in rows
    ]
    return {
        "datos": datos,
        "total": len(datos),
        "nota": "Sin coincidencias: amplíe los filtros (quite el género o baje la calificación mínima)."
        if not datos else "",
        "fuentes": [{"tipo": "base_de_datos", "tabla": "titulos", "id": d["id"], "titulo": d["titulo"]}
                    for d in datos],
    }


# ---------------------------------------------------------------- Wikipedia
def _wiki_search(title: str, lang: str) -> str | None:
    r = httpx.get(
        f"https://{lang}.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": title, "srlimit": 1, "format": "json"},
        headers=HEADERS, timeout=TIMEOUT,
    )
    r.raise_for_status()
    hits = r.json().get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def _extract_reception(text: str) -> str:
    """Busca la sección de recepción/crítica dentro del texto plano del artículo."""
    m = re.search(r"\n==+\s*(Recepción|Recepcion|Crítica|Critica|Reception|Critical reception)[^=]*==+\n",
                  text, re.IGNORECASE)
    if not m:
        return ""
    section = text[m.end():]
    nxt = re.search(r"\n==\s*[^=]+==\n", section)
    return section[: nxt.start() if nxt else 1500].strip()[:1500]


def consultar_wikipedia(titulo: str, idioma: str = "es") -> dict[str, Any]:
    lang = idioma if idioma in ("es", "en") else "es"
    page = _wiki_search(titulo, lang)
    if not page:
        return {"datos": None, "nota": f"No se encontró '{titulo}' en Wikipedia ({lang}). "
                                       "Intente con el título en inglés (idioma='en').", "fuentes": []}
    r = httpx.get(
        f"https://{lang}.wikipedia.org/w/api.php",
        params={"action": "query", "prop": "extracts", "explaintext": 1, "titles": page,
                "format": "json", "redirects": 1},
        headers=HEADERS, timeout=TIMEOUT,
    )
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    text = next(iter(pages.values()), {}).get("extract", "") if pages else ""
    resumen = text.split("\n==", 1)[0].strip()[:900]
    recepcion = _extract_reception("\n" + text)
    url = f"https://{lang}.wikipedia.org/wiki/{quote(page.replace(' ', '_'))}"
    return {
        "datos": {"articulo": page, "resumen": resumen,
                  "recepcion_critica": recepcion or "El artículo no tiene sección de recepción."},
        "fuentes": [{"tipo": "web", "nombre": f"Wikipedia ({lang}): {page}", "url": url}],
    }


# ---------------------------------------------------------------- Noticias
def buscar_noticias(consulta: str, idioma: str = "es", limite: int = 6) -> dict[str, Any]:
    if idioma == "en":
        params = {"q": consulta, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    else:
        params = {"q": consulta, "hl": "es-419", "gl": "US", "ceid": "US:es-419"}
    r = httpx.get("https://news.google.com/rss/search", params=params, headers=HEADERS,
                  timeout=TIMEOUT, follow_redirects=True)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    for it in root.iter("item"):
        title = it.findtext("title") or ""
        source = it.findtext("source") or ""
        pub = it.findtext("pubDate") or ""
        try:
            fecha = parsedate_to_datetime(pub).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            fecha = pub
        items.append({"titular": title, "medio": source, "fecha": fecha, "url": it.findtext("link") or ""})
        if len(items) >= max(1, min(int(limite or 6), 10)):
            break
    return {
        "datos": items,
        "total": len(items),
        "nota": "Pocas noticias: amplíe la búsqueda (nombre de la saga, otro idioma o términos más generales)."
        if len(items) < 2 else "",
        "fuentes": [{"tipo": "noticia", "nombre": f"{i['medio']}: {i['titular'][:90]}", "url": i["url"],
                     "fecha": i["fecha"]} for i in items],
    }


# ---------------------------------------------------------------- Especificación para el modelo
SPEC_CATALOGO = {
    "type": "function",
    "function": {
        "name": "buscar_catalogo",
        "description": "Busca películas o videojuegos en el catálogo propio (base de datos). "
                       "Devuelve título, género, año, calificación (0-10), director/estudio y plataformas.",
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": ["pelicula", "videojuego"]},
                "genero": {"type": "string", "description": "Ej.: drama, aventura, acción, terror, RPG"},
                "texto": {"type": "string", "description": "Palabras del título, descripción o creador"},
                "calificacion_minima": {"type": "number"},
                "limite": {"type": "integer", "description": "Máximo de resultados (1-15)"},
            },
        },
    },
}
SPEC_WIKIPEDIA = {
    "type": "function",
    "function": {
        "name": "consultar_wikipedia",
        "description": "Obtiene el resumen y la recepción de la crítica (reseñas) de un título desde Wikipedia.",
        "parameters": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string"},
                "idioma": {"type": "string", "enum": ["es", "en"], "description": "Usar 'en' si en español no hay datos"},
            },
            "required": ["titulo"],
        },
    },
}
SPEC_NOTICIAS = {
    "type": "function",
    "function": {
        "name": "buscar_noticias",
        "description": "Busca noticias recientes en Google News sobre un título, saga, estudio o tema.",
        "parameters": {
            "type": "object",
            "properties": {
                "consulta": {"type": "string"},
                "idioma": {"type": "string", "enum": ["es", "en"]},
                "limite": {"type": "integer"},
            },
            "required": ["consulta"],
        },
    },
}


def build_toolset(db: Session, names: list[str]) -> tuple[list[dict], dict[str, Callable[..., dict]]]:
    available = {
        "buscar_catalogo": (SPEC_CATALOGO, lambda **kw: buscar_catalogo(db, **kw)),
        "consultar_wikipedia": (SPEC_WIKIPEDIA, consultar_wikipedia),
        "buscar_noticias": (SPEC_NOTICIAS, buscar_noticias),
    }
    specs = [available[n][0] for n in names]
    impls = {n: available[n][1] for n in names}
    return specs, impls
