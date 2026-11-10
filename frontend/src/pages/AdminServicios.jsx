import { useEffect, useState } from 'react'
import { api, SERVICIOS } from '../api'
import { useSession } from '../App'
import FormModal from '../components/FormModal'

export default function AdminServicios() {
  const { refresh } = useSession()
  const [rows, setRows] = useState([])
  const [edit, setEdit] = useState(null)

  const cargar = () => api('/api/servicios').then(setRows)
  useEffect(() => { cargar() }, [])

  const guardar = async (id, body) => {
    await api(`/api/servicios/${id}`, { method: 'PUT', body })
    await cargar()
    refresh()
  }

  return (
    <div className="page">
      <h1>Servicios de IA</h1>
      <p className="muted">Activa o desactiva servicios y ajusta su configuración. Un servicio desactivado responde
        403 en la API y desaparece del menú de los usuarios.</p>
      <div className="service-grid">
        {rows.map(s => (
          <div key={s.id} className={'service-card' + (s.activo ? '' : ' off')}>
            <div className="row-between">
              <h3>{SERVICIOS[s.codigo]?.icono} {s.nombre}</h3>
              <label className="switch">
                <input type="checkbox" checked={s.activo} onChange={e => guardar(s.id, { activo: e.target.checked })} />
                <span />
              </label>
            </div>
            <p className="muted">{s.descripcion}</p>
            <ul className="kv">
              <li><span>Código</span><code>{s.codigo}</code></li>
              <li><span>Modelo</span>{s.modelo || 'Predeterminado (variable LLM_MODEL)'}</li>
              <li><span>Temperatura</span>{s.temperatura}</li>
              <li><span>Máx. pasos</span>{s.max_pasos}</li>
            </ul>
            <button className="btn" onClick={() => setEdit({ ...s, modelo: s.modelo || '' })}>Configurar</button>
          </div>
        ))}
      </div>
      {edit && (
        <FormModal
          title={`Configurar: ${edit.nombre}`}
          initial={edit}
          fields={[
            { name: 'nombre', label: 'Nombre', required: true },
            { name: 'descripcion', label: 'Descripción', type: 'textarea' },
            { name: 'modelo', label: 'Modelo (vacío = predeterminado)', optional: true, placeholder: 'llama-3.3-70b-versatile' },
            { name: 'temperatura', label: 'Temperatura (0-2)', type: 'number', step: '0.1' },
            { name: 'max_pasos', label: 'Máximo de pasos del agente', type: 'number' },
            { name: 'prompt_sistema', label: 'Prompt del sistema', type: 'textarea', rows: 8 },
            { name: 'activo', label: 'Activo', type: 'checkbox' },
          ]}
          onSave={({ id, codigo, ...body }) => guardar(edit.id, body)}
          onClose={() => setEdit(null)}
        />
      )}
    </div>
  )
}
