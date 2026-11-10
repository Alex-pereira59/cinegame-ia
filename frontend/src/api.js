// Cliente HTTP de la API. En producción el frontend y la API comparten dominio.
const BASE = import.meta.env.VITE_API_URL || ''

export function getToken() {
  return localStorage.getItem('token')
}

export function getUser() {
  try { return JSON.parse(localStorage.getItem('usuario')) } catch { return null }
}

export function saveSession(token, usuario) {
  localStorage.setItem('token', token)
  localStorage.setItem('usuario', JSON.stringify(usuario))
}

export function clearSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('usuario')
}

export async function api(path, { method = 'GET', body, params } = {}) {
  let url = BASE + path
  if (params) {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null))
    if ([...qs].length) url += '?' + qs
  }
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined })
  if (res.status === 401 && path !== '/api/auth/login') {
    clearSession()
    window.location.href = '/login'
    return
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map(d => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(', ')
      : data.detail
    const err = new Error(detail || `Error ${res.status}`)
    err.status = res.status
    throw err
  }
  return data
}

export const SERVICIOS = {
  chat_rag: { nombre: 'Chatbot del catálogo', ruta: '/chat' },
  recomendador: { nombre: 'Agente recomendador', ruta: '/recomendador' },
  novedades: { nombre: 'Agente de novedades', ruta: '/novedades' },
}

export const fmt = n => new Intl.NumberFormat('es-GT').format(n ?? 0)
export const fmtFecha = s => s ? new Date(s).toLocaleString('es-GT', { dateStyle: 'short', timeStyle: 'short' }) : ''
