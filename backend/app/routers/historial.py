import json
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consulta, Conversacion, Usuario
from ..schemas import ConsultaOut, ConversacionDetalle, ConversacionOut
from ..security import get_current_user

router = APIRouter(prefix="/api/historial", tags=["Historial"])


def consulta_out(c: Consulta) -> ConsultaOut:
    def load(s):
        try:
            return json.loads(s) if s else []
        except json.JSONDecodeError:
            return []
    return ConsultaOut(
        id=c.id, conversacion_id=c.conversacion_id, usuario_id=c.usuario_id,
        username=c.usuario.username if c.usuario else None, servicio=c.servicio,
        pregunta=c.pregunta, respuesta=c.respuesta, fuentes=load(c.fuentes), pasos=load(c.pasos),
        tokens_entrada=c.tokens_entrada, tokens_salida=c.tokens_salida, tokens_total=c.tokens_total,
        creado_en=c.creado_en,
    )


def rango(desde: date | None, hasta: date | None):
    d = datetime.combine(desde, time.min) if desde else None
    h = datetime.combine(hasta + timedelta(days=1), time.min) if hasta else None
    return d, h


@router.get("/conversaciones", response_model=list[ConversacionOut], summary="Mis conversaciones")
def mis_conversaciones(servicio: str | None = None, user: Usuario = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    stmt = (select(Conversacion, func.count(Consulta.id))
            .outerjoin(Consulta, Consulta.conversacion_id == Conversacion.id)
            .where(Conversacion.usuario_id == user.id)
            .group_by(Conversacion.id).order_by(Conversacion.creado_en.desc()))
    if servicio:
        stmt = stmt.where(Conversacion.servicio == servicio)
    return [ConversacionOut(id=c.id, servicio=c.servicio, titulo=c.titulo, creado_en=c.creado_en,
                            total_consultas=n) for c, n in db.execute(stmt)]


@router.get("/conversaciones/{conv_id}", response_model=ConversacionDetalle)
def detalle_conversacion(conv_id: int, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversacion, conv_id)
    if not conv or (conv.usuario_id != user.id and user.rol != "admin"):
        raise HTTPException(404, "Conversación no encontrada")
    return ConversacionDetalle(id=conv.id, servicio=conv.servicio, titulo=conv.titulo, creado_en=conv.creado_en,
                               total_consultas=len(conv.consultas),
                               consultas=[consulta_out(c) for c in conv.consultas])


@router.delete("/conversaciones/{conv_id}", status_code=204)
def borrar_conversacion(conv_id: int, user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Oculta la conversación de la lista, pero conserva las consultas para el control de consumo."""
    conv = db.get(Conversacion, conv_id)
    if not conv or conv.usuario_id != user.id:
        raise HTTPException(404, "Conversación no encontrada")
    for c in conv.consultas:
        c.conversacion_id = None
    db.flush()
    db.delete(conv)
    db.commit()


@router.get("/consultas", response_model=list[ConsultaOut],
            summary="Consultas registradas (usuario: las propias; admin: todas, con filtros)")
def consultas(desde: date | None = None, hasta: date | None = None, servicio: str | None = None,
              usuario_id: int | None = None, limite: int = Query(200, ge=1, le=5000),
              user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Consulta).order_by(Consulta.creado_en.desc(), Consulta.id.desc()).limit(limite)
    if user.rol != "admin":
        usuario_id = user.id
    if usuario_id:
        stmt = stmt.where(Consulta.usuario_id == usuario_id)
    if servicio:
        stmt = stmt.where(Consulta.servicio == servicio)
    d, h = rango(desde, hasta)
    if d:
        stmt = stmt.where(Consulta.creado_en >= d)
    if h:
        stmt = stmt.where(Consulta.creado_en < h)
    return [consulta_out(c) for c in db.scalars(stmt)]
