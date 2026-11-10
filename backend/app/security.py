"""Autenticación (JWT o API key), roles y control de consumo de tokens."""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import Consulta, ServicioIA, Usuario

bearer_scheme = HTTPBearer(auto_error=False, description="Token JWT obtenido en /api/auth/login")
apikey_scheme = APIKeyHeader(name="X-API-Key", auto_error=False,
                             description="API key para consumidores externos (Power BI, Postman)")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def create_token(user: Usuario) -> str:
    s = get_settings()
    payload = {
        "sub": str(user.id),
        "rol": user.rol,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def new_api_key() -> str:
    return "cg_" + secrets.token_urlsafe(32)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    api_key: str | None = Security(apikey_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado: envíe 'Authorization: Bearer <token>' o 'X-API-Key'",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = None
    if creds and creds.credentials:
        s = get_settings()
        try:
            data = jwt.decode(creds.credentials, s.jwt_secret, algorithms=[s.jwt_algorithm])
            user = db.get(Usuario, int(data["sub"]))
        except (jwt.PyJWTError, KeyError, ValueError):
            raise unauthorized
    elif api_key:
        user = db.scalar(select(Usuario).where(Usuario.api_key == api_key))
    if not user:
        raise unauthorized
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    return user


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.rol != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return user


# ---------- Consumo de tokens ----------
def tokens_usados(db: Session, usuario_id: int) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(Consulta.tokens_total), 0)).where(Consulta.usuario_id == usuario_id)
    )
    return int(total or 0)


def tokens_restantes(db: Session, user: Usuario) -> int:
    return max(user.limite_tokens - tokens_usados(db, user.id), 0)


def verificar_servicio_y_cuota(db: Session, user: Usuario, codigo_servicio: str) -> ServicioIA:
    """Se ejecuta ANTES de llamar al modelo: servicio activo y tokens disponibles."""
    servicio = db.scalar(select(ServicioIA).where(ServicioIA.codigo == codigo_servicio))
    if not servicio:
        raise HTTPException(status_code=404, detail=f"Servicio '{codigo_servicio}' no existe")
    if not servicio.activo:
        raise HTTPException(status_code=403, detail=f"El servicio '{servicio.nombre}' está desactivado")
    if tokens_restantes(db, user) <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Límite de tokens alcanzado ({user.limite_tokens}). Solicite al administrador más cuota.",
        )
    return servicio
