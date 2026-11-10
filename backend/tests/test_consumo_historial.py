from datetime import date

from tests.conftest import login


def _preguntar(client, h, texto="películas de drama"):
    return client.post("/api/ia/chat", headers=h, json={"pregunta": texto})


def test_calculo_de_consumo(client, user_h, llm):
    llm.tokens = (300, 50)
    _preguntar(client, user_h)
    _preguntar(client, user_h)
    c = client.get("/api/consumo/me", headers=user_h).json()
    assert c["tokens_usados"] == 700
    assert c["tokens_restantes"] == 50000 - 700
    assert c["por_servicio"] == [{"servicio": "chat_rag", "consultas": 2, "tokens_total": 700}]


def test_bloqueo_al_alcanzar_limite(client, admin_h, llm):
    maria = login(client, "maria", "Usuario123!")  # límite 3000
    llm.tokens = (2900, 200)
    assert _preguntar(client, maria).status_code == 200  # 3100 >= 3000
    r = _preguntar(client, maria)
    assert r.status_code == 429
    assert len(llm.calls) == 1  # el modelo NO se llamó en la solicitud bloqueada
    # el admin amplía el límite y se desbloquea
    uid = next(u["id"] for u in client.get("/api/usuarios", headers=admin_h).json() if u["username"] == "maria")
    client.put(f"/api/usuarios/{uid}", headers=admin_h, json={"limite_tokens": 10000})
    assert _preguntar(client, maria).status_code == 200


def test_servicio_desactivado(client, admin_h, user_h, llm):
    servs = client.get("/api/servicios", headers=admin_h).json()
    sid = next(s["id"] for s in servs if s["codigo"] == "chat_rag")
    client.put(f"/api/servicios/{sid}", headers=admin_h, json={"activo": False})
    assert _preguntar(client, user_h).status_code == 403
    assert all(s["codigo"] != "chat_rag" for s in client.get("/api/servicios", headers=user_h).json())


def test_historial_propio_y_general(client, admin_h, user_h, llm):
    maria = login(client, "maria", "Usuario123!")
    _preguntar(client, user_h, "drama")
    _preguntar(client, maria, "terror")
    propio = client.get("/api/historial/consultas", headers=user_h).json()
    assert {c["username"] for c in propio} == {"alex"}
    # un usuario no puede ver datos de otro aunque envíe usuario_id
    assert client.get("/api/historial/consultas?usuario_id=99", headers=user_h).json() == propio
    todos = client.get("/api/historial/consultas", headers=admin_h).json()
    assert {c["username"] for c in todos} == {"alex", "maria"}
    hoy = date.today().isoformat()
    f = client.get(f"/api/historial/consultas?servicio=chat_rag&desde={hoy}&hasta={hoy}", headers=admin_h).json()
    assert len(f) == 2
    assert client.get("/api/historial/consultas?servicio=novedades", headers=admin_h).json() == []
    convs = client.get("/api/historial/conversaciones", headers=user_h).json()
    assert len(convs) == 1 and convs[0]["total_consultas"] == 1


def test_reporte_web_coincide_con_detalle_powerbi(client, admin_h, user_h, llm):
    _preguntar(client, user_h)
    _preguntar(client, admin_h)
    rep = client.get("/api/reportes/consumo", headers=admin_h).json()
    det = client.get("/api/reportes/consultas-detalle", headers=admin_h).json()
    assert rep["total_consultas"] == len(det) == 2
    assert rep["total_tokens"] == sum(d["tokens_total"] for d in det)
    rep_user = client.get("/api/reportes/consumo", headers=user_h).json()
    assert rep_user["total_consultas"] == 1
