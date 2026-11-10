from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Usuario
from ..schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from ..security import hash_password, require_admin

router = APIRouter(prefix="/api/usuarios", tags=["Administración: usuarios"],
                   dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db)):
    return list(db.scalars(select(Usuario).order_by(Usuario.id)))


@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener(usuario_id: int, db: Session = Depends(get_db)):
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    return u


@router.post("", response_model=UsuarioOut, status_code=201)
def crear(data: UsuarioCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Usuario).where(Usuario.username == data.username)):
        raise HTTPException(409, "El nombre de usuario ya existe")
    u = Usuario(**data.model_dump(exclude={"password"}), password_hash=hash_password(data.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.put("/{usuario_id}", response_model=UsuarioOut,
            summary="Actualizar usuario (incluye límite de tokens, rol y estado)")
def actualizar(usuario_id: int, data: UsuarioUpdate, db: Session = Depends(get_db),
               admin: Usuario = Depends(require_admin)):
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    cambios = data.model_dump(exclude_unset=True)
    if u.id == admin.id and (cambios.get("rol") == "usuario" or cambios.get("activo") is False):
        raise HTTPException(400, "No puede quitarse el rol de administrador ni desactivarse a sí mismo")
    if "password" in cambios:
        pwd = cambios.pop("password")
        if pwd:
            u.password_hash = hash_password(pwd)
    for k, v in cambios.items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{usuario_id}", status_code=204)
def eliminar(usuario_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    if u.id == admin.id:
        raise HTTPException(400, "No puede eliminarse a sí mismo")
    db.delete(u)
    db.commit()
