import { useEffect, useState } from 'react'
import { api } from '../api'
import FormModal from '../components/FormModal'

const VACIO = { tipo: 'pelicula', titulo: '', genero: '', anio: 2024, calificacion: 8, creador: '', plataforma: '',
  clasificacion: '', descripcion: '' }

const FIELDS = [
  { name: 'tipo', label: 'Tipo', type: 'select', options: [['pelicula', 'Película'], ['videojuego', 'Videojuego']] },
  { name: 'titulo', label: 'Título', required: true },
  { name: 'genero', label: 'Género(s)', required: true, placeholder: 'Drama, Aventura' },
  { name: 'anio', label: 'Año', type: 'number', required: true },
  { name: 'calificacion', label: 'Calificación (0-10)', type: 'number', step: '0.1', required: true },
  { name: 'creador', label: 'Director / Estudio', required: true },
  { name: 'plataforma', label: 'Plataformas (videojuegos)', optional: true },
  { name: 'clasificacion', label: 'Clasificación (PG-13, M, E…)', optional: true },
  { name: 'descripcion', label: 'Descripción', type: 'textarea', required: true },
]

export default function AdminCatalogo() {
  const [rows, setRows] = useState([])
  const [tipo, setTipo] = useState('')
  const [q, setQ] = useState('')
  const [edit, setEdit] = useState(null)

  const cargar = () => api('/api/catalogo', { params: { tipo, q } }).then(setRows)
  useEffect(() => { cargar() }, [tipo, q])

  const guardar = async ({ id, ...data }) => {
    if (edit.id) await api(`/api/catalogo/${edit.id}`, { method: 'PUT', body: data })
    else await api('/api/catalogo', { method: 'POST', body: data })
    cargar()
  }

  const eliminar = async t => {
    if (!confirm(`¿Eliminar "${t.titulo}"?`)) return
    await api(`/api/catalogo/${t.id}`, { method: 'DELETE' })
    cargar()
  }

  return (
    <div className="page">
      <div className="row-between">
        <h1>Catálogo (fuente del chatbot RAG)</h1>
        <button className="btn primary" onClick={() => setEdit(VACIO)}>＋ Nuevo título</button>
      </div>
      <div className="filters">
        <label>Tipo
          <select value={tipo} onChange={e => setTipo(e.target.value)}>
            <option value="">Todos</option><option value="pelicula">Películas</option><option value="videojuego">Videojuegos</option>
          </select>
        </label>
        <label>Buscar <input value={q} onChange={e => setQ(e.target.value)} placeholder="Título, género o creador" /></label>
        <span className="muted">{rows.length} títulos</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Título</th><th>Tipo</th><th>Género</th><th>Año</th><th className="num">Calif.</th>
            <th>Director / Estudio</th><th /></tr></thead>
          <tbody>
            {rows.map(t => (
              <tr key={t.id}>
                <td>{t.id}</td><td><b>{t.titulo}</b></td><td>{t.tipo}</td>
                <td>{t.genero}</td><td>{t.anio}</td><td className="num">{t.calificacion}</td><td>{t.creador}</td>
                <td className="actions">
                  <button className="btn sm" onClick={() => setEdit({ ...t, plataforma: t.plataforma || '', clasificacion: t.clasificacion || '' })}>Editar</button>
                  <button className="btn sm danger" onClick={() => eliminar(t)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {edit && <FormModal title={edit.id ? `Editar: ${edit.titulo}` : 'Nuevo título'} fields={FIELDS} initial={edit}
        onSave={guardar} onClose={() => setEdit(null)} />}
    </div>
  )
}
