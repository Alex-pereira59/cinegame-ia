"""Genera database/01_schema.sql y database/02_datos.sql (PostgreSQL) a partir de los modelos y datos demo."""
from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.ai.services import DEFAULT_PROMPTS
from app.db import Base
from app import models  # noqa: F401
from app.seed_data import SERVICIOS, TITULOS, USUARIOS_DEMO
from app.security import hash_password

OUT = Path(__file__).resolve().parents[2] / "database"
dialect = postgresql.dialect()


def q(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


schema = ["-- CineGame AI - Script de creación de la base de datos (PostgreSQL)",
          "-- Ejecutar sobre una base vacía: psql \"$DATABASE_URL\" -f 01_schema.sql", "",
          "DROP TABLE IF EXISTS consultas, conversaciones, titulos, servicios_ia, usuarios CASCADE;", ""]
for table in Base.metadata.sorted_tables:
    schema.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";\n")
    for idx in table.indexes:
        schema.append(str(CreateIndex(idx).compile(dialect=dialect)).strip() + ";")
    schema.append("")
schema += [
    "-- Vista de apoyo para reportes (consumo por día, usuario y servicio)",
    "CREATE OR REPLACE VIEW v_consumo_diario AS",
    "SELECT DATE(c.creado_en) AS fecha, u.username AS usuario, c.servicio,",
    "       COUNT(*) AS consultas, SUM(c.tokens_entrada) AS tokens_entrada,",
    "       SUM(c.tokens_salida) AS tokens_salida, SUM(c.tokens_total) AS tokens_total",
    "FROM consultas c JOIN usuarios u ON u.id = c.usuario_id",
    "GROUP BY DATE(c.creado_en), u.username, c.servicio;",
]
(OUT / "01_schema.sql").write_text("\n".join(schema) + "\n", encoding="utf-8")

d = ["-- CineGame AI - Datos iniciales para demostración", "-- Contraseñas: admin / Admin123!   alex, maria / Usuario123!", ""]
d.append("INSERT INTO usuarios (username, nombre, email, password_hash, rol, activo, limite_tokens, creado_en) VALUES")
rows = [f"({q('admin')}, {q('Administrador')}, {q('admin@example.com')}, {q(hash_password('Admin123!'))}, 'admin', TRUE, 1000000, NOW())"]
for u, n, e, p, r, lim in USUARIOS_DEMO:
    rows.append(f"({q(u)}, {q(n)}, {q(e)}, {q(hash_password(p))}, {q(r)}, TRUE, {lim}, NOW())")
d.append(",\n".join(rows) + ";\n")
d.append("INSERT INTO servicios_ia (codigo, nombre, descripcion, activo, modelo, temperatura, max_pasos, prompt_sistema) VALUES")
d.append(",\n".join(f"({q(s['codigo'])}, {q(s['nombre'])}, {q(s['descripcion'])}, TRUE, NULL, {s['temperatura']}, "
                    f"{s['max_pasos']}, {q(DEFAULT_PROMPTS[s['codigo']])})" for s in SERVICIOS) + ";\n")
d.append("INSERT INTO titulos (tipo, titulo, genero, anio, calificacion, creador, plataforma, clasificacion, descripcion) VALUES")
d.append(",\n".join("(" + ", ".join(q(v) for v in t) + ")" for t in TITULOS) + ";")
(OUT / "02_datos.sql").write_text("\n".join(d) + "\n", encoding="utf-8")
print("SQL generado en", OUT)
