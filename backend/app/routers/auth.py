from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Usuario
from ..schemas import ApiKeyOut, LoginIn, TokenOut, UsuarioOut
from ..security import create_token, get_current_user, new_api_key, verify_password

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOut, summary="Iniciar sesión y obtener token JWT")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(Usuario).where(Usuario.username == data.username))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    return TokenOut(access_token=create_token(user), usuario=UsuarioOut.model_validate(user))


@router.post("/logout", summary="Cerrar sesión", description=(
    "Los tokens JWT no guardan estado en el servidor: el cliente elimina el token. "
    "El endpoint existe para dejar registro y mantener un contrato uniforme."))
def logout(user: Usuario = Depends(get_current_user)):
    return {"mensaje": f"Sesión cerrada para {user.username}"}


@router.get("/me", response_model=UsuarioOut, summary="Usuario autenticado")
def me(user: Usuario = Depends(get_current_user)):
    return user


@router.post("/api-key", response_model=ApiKeyOut, summary="Generar (o regenerar) mi API key",
             description="La API key permite consumir la API desde Postman o Power BI con el header X-API-Key.")
def generar_api_key(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    user.api_key = new_api_key()
    db.commit()
    return ApiKeyOut(api_key=user.api_key)
