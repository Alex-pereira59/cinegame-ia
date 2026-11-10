"""Lógica de los tres servicios de IA y registro en la base de datos."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Consulta, Conversacion, ServicioIA, Usuario
from .llm import LLMClient
from .retrieval import format_context, retrieve
from .tools import build_toolset

log = logging.getLogger(__name__)

NO_INFO = "No tengo información suficiente en el catálogo"

DEFAULT_PROMPTS = {
    "chat_rag": (
        "Eres el asistente de CineGame AI, un catálogo de películas y videojuegos. "
        "Responde en español, de forma clara y breve, usando ÚNICAMENTE la información del CONTEXTO "
        "recuperado de la base de datos. Cita cada título que menciones con su identificador, por ejemplo [#12]. "
        f"Si el contexto no contiene datos para responder, di exactamente: \"{NO_INFO} para responder esa pregunta.\" "
        "y sugiere cómo reformularla. No inventes títulos, calificaciones ni datos."
    ),
    "recomendador": (
        "Eres un agente recomendador de películas y videojuegos. Trabaja en varios pasos usando herramientas:\n"
        "1) Identifica las preferencias del usuario (tipo, género, plataforma, calificación, gustos).\n"
        "2) Busca candidatos con buscar_catalogo. Si hay pocos o ninguno, amplía los filtros y vuelve a buscar.\n"
        "3) Para los 2 o 3 mejores candidatos consulta reseñas/recepción crítica con consultar_wikipedia "
        "(si no hay datos en español, intenta con idioma 'en').\n"
        "4) Compara los candidatos en una tabla Markdown (título, año, calificación del catálogo, puntos fuertes, "
        "puntos débiles según la crítica).\n"
        "5) Da una recomendación final justificada.\n"
        "Responde en español, cita los títulos del catálogo como [#id] y termina con una sección 'Fuentes' con los "
        "enlaces consultados. No inventes datos que no hayas obtenido de las herramientas."
    ),
    "novedades": (
        "Eres un agente de novedades de películas y videojuegos. Trabaja en varios pasos usando herramientas:\n"
        "1) Identifica el título o saga solicitado.\n"
        "2) Busca noticias recientes con buscar_noticias.\n"
        "3) Si las noticias son pocas, antiguas o no responden la pregunta, AMPLÍA la búsqueda: usa el nombre "
        "de la saga o del estudio, busca en inglés (idioma 'en') y/o consulta consultar_wikipedia para el contexto.\n"
        "4) Revisa si el título existe en el catálogo propio con buscar_catalogo y menciónalo.\n"
        "5) Redacta un resumen ordenado por fecha (lo más reciente primero) con viñetas.\n"
        "Responde en español, indica las fechas y termina con una sección 'Fuentes' con medio y enlace. "
        "Si no encuentras información fiable, dilo claramente."
    ),
}

AGENT_TOOLS = {
    "recomendador": ["buscar_catalogo", "consultar_wikipedia", "buscar_noticias"],
    "novedades": ["buscar_noticias", "consultar_wikipedia", "buscar_catalogo"],
}


@dataclass
class ServiceResult:
    respuesta: str
    fuentes: list[dict[str, Any]] = field(default_factory=list)
    pasos: list[dict[str, Any]] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_salida: int = 0
    suficiente: bool = True


# ---------------------------------------------------------------- conversación / memoria
def get_or_create_conversation(db: Session, user: Usuario, servicio: str, conversacion_id: int | None,
                               texto: str) -> Conversacion:
    if conversacion_id:
        conv = db.get(Conversacion, conversacion_id)
        if not conv or conv.usuario_id != user.id:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        if conv.servicio != servicio:
            raise HTTPException(status_code=400, detail="La conversación pertenece a otro servicio")
        return conv
    conv = Conversacion(usuario_id=user.id, servicio=servicio, titulo=texto.strip()[:80] or "Conversación")
    db.add(conv)
    db.flush()
    return conv


def memory_messages(conv: Conversacion, turns: int) -> list[dict]:
    """Últimos N intercambios de la conversación como mensajes user/assistant."""
    msgs: list[dict] = []
    for c in conv.consultas[-turns:]:
        msgs.append({"role": "user", "content": c.pregunta})
        msgs.append({"role": "assistant", "content": c.respuesta[:1500]})
    return msgs


def registrar_consulta(db: Session, user: Usuario, conv: Conversacion, servicio: str, pregunta: str,
                       res: ServiceResult) -> Consulta:
    c = Consulta(
        conversacion_id=conv.id,
        usuario_id=user.id,
        servicio=servicio,
        pregunta=pregunta,
        respuesta=res.respuesta,
        fuentes=json.dumps(res.fuentes, ensure_ascii=False),
        pasos=json.dumps(res.pasos, ensure_ascii=False),
        tokens_entrada=res.tokens_entrada,
        tokens_salida=res.tokens_salida,
        tokens_total=res.tokens_entrada + res.tokens_salida,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------------------------------------------------------------- Servicio 1: Chatbot RAG
def run_chat_rag(db: Session, llm: LLMClient, servicio: ServicioIA, conv: Conversacion,
                 pregunta: str, tipo: str = "todos") -> ServiceResult:
    s = get_settings()
    previous = conv.consultas[-1].pregunta if conv.consultas else None
    ret = retrieve(db, pregunta, tipo=tipo, k=s.rag_top_k, previous_question=previous)

    if ret.items:
        nota = ("Títulos recuperados por coincidencia con la pregunta."
                if ret.modo == "coincidencias" else "Títulos mejor calificados (la pregunta no tenía filtros).")
        contexto = f"CONTEXTO (tabla titulos; {nota}):\n{format_context(ret.items)}"
    else:
        contexto = "CONTEXTO: SIN RESULTADOS en la base de datos para esta pregunta."

    system = (servicio.prompt_sistema or DEFAULT_PROMPTS["chat_rag"]) + "\n\n" + contexto
    messages = [{"role": "system", "content": system}, *memory_messages(conv, s.memory_turns),
                {"role": "user", "content": pregunta}]
    r = llm.chat(messages, model=servicio.modelo or None, temperature=servicio.temperatura)

    respuesta = r.content.strip() or f"{NO_INFO} para responder esa pregunta."
    suficiente = bool(ret.items) and NO_INFO.lower() not in respuesta.lower()
    fuentes = [{"tipo": "base_de_datos", "tabla": "titulos", "id": t.id, "titulo": t.titulo,
                "citado": f"[#{t.id}]" in respuesta} for t in ret.items]
    pasos = [{"paso": 1, "herramienta": "recuperacion_sql",
              "argumentos": {"palabras_clave": ret.keywords, "tipo": tipo, "modo": ret.modo},
              "resumen": f"{len(ret.items)} títulos recuperados de la tabla titulos"}]
    return ServiceResult(respuesta, fuentes, pasos, r.tokens_in, r.tokens_out, suficiente)


# ---------------------------------------------------------------- Servicios 2 y 3: agentes
def _resumen_resultado(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"
    datos = result.get("datos")
    if isinstance(datos, list):
        nombres = [d.get("titulo") or d.get("titular", "") for d in datos[:4]]
        return f"{len(datos)} resultados: " + "; ".join(n[:60] for n in nombres if n)
    if isinstance(datos, dict):
        return f"Artículo: {datos.get('articulo', '')}"
    return result.get("nota", "Sin datos")


def run_agent(db: Session, llm: LLMClient, servicio: ServicioIA, conv: Conversacion, solicitud: str,
              tool_impls_override: dict[str, Callable[..., dict]] | None = None) -> ServiceResult:
    s = get_settings()
    specs, impls = build_toolset(db, AGENT_TOOLS[servicio.codigo])
    if tool_impls_override:
        impls.update(tool_impls_override)

    system = servicio.prompt_sistema or DEFAULT_PROMPTS[servicio.codigo]
    messages: list[dict] = [{"role": "system", "content": system}, *memory_messages(conv, s.memory_turns),
                            {"role": "user", "content": solicitud}]
    pasos: list[dict] = []
    fuentes: list[dict] = []
    t_in = t_out = 0
    final = ""

    for _ in range(max(1, servicio.max_pasos)):
        r = llm.chat(messages, tools=specs, model=servicio.modelo or None, temperature=servicio.temperatura)
        t_in += r.tokens_in
        t_out += r.tokens_out
        if not r.tool_calls:
            final = r.content
            break
        messages.append({
            "role": "assistant", "content": r.content or "",
            "tool_calls": [{"id": tc.id, "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments}} for tc in r.tool_calls],
        })
        for tc in r.tool_calls:
            try:
                args = json.loads(tc.arguments or "{}") or {}
            except json.JSONDecodeError:
                args = {}
            fn = impls.get(tc.name)
            try:
                result = fn(**args) if fn else {"error": f"Herramienta desconocida: {tc.name}"}
            except Exception as e:  # noqa: BLE001 - el error se devuelve al modelo para que se recupere
                log.warning("Fallo en herramienta %s: %s", tc.name, e)
                result = {"error": f"{type(e).__name__}: {e}"}
            pasos.append({"paso": len(pasos) + 1, "herramienta": tc.name, "argumentos": args,
                          "resumen": _resumen_resultado(result)})
            for f in result.get("fuentes", []):
                if f not in fuentes:
                    fuentes.append(f)
            payload = {k: v for k, v in result.items() if k != "fuentes"}
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(payload, ensure_ascii=False)[:3500]})
    else:
        # Se alcanzó el máximo de pasos: se pide la respuesta final sin herramientas.
        messages.append({"role": "user", "content": "Ya no uses herramientas. Elabora la respuesta final "
                                                    "con la información obtenida."})
        r = llm.chat(messages, model=servicio.modelo or None, temperature=servicio.temperatura)
        t_in += r.tokens_in
        t_out += r.tokens_out
        final = r.content

    final = (final or "").strip() or "No fue posible elaborar una respuesta con la información encontrada."
    return ServiceResult(final, fuentes, pasos, t_in, t_out, suficiente=bool(pasos))
