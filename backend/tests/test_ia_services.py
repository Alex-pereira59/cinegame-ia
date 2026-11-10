from app.ai import services
from app.ai.tools import build_toolset as _real
from app.ai.retrieval import keywords, retrieve
from app.db import SessionLocal


def test_recuperacion_por_genero():
    with SessionLocal() as db:
        r = retrieve(db, "¿Cuáles son 3 películas de drama?", tipo="todos")
        assert r.items and all(t.tipo == "pelicula" for t in r.items)
        assert all("drama" in t.genero.lower() for t in r.items)
        r = retrieve(db, "juegos de disparos con calificación mayor a 8.5")
        assert r.items and all("Disparos" in t.genero for t in r.items[:3])


def test_keywords_normaliza_acentos_y_plurales():
    assert "avent" in keywords("Aventuras épicas")
    assert "pelicula" not in keywords("películas de terror")


def test_chat_rag_envia_contexto_y_registra(client, user_h, llm):
    r = client.post("/api/ia/chat", headers=user_h, json={"pregunta": "Recomiéndame películas de terror"})
    assert r.status_code == 200, r.text
    body = r.json()
    system = llm.calls[0]["messages"][0]["content"]
    assert "CONTEXTO" in system and "El conjuro" in system  # el contexto viene de la BD
    assert body["fuentes"] and body["fuentes"][0]["tabla"] == "titulos"
    assert body["tokens_total"] == 120
    hist = client.get("/api/historial/consultas", headers=user_h).json()
    assert hist[0]["pregunta"] == "Recomiéndame películas de terror"


def test_chat_rag_indica_informacion_insuficiente(client, user_h, llm):
    llm.default = "No tengo información suficiente en el catálogo para responder esa pregunta."
    r = client.post("/api/ia/chat", headers=user_h, json={"pregunta": "¿Qué opinas de la telenovela xyzqwerty?"})
    body = r.json()
    assert body["suficiente"] is False
    assert "SIN RESULTADOS" in llm.calls[0]["messages"][0]["content"]


def test_memoria_conversacional(client, user_h, llm):
    r1 = client.post("/api/ia/chat", headers=user_h, json={"pregunta": "Videojuegos de RPG"}).json()
    client.post("/api/ia/chat", headers=user_h,
                json={"pregunta": "¿Y cuál es el más reciente?", "conversacion_id": r1["conversacion_id"]})
    segunda = llm.calls[1]["messages"]
    roles = [m["role"] for m in segunda]
    assert roles == ["system", "user", "assistant", "user"]  # incluye el intercambio anterior
    assert segunda[1]["content"] == "Videojuegos de RPG"
    # la recuperación reutiliza las palabras clave de la pregunta anterior
    assert "Baldur" in segunda[0]["content"]


def test_conversacion_ajena_no_accesible(client, user_h, llm):
    from tests.conftest import login
    r1 = client.post("/api/ia/chat", headers=user_h, json={"pregunta": "drama"}).json()
    maria = login(client, "maria", "Usuario123!")
    r = client.post("/api/ia/chat", headers=maria, json={"pregunta": "x", "conversacion_id": r1["conversacion_id"]})
    assert r.status_code == 404


def test_agente_recomendador_varios_pasos(client, user_h, llm, monkeypatch):
    monkeypatch.setattr(services, "build_toolset", _toolset_sin_red(services.build_toolset))
    llm.script = [
        ("buscar_catalogo", {"tipo": "videojuego", "genero": "RPG"}),
        ("consultar_wikipedia", {"titulo": "Elden Ring"}),
        "| Título | ... |\nRecomiendo **Elden Ring [#31]**.",
    ]
    r = client.post("/api/ia/recomendador", headers=user_h, json={"solicitud": "Un RPG difícil"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [p["herramienta"] for p in body["pasos"]] == ["buscar_catalogo", "consultar_wikipedia"]
    assert any(f.get("url", "").startswith("https://es.wikipedia.org") for f in body["fuentes"])
    assert any(f.get("tabla") == "titulos" for f in body["fuentes"])
    assert "Elden Ring" in body["respuesta"]
    assert body["tokens_total"] == 3 * 120  # tres llamadas al modelo
    # el resultado de la herramienta se envió de vuelta al modelo
    assert llm.calls[1]["messages"][-1]["role"] == "tool"


def test_agente_novedades_amplia_busqueda(client, user_h, llm, monkeypatch):
    monkeypatch.setattr(services, "build_toolset", _toolset_sin_red(services.build_toolset))
    llm.script = [
        ("buscar_noticias", {"consulta": "Hollow Knight Silksong"}),
        ("buscar_noticias", {"consulta": "Team Cherry", "idioma": "en"}),
        "Resumen de novedades con fuentes.",
    ]
    r = client.post("/api/ia/novedades", headers=user_h, json={"solicitud": "Novedades de Silksong"})
    assert len(r.json()["pasos"]) == 2


def test_agente_error_de_herramienta_no_rompe(client, user_h, llm, monkeypatch):
    def toolset(db, names):
        specs, impls = _real(db, names)
        impls["buscar_noticias"] = lambda **kw: (_ for _ in ()).throw(TimeoutError("sin red"))
        return specs, impls
    monkeypatch.setattr(services, "build_toolset", toolset)
    llm.script = [("buscar_noticias", {"consulta": "x"}), "No encontré información fiable."]
    r = client.post("/api/ia/novedades", headers=user_h, json={"solicitud": "x"})
    assert r.status_code == 200
    assert r.json()["pasos"][0]["resumen"].startswith("Error")



def _toolset_sin_red(real):
    def toolset(db, names):
        specs, impls = real(db, names)
        impls["consultar_wikipedia"] = lambda titulo, idioma="es": {
            "datos": {"articulo": titulo, "resumen": "Resumen", "recepcion_critica": "Aclamado por la crítica"},
            "fuentes": [{"tipo": "web", "nombre": f"Wikipedia: {titulo}",
                         "url": f"https://es.wikipedia.org/wiki/{titulo.replace(' ', '_')}"}]}
        impls["buscar_noticias"] = lambda consulta, idioma="es", limite=6: {
            "datos": [{"titular": f"Noticia sobre {consulta}", "medio": "Medio", "fecha": "2026-11-01", "url": "https://n.example"}],
            "fuentes": [{"tipo": "noticia", "nombre": "Medio", "url": "https://n.example"}]}
        return specs, impls
    return toolset
