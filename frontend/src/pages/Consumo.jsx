import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, fmt, SERVICIOS } from '../api'
import { useSession } from '../App'

export default function Consumo() {
  const { user } = useSession()
  const [c, setC] = useState(null)
  const [todos, setTodos] = useState([])

  useEffect(() => {
    api('/api/consumo/me').then(setC)
    if (user.rol === 'admin') api('/api/consumo/usuarios').then(setTodos)
  }, [user])

  if (!c) return <div className="page">Cargando…</div>
  const pct = Math.min(100, c.porcentaje)
  const data = c.por_servicio.map(s => ({ ...s, nombre: SERVICIOS[s.servicio]?.nombre || s.servicio }))

  return (
    <div className="page">
      <h1>Consumo de tokens</h1>
      <div className="cards">
        <div className="card"><small>Límite asignado</small><b>{fmt(c.limite_tokens)}</b></div>
        <div className="card"><small>Tokens usados</small><b>{fmt(c.tokens_usados)}</b></div>
        <div className="card"><small>Disponibles</small><b className={pct >= 90 ? 'danger-text' : ''}>{fmt(c.tokens_restantes)}</b></div>
      </div>
      <div className="quota-bar big"><div style={{ width: pct + '%' }} className={pct >= 90 ? 'danger' : ''} /></div>
      <p className="muted">{c.porcentaje}% utilizado. Al llegar al 100% las solicitudes se bloquean hasta que el administrador amplíe el límite.</p>

      <h3>Consumo por servicio</h3>
      <div className="chart">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="nombre" />
            <YAxis />
            <Tooltip formatter={v => fmt(v)} />
            <Bar dataKey="tokens_total" name="Tokens" fill="#6d5dfc" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {user.rol === 'admin' && (
        <>
          <h3>Consumo por usuario</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Usuario</th><th className="num">Límite</th><th className="num">Usados</th>
                <th className="num">Disponibles</th><th>% uso</th></tr></thead>
              <tbody>
                {todos.map(u => (
                  <tr key={u.usuario_id}>
                    <td>{u.username}</td><td className="num">{fmt(u.limite_tokens)}</td>
                    <td className="num">{fmt(u.tokens_usados)}</td><td className="num">{fmt(u.tokens_restantes)}</td>
                    <td><div className="quota-bar"><div style={{ width: Math.min(100, u.porcentaje) + '%' }}
                      className={u.porcentaje >= 90 ? 'danger' : ''} /></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
