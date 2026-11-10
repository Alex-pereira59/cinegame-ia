def test_login_incorrecto(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "mala"})
    assert r.status_code == 401


def test_endpoints_requieren_autenticacion(client):
    assert client.get("/api/historial/consultas").status_code == 401
    assert client.post("/api/ia/chat", json={"pregunta": "hola"}).status_code == 401


def test_usuario_no_accede_a_admin(client, user_h):
    assert client.get("/api/usuarios", headers=user_h).status_code == 403
    r = client.post("/api/catalogo", headers=user_h, json={})
    assert r.status_code in (403, 422)


def test_crud_usuarios(client, admin_h):
    r = client.post("/api/usuarios", headers=admin_h, json={
        "username": "nuevo", "nombre": "Nuevo", "password": "secreto1", "limite_tokens": 1234})
    assert r.status_code == 201
    uid = r.json()["id"]
    r = client.put(f"/api/usuarios/{uid}", headers=admin_h, json={"limite_tokens": 999, "activo": False})
    assert r.json()["limite_tokens"] == 999 and r.json()["activo"] is False
    # usuario desactivado no puede iniciar sesión
    assert client.post("/api/auth/login", json={"username": "nuevo", "password": "secreto1"}).status_code == 403
    assert client.delete(f"/api/usuarios/{uid}", headers=admin_h).status_code == 204


def test_api_key_para_consumidores_externos(client, user_h):
    key = client.post("/api/auth/api-key", headers=user_h).json()["api_key"]
    r = client.get("/api/consumo/me", headers={"X-API-Key": key})
    assert r.status_code == 200 and r.json()["username"] == "alex"


def test_crud_catalogo(client, admin_h, user_h):
    nuevo = {"tipo": "pelicula", "titulo": "Película de prueba", "genero": "Comedia", "anio": 2020,
             "calificacion": 7.0, "creador": "Alguien", "descripcion": "Prueba"}
    r = client.post("/api/catalogo", headers=admin_h, json=nuevo)
    assert r.status_code == 201
    tid = r.json()["id"]
    assert client.put(f"/api/catalogo/{tid}", headers=admin_h, json={"calificacion": 8.1}).json()["calificacion"] == 8.1
    assert any(t["id"] == tid for t in client.get("/api/catalogo?q=prueba", headers=user_h).json())
    assert client.delete(f"/api/catalogo/{tid}", headers=admin_h).status_code == 204
