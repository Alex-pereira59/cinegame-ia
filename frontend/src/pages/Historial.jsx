import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api, fmt, fmtFecha, SERVICIOS } from '../api'
import { useSession } from '../App'

export function Filtros({ f, setF, usuarios }) {
  return (
    <div className="filters">
      <label>Desde <input type="date" value={f.desde} onChange={e => setF({ ...f, desde: e.target.value })} /></label>
      <label>Hasta <input type="date" value={f.hasta} onChange={e => setF({ ...f, hasta: e.target.value })} /></label>
      <label>Servicio
        <select value={f.servicio} onChange={e => setF({ ...f, servicio: e.target.value })}>
          <option value="">Todos</option>
          {Object.entries(SERVICIOS).map(([k, s]) => <option key={k} value={k}>{s.nombre}</option>)}
        </select>
      </label>
      {usuarios && (
        <label>Usuario
          <select value={f.usuario_id} onChange={e => setF({ ...f, usuario_id: e.target.value })}>
            <option value="">Todos</option>
            {usuarios.map(u => <option key={u.id} value={u.id}>{u.username}</option>)}
          </select>
        </label>
      )}
      <button className="btn ghost" onClick={() => setF({ desde: '', hasta: '', servicio: '', usuario_id: '' })}>Limpiar</button>
    </div>
  )
}

export default function Historial() {
  const { user } = useSession()
  const [f, setF] = useState({ desde: '', hasta: '', servicio: '', usuario_id: '' })
  const [rows, setRows] = useState([])
  const [usuarios, setUsuarios] = useState(null)
  const [sel, setSel] = useState(null)

  useEffect(() => { if (user.rol === 'admin') api('/api/usuarios').then(setUsuarios) }, [user])
  useEffect(() => { api('/api/historial/consultas', { params: { ...f, limite: 500 } }).then(setRows) }, [f])

  return (
    <div className="page">
      <h1>Historial de consultas</h1>
      <p className="muted">{user.rol === 'admin' ? 'Como administrador ves las consultas de todos los usuarios.' : 'Tus consultas registradas automáticamente.'}</p>
      <Filtros f={f} setF={setF} usuarios={usuarios} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Fecha</th>{user.rol === 'admin' && <th>Usuario</th>}<th>Servicio</th><th>Pregunta</th>
              <th className="num">Entrada</th><th className="num">Salida</th><th className="num">Total</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} onClick={() => setSel(r)} className="clickable">
                <td>{fmtFecha(r.creado_en)}</td>
                {user.rol === 'admin' && <td>{r.username}</td>}
                <td>{SERVICIOS[r.servicio]?.nombre || r.servicio}</td>
                <td className="ellipsis">{r.pregunta}</td>
                <td className="num">{fmt(r.tokens_entrada)}</td>
                <td className="num">{fmt(r.tokens_salida)}</td>
                <td className="num"><b>{fmt(r.tokens_total)}</b></td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={7} className="muted">Sin registros.</td></tr>}
          </tbody>
        </table>
      </div>

      {sel && (
        <div className="modal-bg" onClick={() => setSel(null)}>
          <div className="modal wide" onClick={e => e.stopPropagation()}>
            <h3>{SERVICIOS[sel.servicio]?.nombre} · {fmtFecha(sel.creado_en)}</h3>
            <p><b>Pregunta:</b> {sel.pregunta}</p>
            <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{sel.respuesta}</ReactMarkdown></div>
            {!!sel.pasos?.length && <p className="muted">Pasos: {sel.pasos.map(p => p.herramienta).join(' → ')}</p>}
            {!!sel.fuentes?.length && <p className="muted">Fuentes: {sel.fuentes.map(x => x.titulo || x.nombre).join('; ')}</p>}
            <button className="btn" onClick={() => setSel(null)}>Cerrar</button>
          </div>
        </div>
      )}
    </div>
  )
}
