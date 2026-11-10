# Guía paso a paso — Proyecto final Programación Comercial

**CineGame AI**: aplicación web con 3 servicios de IA sobre un catálogo de películas y videojuegos.
Brayan Alexander, de León Pereira - 202308112

> Tiempo estimado: 4–6 horas. Sigue las fases en orden; en cada una se indica **qué captura tomar** para el PDF (📸).

---

## Fase 0 — Cuentas necesarias (15 min)

| Servicio | Para qué | Dónde |
|---|---|---|
| GitHub | Repositorio + CI/CD (Actions) | github.com |
| Groq | API key del modelo de IA (gratis) | console.groq.com → API Keys → *Create API Key* (empieza con `gsk_`) |
| Render | Hosting de la app y de PostgreSQL (gratis) | render.com → *Sign in with GitHub* |
| Postman | Consumidor externo | app de escritorio o web |
| Power BI Desktop | Reporte | Windows |

---

## Fase 1 — Correr el proyecto en tu máquina (45 min)

Necesitas Python 3.12, Node 20 y PostgreSQL (puedes usar Docker como en los laboratorios).

```bash
# 1. Base de datos PostgreSQL en Docker
docker run -d --name cinegame-db -e POSTGRES_USER=cinegame -e POSTGRES_PASSWORD=cinegame \
  -e POSTGRES_DB=cinegame -p 5432:5432 postgres:16

# 2. Crear tablas y datos con el script del proyecto (o hazlo desde DBeaver)
psql postgresql://cinegame:cinegame@localhost:5432/cinegame -f database/01_schema.sql
psql postgresql://cinegame:cinegame@localhost:5432/cinegame -f database/02_datos.sql
```
📸 DBeaver mostrando las 5 tablas y `SELECT * FROM titulos`.

```bash
# 3. Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # edita: DATABASE_URL y LLM_API_KEY (tu key de Groq)
pytest -v                          # deben pasar todas las pruebas
uvicorn app.main:app --reload      # API en http://localhost:8000/docs
```
📸 Terminal con `pytest -v` en verde.

```bash
# 4. Frontend (otra terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173 (redirige /api al backend)
```

Usuarios de prueba: `admin / Admin123!` · `alex / Usuario123!` · `maria / Usuario123!` (maria tiene límite de 3,000 tokens para demostrar el bloqueo).

> Sin `LLM_API_KEY` la app funciona en **modo demo** (respuestas simuladas). Úsalo solo para probar; las capturas finales deben ser con Groq.

---

## Fase 2 — Subir a GitHub (10 min)

```bash
git init
git add .
git commit -m "feat: proyecto final CineGame AI"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/cinegame-ai.git
git push -u origin main
```
El primer push ejecutará Actions: las pruebas pasarán y el job *deploy* fallará porque aún no existe el secreto de Render (es normal, lo configuras en la fase 3).

---

## Fase 3 — Desplegar en Render (30 min)

1. Render → **New → Blueprint** → elige el repositorio. Render lee `render.yaml` y crea:
   - `cinegame-db` (PostgreSQL)
   - `cinegame-ai` (servicio web Docker)
2. Te pedirá los valores marcados como secretos: `LLM_API_KEY` (tu `gsk_...`) y `ADMIN_PASSWORD`.
3. Espera el primer deploy (5–8 min). Al iniciar, la API crea las tablas y carga los datos si la base está vacía.
4. Abre `https://cinegame-ai-XXXX.onrender.com` y `.../docs`.

📸 Dashboard de Render con el servicio *Live* y la base de datos.
📸 La app publicada y Swagger (`/docs`).

> El plan gratuito “duerme” tras 15 min sin uso: la primera visita tarda ~50 s. Abre la app unos minutos antes de presentar.

**Opcional (evidencia del script SQL en la nube):** en Render → `cinegame-db` → *Connect* → copia la *External Database URL* y conéctate desde DBeaver.

---

## Fase 4 — CI/CD con GitHub Actions (20 min)

1. Render → servicio `cinegame-ai` → **Settings → Deploy Hook** → copia la URL.
2. Confirma que en *Settings → Build & Deploy* el **Auto-Deploy** está en **No** (el blueprint ya lo pone así) — así solo Actions despliega.
3. GitHub → repo → **Settings → Secrets and variables → Actions**:
   - *Secrets* → `RENDER_DEPLOY_HOOK_URL` = la URL del deploy hook
   - *Variables* → `APP_URL` = `https://cinegame-ai-XXXX.onrender.com`
4. Haz un cambio pequeño y súbelo:
   ```bash
   git commit --allow-empty -m "ci: probar despliegue" && git push
   ```
📸 Actions con **Pruebas automatizadas ✅ → Desplegar en Render ✅**.

**Evidencia de que NO despliega si fallan las pruebas** (muy recomendable):
```bash
git checkout -b prueba-fallo
# en backend/tests/test_consumo_historial.py cambia 700 por 701 en test_calculo_de_consumo
git commit -am "test: forzar fallo" && git push -u origin prueba-fallo
# en GitHub abre un Pull Request hacia main y haz merge (o push directo a main y luego reviertes)
```
📸 Actions con *Pruebas ❌* y *Desplegar* **omitido (skipped)**. Luego revierte el cambio (`git revert HEAD` y push).

---

## Fase 5 — Probar la aplicación y tomar evidencias (60 min)

Inicia sesión como **alex**:

| # | Qué hacer | 📸 |
|---|---|---|
| 1 | Chatbot → “¿Cuáles son 3 películas de drama?” | respuesta con `[#id]`, abrir *Pasos* y *Fuentes* |
| 2 | En la misma conversación: “¿Y cuál de ellas es la más antigua?” | memoria conversacional |
| 3 | Pestaña *Videojuegos* → “¿Qué juegos de disparos tienen calificación mayor a 8.5?” | filtro por categoría |
| 4 | “¿Qué telenovelas turcas tienen?” | etiqueta **Información insuficiente** |
| 5 | Agente recomendador → “Quiero un RPG largo para PS5 con buena historia, compárame opciones” | pasos: catálogo → Wikipedia → tabla comparativa → recomendación + fuentes |
| 6 | Agente de novedades → “¿Qué novedades hay sobre Hollow Knight: Silksong?” | pasos: noticias → ampliar búsqueda → resumen con fuentes |
| 7 | Historial y Consumo de tokens | tabla e indicador |

Inicia sesión como **maria** (límite 3,000) y haz 2–3 preguntas al recomendador hasta que aparezca **⛔ Límite de tokens alcanzado**. 📸

Inicia sesión como **admin**:

| # | Qué hacer | 📸 |
|---|---|---|
| 8 | Usuarios → crear, editar (cambiar límite de maria a 20,000), eliminar | CRUD |
| 9 | Servicios de IA → desactivar *Agente de novedades* → entrar como alex: aparece deshabilitado; volver a activar | activar/desactivar |
| 10 | Catálogo → crear “Hollow Knight: Silksong”, editar, preguntar por él en el chatbot | datos que alimentan el RAG |
| 11 | Reporte de uso con filtros por fecha, servicio y usuario | reporte web |

---

## Fase 6 — Consumo externo con Postman (20 min)

1. Postman → *Import* → `postman/CineGameAI.postman_collection.json`.
2. En la colección → *Variables* → `base_url` = tu URL de Render.
3. Ejecuta en orden: *Login (usuario alex)* → *Generar API key* → los de *Servicios de IA* → *Historial y consumo*.
4. *Login (admin)* y la carpeta *Administración*.
5. Opcional: *Run collection* para ver todos los tests en verde.

📸 Respuesta del chat RAG, del agente, el 401 sin token y el Runner.

---

## Fase 7 — Reporte en Power BI (40 min)

1. En la web (como **admin**) → *Acceso a la API* → **Generar mi API key** y cópiala (con la key de admin Power BI ve el uso de todos los usuarios).
2. Power BI Desktop → *Inicio → Transformar datos → Administrar parámetros → Nuevo*:
   - `BaseUrl` (Texto) = `https://cinegame-ai-XXXX.onrender.com`
   - `ApiKey` (Texto) = la key copiada
3. *Nuevo origen → Consulta en blanco → Editor avanzado* → pega `powerbi/consultas_detalle.pq` → renombra la consulta como `consultas_detalle`.
4. Si pide credenciales: **Anónimo** → Conectar. *Cerrar y aplicar*.
5. Crea las medidas de `powerbi/medidas.dax`.
6. Visuales (replican la página *Reporte de uso* de la web):
   - Segmentación **fecha** (estilo *Entre*) y segmentación **servicio_nombre**
   - Tarjetas: *Consultas* y *Tokens total*
   - Gráfico de columnas apiladas: eje `servicio_nombre`, valores *Tokens entrada* y *Tokens salida*
   - Gráfico de líneas: eje `fecha`, valor *Consultas*
   - Tabla: `servicio_nombre`, Consultas, Tokens entrada, Tokens salida, Tokens total
7. Guarda como `powerbi/CineGameAI.pbix`.

**Verificación de coincidencia:** pon el mismo filtro (p. ej. un día y un servicio) en la web y en Power BI.
📸 Las dos pantallas lado a lado con los mismos totales.

---

## Fase 8 — PDF de entrega

Usa `docs/propuesta.md` como base del texto y las imágenes de `docs/diagramas/`. Estructura sugerida:

1. Portada (curso, nombre, carné, fecha)
2. Propuesta: objetivo, usuarios, fuentes de información, servicios de IA
3. Arquitectura: `arquitectura.png`, `flujo_gui.png`, `flujo_powerbi.png` + explicación
4. Modelo de datos: `modelo_datos.png` + descripción de tablas
5. API REST: tabla de endpoints + captura de Swagger
6. Evidencias (capturas de las fases 1–7)
7. Pruebas automatizadas y CI/CD
8. Enlaces: repositorio, aplicación publicada, Swagger (`/docs`)

## Entregables (checklist)

- [ ] Enlace del repositorio Git (código, pruebas, `.github/workflows/ci-cd.yml`)
- [ ] `database/01_schema.sql` y `database/02_datos.sql`
- [ ] PDF con propuesta, arquitectura, modelo de datos y capturas
- [ ] Enlace de la app publicada y de Swagger `/docs`
- [ ] `CineGameAI.pbix`
- [ ] Demostración: web + Postman + Power BI

## Problemas comunes

| Síntoma | Solución |
|---|---|
| `429` de Groq / “rate limit” | El plan gratuito limita tokens por minuto. Espera 1 min, o en *Servicios de IA* pon otro modelo (p. ej. `llama-3.1-8b-instant`) para los agentes. |
| El agente responde sin usar herramientas | Baja la temperatura a 0.1–0.2 o reformula la solicitud pidiendo explícitamente “compara” / “busca noticias”. |
| Power BI: “acceso denegado” | Credenciales en **Anónimo** y verifica la API key (se invalida si la regeneras). |
| La app tarda en abrir | Render gratis se duerme; espera ~50 s. |
| Fechas con un día de diferencia | `APP_TIMEZONE=America/Guatemala` (ya viene en `render.yaml`). |
