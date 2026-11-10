"""Endpoints de los servicios de IA (usados por la web y por consumidores externos)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..ai.llm import LLMClient, get_llm
from ..ai.services import get_or_create_conversation, registrar_consulta, run_agent, run_chat_rag
from ..db import get_db
from ..models import Usuario
from ..schemas import AgenteIn, ChatIn, IAOut
from ..security import get_current_user, tokens_restantes, verificar_servicio_y_cuota

router = APIRouter(prefix="/api/ia", tags=["Servicios de IA"])

ERRORES = {
    401: {"description": "No autenticado"},
    403: {"description": "Servicio desactivado o usuario inactivo"},
    429: {"description": "Límite de tokens alcanzado"},
}


def _out(db, user, consulta, res, servicio) -> IAOut:
    return IAOut(
        consulta_id=consulta.id, conversacion_id=consulta.conversacion_id, servicio=servicio,
        respuesta=res.respuesta, fuentes=res.fuentes, pasos=res.pasos, suficiente=res.suficiente,
        tokens_entrada=consulta.tokens_entrada, tokens_salida=consulta.tokens_salida,
        tokens_total=consulta.tokens_total, tokens_restantes=tokens_restantes(db, user),
    )


@router.post("/chat", response_model=IAOut, responses=ERRORES,
             summary="Chatbot con RAG sobre el catálogo (con memoria conversacional)",
             description="Recupera títulos relevantes de la tabla `titulos`, los envía como contexto al modelo y "
                         "devuelve la respuesta con sus fuentes. Envíe `conversacion_id` para mantener el contexto.")
def chat(data: ChatIn, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db),
         llm: LLMClient = Depends(get_llm)):
    servicio = verificar_servicio_y_cuota(db, user, "chat_rag")
    conv = get_or_create_conversation(db, user, "chat_rag", data.conversacion_id, data.pregunta)
    res = run_chat_rag(db, llm, servicio, conv, data.pregunta, data.tipo)
    c = registrar_consulta(db, user, conv, "chat_rag", data.pregunta, res)
    return _out(db, user, c, res, "chat_rag")


@router.post("/recomendador", response_model=IAOut, responses=ERRORES,
             summary="Agente recomendador (busca candidatos, consulta reseñas, compara y recomienda)")
def recomendador(data: AgenteIn, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db),
                 llm: LLMClient = Depends(get_llm)):
    servicio = verificar_servicio_y_cuota(db, user, "recomendador")
    conv = get_or_create_conversation(db, user, "recomendador", data.conversacion_id, data.solicitud)
    res = run_agent(db, llm, servicio, conv, data.solicitud)
    c = registrar_consulta(db, user, conv, "recomendador", data.solicitud, res)
    return _out(db, user, c, res, "recomendador")


@router.post("/novedades", response_model=IAOut, responses=ERRORES,
             summary="Agente de novedades (busca noticias, amplía la búsqueda si falta información y resume)")
def novedades(data: AgenteIn, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db),
              llm: LLMClient = Depends(get_llm)):
    servicio = verificar_servicio_y_cuota(db, user, "novedades")
    conv = get_or_create_conversation(db, user, "novedades", data.conversacion_id, data.solicitud)
    res = run_agent(db, llm, servicio, conv, data.solicitud)
    c = registrar_consulta(db, user, conv, "novedades", data.solicitud, res)
    return _out(db, user, c, res, "novedades")
