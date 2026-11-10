# CineGame AI

Aplicación web con servicios de Inteligencia Artificial sobre un catálogo de películas y videojuegos.
Proyecto final — Programación Comercial.

- **Chatbot con RAG** sobre PostgreSQL, con fuentes y memoria conversacional.
- **Agente recomendador**: catálogo → reseñas (Wikipedia) → comparación → recomendación.
- **Agente de novedades**: noticias (Google News) → ampliación de búsqueda → resumen con fuentes.
- Login con roles, CRUD de usuarios/servicios/catálogo, límites de tokens, historial y reportes.
- API REST documentada en `/docs`, consumible desde Postman y Power BI.
- Pruebas con pytest y CI/CD en GitHub Actions con despliegue en Render.

## Estructura

```
backend/        API FastAPI (app/), pruebas (tests/)
frontend/       React + Vite
database/       01_schema.sql, 02_datos.sql (PostgreSQL)
docs/           propuesta, arquitectura, modelo de datos (diagramas)
postman/        colección para consumo externo
powerbi/        consultas Power Query y medidas DAX
.github/        workflow de CI/CD
Dockerfile, render.yaml, docker-compose.yml
```

## Inicio rápido

```bash
cd backend && pip install -r requirements-dev.txt && cp .env.example .env
pytest                              # pruebas
uvicorn app.main:app --reload       # http://localhost:8000/docs
cd ../frontend && npm install && npm run dev   # http://localhost:5173
```

O todo con Docker: `docker compose up --build` → http://localhost:8000

Usuarios demo: `admin / Admin123!`, `alex / Usuario123!`, `maria / Usuario123!`.

Guía completa de despliegue, Postman y Power BI: [GUIA.md](GUIA.md).
