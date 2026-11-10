"""Esquemas Pydantic de entrada/salida de la API."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: "UsuarioOut"


# ---------- Usuarios ----------
class UsuarioOut(ORM):
    id: int
    username: str
    nombre: str
    email: str | None = None
    rol: str
    activo: bool
    limite_tokens: int
    creado_en: datetime


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=1, max_length=120)
    email: str | None = None
    password: str = Field(min_length=6)
    rol: Literal["admin", "usuario"] = "usuario"
    activo: bool = True
    limite_tokens: int = Field(default=50000, ge=0)


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, min_length=6)
    rol: Literal["admin", "usuario"] | None = None
    activo: bool | None = None
    limite_tokens: int | None = Field(default=None, ge=0)


class ApiKeyOut(BaseModel):
    api_key: str


# ---------- Servicios IA ----------
class ServicioOut(ORM):
    id: int
    codigo: str
    nombre: str
    descripcion: str
    activo: bool
    modelo: str | None
    temperatura: float
    max_pasos: int
    prompt_sistema: str


class ServicioUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None
    modelo: str | None = None
    temperatura: float | None = Field(default=None, ge=0, le=2)
    max_pasos: int | None = Field(default=None, ge=1, le=12)
    prompt_sistema: str | None = None


# ---------- Catálogo ----------
class TituloBase(BaseModel):
    tipo: Literal["pelicula", "videojuego"]
    titulo: str = Field(min_length=1, max_length=200)
    genero: str
    anio: int = Field(ge=1880, le=2100)
    calificacion: float = Field(ge=0, le=10)
    creador: str
    plataforma: str | None = None
    clasificacion: str | None = None
    descripcion: str


class TituloOut(TituloBase, ORM):
    id: int


class TituloUpdate(BaseModel):
    tipo: Literal["pelicula", "videojuego"] | None = None
    titulo: str | None = None
    genero: str | None = None
    anio: int | None = None
    calificacion: float | None = Field(default=None, ge=0, le=10)
    creador: str | None = None
    plataforma: str | None = None
    clasificacion: str | None = None
    descripcion: str | None = None


# ---------- IA ----------
class ChatIn(BaseModel):
    pregunta: str = Field(min_length=1, max_length=2000)
    conversacion_id: int | None = None
    tipo: Literal["pelicula", "videojuego", "todos"] = "todos"


class AgenteIn(BaseModel):
    solicitud: str = Field(min_length=1, max_length=2000)
    conversacion_id: int | None = None


class IAOut(BaseModel):
    consulta_id: int
    conversacion_id: int
    servicio: str
    respuesta: str
    fuentes: list[dict[str, Any]] = []
    pasos: list[dict[str, Any]] = []
    suficiente: bool = True
    tokens_entrada: int
    tokens_salida: int
    tokens_total: int
    tokens_restantes: int


# ---------- Historial ----------
class ConsultaOut(ORM):
    id: int
    conversacion_id: int | None
    usuario_id: int
    username: str | None = None
    servicio: str
    pregunta: str
    respuesta: str
    fuentes: list[dict[str, Any]] = []
    pasos: list[dict[str, Any]] = []
    tokens_entrada: int
    tokens_salida: int
    tokens_total: int
    creado_en: datetime


class ConversacionOut(ORM):
    id: int
    servicio: str
    titulo: str
    creado_en: datetime
    total_consultas: int = 0


class ConversacionDetalle(ConversacionOut):
    consultas: list[ConsultaOut] = []


# ---------- Consumo ----------
class ConsumoUsuario(BaseModel):
    usuario_id: int
    username: str
    limite_tokens: int
    tokens_usados: int
    tokens_restantes: int
    porcentaje: float
    por_servicio: list[dict[str, Any]]


class ReporteFila(BaseModel):
    servicio: str
    consultas: int
    tokens_entrada: int
    tokens_salida: int
    tokens_total: int


class ReporteOut(BaseModel):
    filtros: dict[str, Any]
    total_consultas: int
    total_tokens: int
    por_servicio: list[ReporteFila]
    por_dia: list[dict[str, Any]]


TokenOut.model_rebuild()
