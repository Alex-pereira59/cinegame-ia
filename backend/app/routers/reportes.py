"""Consumo de tokens y reportes (los mismos endpoints alimentan la web y Power BI)."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Consulta, Usuario
from ..schemas import ConsumoUsuario, ReporteFila, ReporteOut
from ..security import get_current_user, require_admin, tokens_usados
from .historial import rango

router = APIRouter(tags=["Consumo y reportes"])


def _filtros(stmt, user, desde, hasta, servicio, usuario_id):
    if user.rol != "admin":
        usuario_id = user.id  # un usuario solo ve sus datos
    if usuario_id:
        stmt = stmt.where(Consulta.usuario_id == usuario_id)
    if servicio:
        stmt = stmt.where(Consulta.servicio == servicio)
    d, h = rango(desde, hasta)
    if d:
        stmt = stmt.where(Consulta.creado_en >= d)
    if h:
        stmt = stmt.where(Consulta.creado_en < h)
    return stmt, usuario_id


def calcular_consumo(db: Session, u: Usuario) -> ConsumoUsuario:
    usados = tokens_usados(db, u.id)
    rows = db.execute(
        select(Consulta.servicio, func.count(Consulta.id), func.sum(Consulta.tokens_total))
        .where(Consulta.usuario_id == u.id).group_by(Consulta.servicio).order_by(Consulta.servicio)
    ).all()
    return ConsumoUsuario(
        usuario_id=u.id, username=u.username, limite_tokens=u.limite_tokens, tokens_usados=usados,
        tokens_restantes=max(u.limite_tokens - usados, 0),
        porcentaje=round(100 * usados / u.limite_tokens, 2) if u.limite_tokens else 100.0,
        por_servicio=[{"servicio": s, "consultas": n, "tokens_total": int(t or 0)} for s, n, t in rows],
    )


@router.get("/api/consumo/me", response_model=ConsumoUsuario, summary="Mi consumo de tokens y cuota disponible")
def mi_consumo(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    return calcular_consumo(db, user)


@router.get("/api/consumo/usuarios", response_model=list[ConsumoUsuario], summary="Consumo de todos (admin)")
def consumo_usuarios(_: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return [calcular_consumo(db, u) for u in db.scalars(select(Usuario).order_by(Usuario.id))]


@router.get("/api/reportes/consumo", response_model=ReporteOut,
            summary="Reporte de consultas y consumo acumulado por servicio y por día",
            description="Filtros opcionales: desde, hasta (YYYY-MM-DD), servicio, usuario_id (solo admin).")
def reporte_consumo(desde: date | None = None, hasta: date | None = None, servicio: str | None = None,
                    usuario_id: int | None = None, user: Usuario = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    base = select(Consulta.servicio, func.count(Consulta.id), func.sum(Consulta.tokens_entrada),
                  func.sum(Consulta.tokens_salida), func.sum(Consulta.tokens_total))
    stmt, uid = _filtros(base, user, desde, hasta, servicio, usuario_id)
    filas = [ReporteFila(servicio=s, consultas=n, tokens_entrada=int(ti or 0), tokens_salida=int(to or 0),
                         tokens_total=int(tt or 0))
             for s, n, ti, to, tt in db.execute(stmt.group_by(Consulta.servicio).order_by(Consulta.servicio))]

    dia = func.date(Consulta.creado_en)
    stmt_dia, _ = _filtros(select(dia, func.count(Consulta.id), func.sum(Consulta.tokens_total)),
                           user, desde, hasta, servicio, usuario_id)
    por_dia = [{"fecha": str(f), "consultas": n, "tokens_total": int(t or 0)}
               for f, n, t in db.execute(stmt_dia.group_by(dia).order_by(dia))]
    return ReporteOut(
        filtros={"desde": desde, "hasta": hasta, "servicio": servicio, "usuario_id": uid},
        total_consultas=sum(f.consultas for f in filas), total_tokens=sum(f.tokens_total for f in filas),
        por_servicio=filas, por_dia=por_dia,
    )


@router.get("/api/reportes/consultas-detalle", summary="Filas planas para Power BI",
            description="Una fila por consulta (fecha, usuario, servicio, tokens). Power BI aplica los "
                        "filtros de fecha y servicio con segmentaciones sobre estos datos.")
def consultas_detalle(desde: date | None = None, hasta: date | None = None, servicio: str | None = None,
                      usuario_id: int | None = None, limite: int = Query(10000, ge=1, le=50000),
                      user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    base = (select(Consulta.id, Consulta.creado_en, Usuario.username, Consulta.servicio,
                   Consulta.tokens_entrada, Consulta.tokens_salida, Consulta.tokens_total)
            .join(Usuario, Usuario.id == Consulta.usuario_id))
    stmt, _ = _filtros(base, user, desde, hasta, servicio, usuario_id)
    rows = db.execute(stmt.order_by(Consulta.creado_en).limit(limite)).all()
    return [{"consulta_id": i, "fecha": f.date().isoformat(), "fecha_hora": f.isoformat(timespec="seconds"),
             "usuario": u, "servicio": s, "tokens_entrada": ti, "tokens_salida": to, "tokens_total": tt}
            for i, f, u, s, ti, to, tt in rows]
