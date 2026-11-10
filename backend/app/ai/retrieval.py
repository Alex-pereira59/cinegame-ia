"""Recuperación (la "R" de RAG) sobre la tabla `titulos` de la base de datos.

Estrategia por palabras clave con normalización de acentos y raíces simples
("dramas" -> "drama", "aventuras" -> "avent"). Puntúa cada título según en qué
campo aparece la palabra y devuelve los K más relevantes.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Titulo

STOPWORDS = {
    # español común
    "que", "cual", "cuales", "cuál", "cuáles", "como", "cuando", "donde", "quien", "quienes",
    "los", "las", "una", "unos", "unas", "del", "por", "para", "con", "sin", "sobre", "entre",
    "hay", "son", "sea", "ser", "esta", "este", "estos", "estas", "ese", "esos", "esa", "esas",
    "tiene", "tienen", "tengo", "tenga", "algo", "alguna", "alguno", "algunas", "algunos", "mas",
    "más", "muy", "pero", "porque", "solo", "todo", "todos", "toda", "todas", "me", "mi", "mis",
    "puedes", "puede", "podrias", "quiero", "dame", "dime", "decir", "mostrar", "muestra", "lista",
    "listar", "hola", "gracias", "favor", "otro", "otra", "otros", "otras", "tambien", "también",
    "and", "the", "of", "sus", "les", "nos", "ver", "hacer", "mejor", "mejores", "peor",
    "mayor", "menor", "menos", "igual", "año", "años", "anio", "uno", "dos", "tres", "cuatro",
    "cinco", "seis", "siete", "ocho", "nueve", "diez", "reciente", "recientes", "nuevo", "nueva", "nuevos",
    "antiguo", "antigua", "viejo", "vieja", "ultimo", "último", "ultima", "última", "primero", "primera",
    "alto", "alta", "bajo", "baja", "esos", "ellos", "ellas", "eso", "ese",
    # del dominio (no ayudan a filtrar)
    "pelicula", "peliculas", "película", "películas", "film", "filmes", "videojuego", "videojuegos",
    "juego", "juegos", "titulo", "titulos", "título", "títulos", "catalogo", "catálogo",
    "recomienda", "recomiendas", "recomendar", "recomendacion", "calificacion", "calificación",
    "puntuacion", "nota", "genero", "género", "generos", "géneros", "tipo", "tipos",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def stem(word: str) -> str:
    """Raíz simple: recorta plurales y deja como máximo 5 caracteres."""
    if word.endswith("es") and len(word) > 5:
        word = word[:-2]
    elif word.endswith("s") and len(word) > 4:
        word = word[:-1]
    return word[:5] if len(word) > 5 else word


def keywords(question: str) -> list[str]:
    words = re.findall(r"[a-z0-9ñ]+", normalize(question))
    stop = {normalize(w) for w in STOPWORDS}
    out = []
    for w in words:
        if w in stop or (len(w) < 3 and not w.isdigit()):
            continue
        k = w if w.isdigit() else stem(w)
        if k not in out:
            out.append(k)
    return out


def detect_tipo(question: str) -> str | None:
    q = normalize(question)
    peli = bool(re.search(r"pelicul|film|cine|director", q))
    juego = bool(re.search(r"juego|videojuego|gamer|consola|playstation|xbox|nintendo|switch", q))
    if peli and not juego:
        return "pelicula"
    if juego and not peli:
        return "videojuego"
    return None


@dataclass
class Retrieved:
    items: list[Titulo]
    keywords: list[str]
    modo: str  # "coincidencias" | "general" | "sin_resultados"


def _score(t: Titulo, kws: list[str]) -> float:
    fields = [
        (normalize(t.titulo), 4.0),
        (normalize(t.genero), 4.0),
        (normalize(t.creador), 3.0),
        (normalize(t.plataforma or ""), 2.0),
        (normalize(t.clasificacion or ""), 1.0),
        (normalize(t.descripcion), 1.0),
    ]
    score = 0.0
    for k in kws:
        if k.isdigit():
            if str(t.anio) == k:
                score += 3
            continue
        for text, weight in fields:
            if k in text:
                score += weight
    return score


def retrieve(db: Session, question: str, tipo: str = "todos", k: int = 8,
             previous_question: str | None = None) -> Retrieved:
    if tipo == "todos":
        tipo = detect_tipo(question) or (detect_tipo(previous_question) if previous_question else None) or "todos"

    stmt = select(Titulo)
    if tipo in ("pelicula", "videojuego"):
        stmt = stmt.where(Titulo.tipo == tipo)
    rows = list(db.scalars(stmt))

    kws = keywords(question)
    prev_kws = keywords(previous_question) if previous_question else []
    # Memoria en la recuperación: si la pregunta es de seguimiento ("¿y cuál es la más reciente?")
    # se reutilizan las palabras clave de la pregunta anterior.
    if not kws and prev_kws:
        kws = prev_kws

    if not kws:
        top = sorted(rows, key=lambda t: t.calificacion, reverse=True)[:k]
        return Retrieved(top, kws, "general" if top else "sin_resultados")

    matched = [(t, sc) for t in rows if (sc := _score(t, kws)) > 0]
    if not matched and prev_kws and prev_kws != kws:
        kws = kws + [k for k in prev_kws if k not in kws]
        matched = [(t, sc) for t in rows if (sc := _score(t, kws)) > 0]
    matched.sort(key=lambda x: (x[1], x[0].calificacion), reverse=True)
    items = [t for t, _ in matched[:k]]
    return Retrieved(items, kws, "coincidencias" if items else "sin_resultados")


def format_context(items: list[Titulo]) -> str:
    lines = []
    for t in items:
        lines.append(
            f"[#{t.id}] {t.titulo} | tipo: {t.tipo} | género: {t.genero} | año: {t.anio} | "
            f"calificación: {t.calificacion} | {'director' if t.tipo == 'pelicula' else 'estudio'}: {t.creador}"
            + (f" | plataformas: {t.plataforma}" if t.plataforma else "")
            + (f" | clasificación: {t.clasificacion}" if t.clasificacion else "")
            + f" | descripción: {t.descripcion}"
        )
    return "\n".join(lines)
