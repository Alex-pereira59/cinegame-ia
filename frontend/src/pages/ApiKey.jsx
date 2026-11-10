import { useState } from 'react'
import { api } from '../api'

export default function ApiKey() {
  const [key, setKey] = useState('')
  const base = window.location.origin

  const generar = async () => {
    if (key && !confirm('Se invalidará la API key anterior. ¿Continuar?')) return
    const r = await api('/api/auth/api-key', { method: 'POST' })
    setKey(r.api_key)
  }

  return (
    <div className="page">
      <h1>Acceso a la API</h1>
      <p>La API REST es la misma que usa esta interfaz. Los consumidores externos (Postman, Power BI) pueden
        autenticarse con un token JWT o con una API key en el header <code>X-API-Key</code>.</p>
      <p>Documentación interactiva: <a href="/docs" target="_blank" rel="noreferrer">{base}/docs</a> (Swagger)
        · <a href="/redoc" target="_blank" rel="noreferrer">{base}/redoc</a></p>
      <button className="btn primary" onClick={generar}>{key ? 'Regenerar' : 'Generar'} mi API key</button>
      {key && (
        <>
          <div className="alert ok">Copia la key ahora; por seguridad no se volverá a mostrar.</div>
          <pre className="code">{key}</pre>
          <h3>Ejemplo con curl</h3>
          <pre className="code">{`curl -X POST ${base}/api/ia/chat \\
  -H "X-API-Key: ${key}" -H "Content-Type: application/json" \\
  -d '{"pregunta": "¿Cuáles son 3 películas de drama?"}'`}</pre>
          <h3>Power BI (Obtener datos → Consulta en blanco → Editor avanzado)</h3>
          <pre className="code">{`let
  Fuente = Json.Document(Web.Contents("${base}",
    [RelativePath = "api/reportes/consultas-detalle",
     Headers = [#"X-API-Key" = "${key}"]])),
  Tabla = Table.FromRecords(Fuente)
in
  Tabla`}</pre>
        </>
      )}
    </div>
  )
}
