import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, fmt, fmtFecha, SERVICIOS } from '../api'
import { useSession } from '../App'

const EJEMPLOS = {
  chat_rag: ['¿Cuáles son 3 películas de drama?', '¿Cuáles son 2 videojuegos de aventura?',
    '¿Qué juegos de disparos tienen una calificación mayor a 8.5?', '¿Qué películas dirigió Christopher Nolan?'],
  recomendador: ['Quiero un RPG largo para PS5 con buena historia, ¿cuál me recomiendas?',
    'Busco una película de ciencia ficción que haga pensar, compárame opciones',
    'Recomiéndame un juego familiar para jugar con mis hermanos en Switch'],
  novedades: ['¿Qué novedades hay sobre Hollow Knight: Silksong?', 'Últimas noticias de la saga Zelda',
    '¿Qué se sabe de la próxima película de Dune?'],
}

function Fuentes({ fuentes }) {
  if (!fuentes?.length) return null
  return (
    <details className="meta">
      <summary>Fuentes ({fuentes.length})</summary>
      <ul>
        {fuentes.map((f, i) => (
          <li key={i}>
            {f.tipo === 'base_de_datos'
              ? <>BD · tabla <code>{f.tabla}</code> · [#{f.id}] {f.titulo}{f.citado ? ' (citado)' : ''}</>
              : <a href={f.url} target="_blank" rel="noreferrer">{f.nombre || f.url}</a>}
            {f.fecha && <small> ({f.fecha})</small>}
          </li>
        ))}
      </ul>
    </details>
  )
}

function Pasos({ pasos }) {
  if (!pasos?.length) return null
  return (
    <details className="meta">
      <summary>Pasos del {pasos.length > 1 || pasos[0].herramienta !== 'recuperacion_sql' ? 'agente' : 'RAG'} ({pasos.length})</summary>
      <ol>
        {pasos.map(p => (
          <li key={p.paso}>
            <code>{p.herramienta}</code>({Object.entries(p.argumentos || {}).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ')})
            <div className="muted">→ {p.resumen}</div>
          </li>
        ))}
      </ol>
    </details>
  )
}

export default function ServicioIA({ codigo }) {
  const info = SERVICIOS[codigo]
  const { refresh, servicios } = useSession()
  const servicio = servicios.find(s => s.codigo === codigo)
  const [convs, setConvs] = useState([])
  const [convId, setConvId] = useState(null)
  const [mensajes, setMensajes] = useState([])
  const [texto, setTexto] = useState('')
  const [tipo, setTipo] = useState('todos')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  const cargarConvs = () => api('/api/historial/conversaciones', { params: { servicio: codigo } }).then(setConvs)
  useEffect(() => { cargarConvs() }, [codigo])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [mensajes, loading])

  const abrir = async id => {
    const d = await api(`/api/historial/conversaciones/${id}`)
    setConvId(id)
    setError('')
    setMensajes(d.consultas.flatMap(c => [
      { rol: 'user', texto: c.pregunta },
      { rol: 'ai', texto: c.respuesta, fuentes: c.fuentes, pasos: c.pasos, tokens: c.tokens_total, fecha: c.creado_en },
    ]))
  }

  const nueva = () => { setConvId(null); setMensajes([]); setError('') }

  const borrar = async (e, id) => {
    e.stopPropagation()
    if (!confirm('¿Ocultar esta conversación? (el consumo se conserva)')) return
    await api(`/api/historial/conversaciones/${id}`, { method: 'DELETE' })
    if (id === convId) nueva()
    cargarConvs()
  }

  const enviar = async e => {
    e?.preventDefault()
    const pregunta = texto.trim()
    if (!pregunta || loading) return
    setTexto('')
    setError('')
    setMensajes(m => [...m, { rol: 'user', texto: pregunta }])
    setLoading(true)
    try {
      const body = codigo === 'chat_rag'
        ? { pregunta, conversacion_id: convId, tipo }
        : { solicitud: pregunta, conversacion_id: convId }
      const ruta = codigo === 'chat_rag' ? '/api/ia/chat' : `/api/ia/${codigo}`
      const r = await api(ruta, { method: 'POST', body })
      setMensajes(m => [...m, {
        rol: 'ai', texto: r.respuesta, fuentes: r.fuentes, pasos: r.pasos, tokens: r.tokens_total,
        suficiente: r.suficiente,
      }])
      if (!convId) setConvId(r.conversacion_id)
      cargarConvs()
      refresh()
    } catch (err) {
      setError(err.message)
      setMensajes(m => m.slice(0, -1))
      setTexto(pregunta)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-layout">
      <div className="conv-list">
        <button className="btn primary block" onClick={nueva}>＋ Nueva conversación</button>
        {convs.map(c => (
          <div key={c.id} className={'conv' + (c.id === convId ? ' active' : '')} onClick={() => abrir(c.id)}>
            <div className="conv-title">{c.titulo}</div>
            <small>{fmtFecha(c.creado_en)} · {c.total_consultas} msg</small>
            <button className="x" title="Ocultar" onClick={e => borrar(e, c.id)}>×</button>
          </div>
        ))}
        {!convs.length && <p className="muted small">Sin conversaciones todavía.</p>}
      </div>

      <section className="chat">
        <header className="chat-head">
          <h2>{info.icono} {info.nombre}</h2>
          <p className="muted">{servicio?.descripcion}</p>
          {codigo === 'chat_rag' && (
            <div className="seg">
              {[['todos', 'Todo'], ['pelicula', 'Películas'], ['videojuego', 'Videojuegos']].map(([v, l]) => (
                <button key={v} className={tipo === v ? 'on' : ''} onClick={() => setTipo(v)}>{l}</button>
              ))}
            </div>
          )}
        </header>

        <div className="messages">
          {!mensajes.length && (
            <div className="empty">
              <p>Prueba con:</p>
              {EJEMPLOS[codigo].map(e => <button key={e} className="chip" onClick={() => setTexto(e)}>{e}</button>)}
            </div>
          )}
          {mensajes.map((m, i) => (
            <div key={i} className={'msg ' + m.rol}>
              {m.rol === 'ai'
                ? <>
                    {m.suficiente === false && <div className="badge warn">Información insuficiente en la BD</div>}
                    <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{m.texto}</ReactMarkdown></div>
                    <Pasos pasos={m.pasos} />
                    <Fuentes fuentes={m.fuentes} />
                    <small className="muted">{fmt(m.tokens)} tokens{m.fecha ? ' · ' + fmtFecha(m.fecha) : ''}</small>
                  </>
                : m.texto}
            </div>
          ))}
          {loading && (
            <div className="msg ai thinking">
              {codigo === 'chat_rag' ? 'Consultando el catálogo…' : 'El agente está buscando, consultando y comparando…'}
            </div>
          )}
          <div ref={endRef} />
        </div>

        {error && <div className="alert error">{error}</div>}
        <form className="composer" onSubmit={enviar}>
          <textarea
            value={texto} rows={2} placeholder="Escribe tu pregunta…"
            onChange={e => setTexto(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) enviar(e) }}
          />
          <button className="btn primary" disabled={loading || !texto.trim()}>Enviar</button>
        </form>
      </section>
    </div>
  )
}
