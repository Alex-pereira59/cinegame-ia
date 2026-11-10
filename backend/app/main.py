"""Punto de entrada de la API (FastAPI). Documentación: /docs (Swagger) y /redoc."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import auth, catalogo, historial, ia, reportes, servicios, usuarios
from .seed import init_db

logging.basicConfig(level=logging.INFO)

DESCRIPTION = """
API de **CineGame AI**: aplicación web con servicios de Inteligencia Artificial sobre un catálogo
de películas y videojuegos.

### Autenticación
1. `POST /api/auth/login` → copie `access_token` y pulse **Authorize** (HTTPBearer), o
2. genere una API key con `POST /api/auth/api-key` y envíela en el header `X-API-Key`
   (recomendado para Power BI y Postman).

### Servicios de IA
* `POST /api/ia/chat` – chatbot con RAG y memoria conversacional.
* `POST /api/ia/recomendador` – agente de varios pasos (catálogo → reseñas → comparación → recomendación).
* `POST /api/ia/novedades` – agente de varios pasos (noticias → ampliar búsqueda → resumen con fuentes).

Antes de cada solicitud se verifica que el servicio esté activo y que el usuario tenga tokens disponibles
(si no, responde **429**).
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("SKIP_INIT_DB") != "1":
        init_db(demo_users=os.getenv("SEED_DEMO_USERS", "1") == "1")
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", description=DESCRIPTION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, usuarios.router, servicios.router, catalogo.router, ia.router, historial.router,
          reportes.router):
    app.include_router(r)


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok"}


# ---- Frontend React compilado (mismo dominio que la API) ----
STATIC_DIR = Path(os.getenv("STATIC_DIR", Path(__file__).resolve().parent.parent / "static"))
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        file = STATIC_DIR / full_path
        if full_path and file.is_file():
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
