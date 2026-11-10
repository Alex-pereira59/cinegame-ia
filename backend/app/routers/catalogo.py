from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Titulo
from ..schemas import TituloBase, TituloOut, TituloUpdate
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/api/catalogo", tags=["Catálogo (datos del RAG)"])


@router.get("", response_model=list[TituloOut], dependencies=[Depends(get_current_user)])
def listar(tipo: str | None = Query(None, pattern="^(pelicula|videojuego)$"),
           q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Titulo).order_by(Titulo.tipo, Titulo.titulo)
    if tipo:
        stmt = stmt.where(Titulo.tipo == tipo)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Titulo.titulo.ilike(like), Titulo.genero.ilike(like), Titulo.creador.ilike(like)))
    return list(db.scalars(stmt))


@router.post("", response_model=TituloOut, status_code=201, dependencies=[Depends(require_admin)])
def crear(data: TituloBase, db: Session = Depends(get_db)):
    t = Titulo(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/{titulo_id}", response_model=TituloOut, dependencies=[Depends(require_admin)])
def actualizar(titulo_id: int, data: TituloUpdate, db: Session = Depends(get_db)):
    t = db.get(Titulo, titulo_id)
    if not t:
        raise HTTPException(404, "Título no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{titulo_id}", status_code=204, dependencies=[Depends(require_admin)])
def eliminar(titulo_id: int, db: Session = Depends(get_db)):
    t = db.get(Titulo, titulo_id)
    if not t:
        raise HTTPException(404, "Título no encontrado")
    db.delete(t)
    db.commit()
