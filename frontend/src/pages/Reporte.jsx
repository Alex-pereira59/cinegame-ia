import { useEffect, useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api, fmt, SERVICIOS } from '../api'
import { useSession } from '../App'
import { Filtros } from './Historial'

export default function Reporte() {
  const { user } = useSession()
  const [f, setF] = useState({ desde: '', hasta: '', servicio: '', usuario_id: '' })
  const [r, setR] = useState(null)
  const [usuarios, setUsuarios] = useState(null)

  useEffect(() => { if (user.rol === 'admin') api('/api/usuarios').then(setUsuarios) }, [user])
  useEffect(() => { api('/api/reportes/consumo', { params: f }).then(setR) }, [f])

  if (!r) return <div className="page">Cargando…</div>
  const data = r.por_servicio.map(s => ({ ...s, nombre: SERVICIOS[s.servicio]?.nombre || s.servicio }))

  return (
    <div className="page">
      <h1>Reporte de consultas y consumo</h1>
      <p className="muted">
        {user.rol === 'admin' ? 'Uso general de la plataforma.' : 'Tu uso de la plataforma.'} Los mismos datos se
        exponen en <code>/api/reportes/consumo</code> y <code>/api/reportes/consultas-detalle</code> para Power BI.
      </p>
      <Filtros f={f} setF={setF} usuarios={usuarios} />
      <div className="cards">
        <div className="card"><small>Consultas realizadas</small><b>{fmt(r.total_consultas)}</b></div>
        <div className="card"><small>Tokens consumidos</small><b>{fmt(r.total_tokens)}</b></div>
        <div className="card"><small>Servicios usados</small><b>{r.por_servicio.length}</b></div>
      </div>

      <div className="grid2">
        <div className="chart">
          <h3>Consumo acumulado por servicio</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="nombre" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip formatter={v => fmt(v)} />
              <Legend />
              <Bar dataKey="tokens_entrada" name="Entrada" stackId="t" fill="#6d5dfc" />
              <Bar dataKey="tokens_salida" name="Salida" stackId="t" fill="#22c3a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart">
          <h3>Consultas por día</h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={r.por_dia}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line dataKey="consultas" name="Consultas" stroke="#6d5dfc" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead><tr><th>Servicio</th><th className="num">Consultas</th><th className="num">Tokens entrada</th>
            <th className="num">Tokens salida</th><th className="num">Total tokens</th></tr></thead>
          <tbody>
            {data.map(s => (
              <tr key={s.servicio}><td>{s.nombre}</td><td className="num">{fmt(s.consultas)}</td>
                <td className="num">{fmt(s.tokens_entrada)}</td><td className="num">{fmt(s.tokens_salida)}</td>
                <td className="num"><b>{fmt(s.tokens_total)}</b></td></tr>
            ))}
            <tr className="total"><td>Total</td><td className="num">{fmt(r.total_consultas)}</td>
              <td className="num">{fmt(data.reduce((a, s) => a + s.tokens_entrada, 0))}</td>
              <td className="num">{fmt(data.reduce((a, s) => a + s.tokens_salida, 0))}</td>
              <td className="num">{fmt(r.total_tokens)}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
