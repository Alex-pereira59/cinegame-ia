import { useEffect, useState } from 'react'
import { api, fmt, fmtFecha } from '../api'
import FormModal from '../components/FormModal'

const VACIO = { username: '', nombre: '', email: '', password: '', rol: 'usuario', activo: true, limite_tokens: 50000 }

export default function AdminUsuarios() {
  const [rows, setRows] = useState([])
  const [consumo, setConsumo] = useState({})
  const [edit, setEdit] = useState(null)

  const cargar = async () => {
    const [u, c] = await Promise.all([api('/api/usuarios'), api('/api/consumo/usuarios')])
    setRows(u)
    setConsumo(Object.fromEntries(c.map(x => [x.usuario_id, x])))
  }
  useEffect(() => { cargar() }, [])

  const fields = edit?.id
    ? [
        { name: 'nombre', label: 'Nombre', required: true },
        { name: 'email', label: 'Correo', type: 'email', optional: true },
        { name: 'password', label: 'Nueva contraseña (opcional)', type: 'password', optional: true },
        { name: 'rol', label: 'Rol', type: 'select', options: [['usuario', 'Usuario'], ['admin', 'Administrador']] },
        { name: 'limite_tokens', label: 'Límite de tokens', type: 'number', required: true },
        { name: 'activo', label: 'Activo', type: 'checkbox' },
      ]
    : [
        { name: 'username', label: 'Usuario', required: true },
        { name: 'nombre', label: 'Nombre', required: true },
        { name: 'email', label: 'Correo', type: 'email', optional: true },
        { name: 'password', label: 'Contraseña', type: 'password', required: true },
        { name: 'rol', label: 'Rol', type: 'select', options: [['usuario', 'Usuario'], ['admin', 'Administrador']] },
        { name: 'limite_tokens', label: 'Límite de tokens', type: 'number', required: true },
        { name: 'activo', label: 'Activo', type: 'checkbox' },
      ]

  const guardar = async data => {
    if (edit.id) {
      const { username, id, creado_en, ...rest } = data
      if (!rest.password) delete rest.password
      await api(`/api/usuarios/${edit.id}`, { method: 'PUT', body: rest })
    } else {
      await api('/api/usuarios', { method: 'POST', body: data })
    }
    cargar()
  }

  const eliminar = async u => {
    if (!confirm(`¿Eliminar al usuario ${u.username} y todo su historial?`)) return
    try { await api(`/api/usuarios/${u.id}`, { method: 'DELETE' }); cargar() } catch (e) { alert(e.message) }
  }

  return (
    <div className="page">
      <div className="row-between">
        <h1>Usuarios</h1>
        <button className="btn primary" onClick={() => setEdit(VACIO)}>＋ Nuevo usuario</button>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Estado</th><th className="num">Límite</th>
            <th className="num">Usados</th><th>Creado</th><th /></tr></thead>
          <tbody>
            {rows.map(u => (
              <tr key={u.id}>
                <td><b>{u.username}</b></td><td>{u.nombre}</td>
                <td><span className={'badge ' + (u.rol === 'admin' ? 'info' : '')}>{u.rol}</span></td>
                <td><span className={'badge ' + (u.activo ? 'ok' : 'warn')}>{u.activo ? 'Activo' : 'Inactivo'}</span></td>
                <td className="num">{fmt(u.limite_tokens)}</td>
                <td className="num">{fmt(consumo[u.id]?.tokens_usados)}</td>
                <td>{fmtFecha(u.creado_en)}</td>
                <td className="actions">
                  <button className="btn sm" onClick={() => setEdit({ ...u, password: '', email: u.email || '' })}>Editar</button>
                  <button className="btn sm danger" onClick={() => eliminar(u)}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {edit && <FormModal title={edit.id ? `Editar ${edit.username}` : 'Nuevo usuario'} fields={fields}
        initial={edit} onSave={guardar} onClose={() => setEdit(null)} />}
    </div>
  )
}
