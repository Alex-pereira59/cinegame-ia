import { useState } from 'react'

// Formulario genérico para los CRUD. fields: [{name, label, type, options, required}]
export default function FormModal({ title, fields, initial, onSave, onClose }) {
  const [v, setV] = useState(initial)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const set = (name, value) => setV(prev => ({ ...prev, [name]: value }))

  const submit = async e => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const data = { ...v }
      fields.forEach(f => {
        if (f.type === 'number' && data[f.name] !== '' && data[f.name] != null) data[f.name] = Number(data[f.name])
        if (f.optional && data[f.name] === '') data[f.name] = null
      })
      await onSave(data)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="modal-bg" onClick={onClose}>
      <form className="modal" onClick={e => e.stopPropagation()} onSubmit={submit}>
        <h3>{title}</h3>
        {fields.map(f => (
          <label key={f.name} className={f.type === 'checkbox' ? 'check' : ''}>
            {f.type !== 'checkbox' && f.label}
            {f.type === 'select' ? (
              <select value={v[f.name] ?? ''} onChange={e => set(f.name, e.target.value)}>
                {f.options.map(([val, lab]) => <option key={val} value={val}>{lab}</option>)}
              </select>
            ) : f.type === 'textarea' ? (
              <textarea rows={f.rows || 3} value={v[f.name] ?? ''} required={f.required}
                onChange={e => set(f.name, e.target.value)} />
            ) : f.type === 'checkbox' ? (
              <><input type="checkbox" checked={!!v[f.name]} onChange={e => set(f.name, e.target.checked)} /> {f.label}</>
            ) : (
              <input type={f.type || 'text'} step={f.step} value={v[f.name] ?? ''} required={f.required}
                placeholder={f.placeholder} onChange={e => set(f.name, e.target.value)} />
            )}
          </label>
        ))}
        {error && <div className="alert error">{error}</div>}
        <div className="row-end">
          <button type="button" className="btn ghost" onClick={onClose}>Cancelar</button>
          <button className="btn primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
        </div>
      </form>
    </div>
  )
}
