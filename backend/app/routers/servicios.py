from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ServicioIA, Usuario
from ..schemas import ServicioOut, ServicioUpdate
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/api/servicios", tags=["Administración: servicios de IA"])


@router.get("", response_model=list[ServicioOut], summary="Listar servicios (usuarios ven solo los activos)")
def listar(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    stmt = select(ServicioIA).order_by(ServicioIA.id)
    if user.rol != "admin":
        stmt = stmt.where(ServicioIA.activo.is_(True))
    return list(db.scalars(stmt))


@router.put("/{servicio_id}", response_model=ServicioOut,
            summary="Configurar servicio: activar/desactivar, modelo, temperatura, pasos, prompt")
def actualizar(servicio_id: int, data: ServicioUpdate, db: Session = Depends(get_db),
               _: Usuario = Depends(require_admin)):
    s = db.get(ServicioIA, servicio_id)
    if not s:
        raise HTTPException(404, "Servicio no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s
