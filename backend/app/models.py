"""Modelo de datos (tablas) de la aplicación."""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow():
    """Fecha/hora local de la aplicación (APP_TIMEZONE, por defecto America/Guatemala)."""
    from .config import get_settings
    return datetime.now(ZoneInfo(get_settings().app_timezone)).replace(tzinfo=None)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(20), default="usuario")  # admin | usuario
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    limite_tokens: Mapped[int] = mapped_column(Integer, default=50000)
    api_key: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ServicioIA(Base):
    __tablename__ = "servicios_ia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)  # chat_rag | recomendador | novedades
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)  # vacío = modelo por defecto
    temperatura: Mapped[float] = mapped_column(Float, default=0.3)
    max_pasos: Mapped[int] = mapped_column(Integer, default=6)
    prompt_sistema: Mapped[str] = mapped_column(Text, default="")


class Titulo(Base):
    """Catálogo de películas y videojuegos (fuente del RAG)."""
    __tablename__ = "titulos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)  # pelicula | videojuego
    titulo: Mapped[str] = mapped_column(String(200))
    genero: Mapped[str] = mapped_column(String(100))
    anio: Mapped[int] = mapped_column(Integer)
    calificacion: Mapped[float] = mapped_column(Float)
    creador: Mapped[str] = mapped_column(String(150))  # director o estudio
    plataforma: Mapped[str | None] = mapped_column(String(150), nullable=True)
    clasificacion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    descripcion: Mapped[str] = mapped_column(Text)


class Conversacion(Base):
    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    servicio: Mapped[str] = mapped_column(String(50))
    titulo: Mapped[str] = mapped_column(String(200))
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    consultas: Mapped[list["Consulta"]] = relationship(
        back_populates="conversacion", order_by="Consulta.id", cascade="all, delete-orphan"
    )


class Consulta(Base):
    """Cada pregunta/respuesta registrada con su consumo de tokens."""
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="CASCADE"), index=True, nullable=True
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    servicio: Mapped[str] = mapped_column(String(50), index=True)
    pregunta: Mapped[str] = mapped_column(Text)
    respuesta: Mapped[str] = mapped_column(Text)
    fuentes: Mapped[str] = mapped_column(Text, default="")  # JSON con fuentes usadas
    pasos: Mapped[str] = mapped_column(Text, default="")  # JSON con pasos del agente
    tokens_entrada: Mapped[int] = mapped_column(Integer, default=0)
    tokens_salida: Mapped[int] = mapped_column(Integer, default=0)
    tokens_total: Mapped[int] = mapped_column(Integer, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    conversacion: Mapped[Conversacion | None] = relationship(back_populates="consultas")
    usuario: Mapped[Usuario] = relationship()
