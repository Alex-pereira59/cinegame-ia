import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { api, clearSession, fmt, getUser, SERVICIOS } from './api'
import Login from './pages/Login'
import ServicioIA from './pages/ServicioIA'
import Historial from './pages/Historial'
import Consumo from './pages/Consumo'
import Reporte from './pages/Reporte'
import ApiKey from './pages/ApiKey'
import AdminUsuarios from './pages/AdminUsuarios'
import AdminServicios from './pages/AdminServicios'
import AdminCatalogo from './pages/AdminCatalogo'

const SessionCtx = createContext(null)
export const useSession = () => useContext(SessionCtx)

function Layout({ children }) {
  const { user, consumo, servicios, logout } = useSession()
  const pct = consumo ? Math.min(100, consumo.porcentaje) : 0
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">CineGame <span>AI</span></div>
        <nav>
          <div className="nav-title">Servicios de IA</div>
          {Object.entries(SERVICIOS).map(([codigo, s]) => {
            const activo = servicios.some(x => x.codigo === codigo && x.activo)
            return activo ? (
              <NavLink key={codigo} to={s.ruta}>{s.nombre}</NavLink>
            ) : (
              <span key={codigo} className="nav-disabled" title="Servicio desactivado por el administrador">
                {s.nombre}
              </span>
            )
          })}
          <div className="nav-title">Mi cuenta</div>
          <NavLink to="/historial">Historial</NavLink>
          <NavLink to="/consumo">Consumo de tokens</NavLink>
          <NavLink to="/reporte">Reporte de uso</NavLink>
          <NavLink to="/api-key">Acceso a la API</NavLink>
          {user.rol === 'admin' && (
            <>
              <div className="nav-title">Administración</div>
              <NavLink to="/admin/usuarios">Usuarios</NavLink>
              <NavLink to="/admin/servicios">Servicios de IA</NavLink>
              <NavLink to="/admin/catalogo">Catálogo</NavLink>
            </>
          )}
          <a href="/docs" target="_blank" rel="noreferrer">Swagger (API)</a>
        </nav>
        <div className="sidebar-foot">
          <div className="who">{user.nombre} <small>({user.rol})</small></div>
          {consumo && (
            <div className="quota" title={`${fmt(consumo.tokens_usados)} de ${fmt(consumo.limite_tokens)} tokens`}>
              <div className="quota-bar"><div style={{ width: pct + '%' }} className={pct >= 90 ? 'danger' : ''} /></div>
              <small>{fmt(consumo.tokens_restantes)} tokens disponibles</small>
            </div>
          )}
          <button className="btn ghost" onClick={logout}>Cerrar sesión</button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(getUser())
  const [consumo, setConsumo] = useState(null)
  const [servicios, setServicios] = useState([])
  const navigate = useNavigate()

  const refresh = useCallback(async () => {
    if (!getUser()) return
    const [c, s] = await Promise.all([api('/api/consumo/me'), api('/api/servicios')])
    setConsumo(c)
    setServicios(s || [])
  }, [])

  useEffect(() => { if (user) refresh().catch(() => {}) }, [user, refresh])

  const logout = async () => {
    try { await api('/api/auth/logout', { method: 'POST' }) } catch { /* ignorar */ }
    clearSession()
    setUser(null)
    navigate('/login')
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={setUser} />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    )
  }

  const admin = el => (user.rol === 'admin' ? el : <Navigate to="/chat" />)

  return (
    <SessionCtx.Provider value={{ user, consumo, servicios, refresh, logout }}>
      <Layout>
        <Routes>
          <Route path="/chat" element={<ServicioIA key="chat_rag" codigo="chat_rag" />} />
          <Route path="/recomendador" element={<ServicioIA key="recomendador" codigo="recomendador" />} />
          <Route path="/novedades" element={<ServicioIA key="novedades" codigo="novedades" />} />
          <Route path="/historial" element={<Historial />} />
          <Route path="/consumo" element={<Consumo />} />
          <Route path="/reporte" element={<Reporte />} />
          <Route path="/api-key" element={<ApiKey />} />
          <Route path="/admin/usuarios" element={admin(<AdminUsuarios />)} />
          <Route path="/admin/servicios" element={admin(<AdminServicios />)} />
          <Route path="/admin/catalogo" element={admin(<AdminCatalogo />)} />
          <Route path="*" element={<Navigate to="/chat" />} />
        </Routes>
      </Layout>
    </SessionCtx.Provider>
  )
}
