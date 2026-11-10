"""Crea tablas y carga datos iniciales si la base está vacía.

Uso manual:  python -m app.seed
También se ejecuta automáticamente al iniciar la API.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai.services import DEFAULT_PROMPTS
from .config import get_settings
from .db import Base, SessionLocal, engine
from .models import ServicioIA, Titulo, Usuario
from .seed_data import SERVICIOS, TITULOS, USUARIOS_DEMO
from .security import hash_password


def seed(db: Session, demo_users: bool = True) -> None:
    s = get_settings()
    if not db.scalar(select(Usuario).where(Usuario.rol == "admin")):
        db.add(Usuario(username=s.admin_username, nombre="Administrador", email="admin@example.com",
                       password_hash=hash_password(s.admin_password), rol="admin", limite_tokens=1_000_000))
    if demo_users:
        for username, nombre, email, pwd, rol, limite in USUARIOS_DEMO:
            if not db.scalar(select(Usuario).where(Usuario.username == username)):
                db.add(Usuario(username=username, nombre=nombre, email=email, password_hash=hash_password(pwd),
                               rol=rol, limite_tokens=limite))
    for sv in SERVICIOS:
        if not db.scalar(select(ServicioIA).where(ServicioIA.codigo == sv["codigo"])):
            db.add(ServicioIA(**sv, prompt_sistema=DEFAULT_PROMPTS[sv["codigo"]], activo=True))
    if not db.scalar(select(Titulo).limit(1)):
        for t in TITULOS:
            db.add(Titulo(tipo=t[0], titulo=t[1], genero=t[2], anio=t[3], calificacion=t[4], creador=t[5],
                          plataforma=t[6], clasificacion=t[7], descripcion=t[8]))
    db.commit()


def init_db(demo_users: bool = True) -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db, demo_users)


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada")
