import { useState } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { api } from '../api/client'

type NavItem = { to: string; label: string; icon: string }
type NavGroup = { title?: string; key?: string; collapsible?: boolean; items: NavItem[] }

const NAV_GROUPS: NavGroup[] = [
  { items: [
    { to: '/', label: 'Trang chủ', icon: 'ti-layout-dashboard' },
    { to: '/reports', label: 'Báo cáo mua hàng', icon: 'ti-chart-bar' },
  ] },
  { title: 'Mua hàng', items: [
    { to: '/purchase-requests', label: 'Yêu cầu mua', icon: 'ti-file-text' },
    { to: '/surveys-supplier', label: 'Khảo sát NCC', icon: 'ti-clipboard-search' },
    { to: '/surveys-product', label: 'Khảo sát SP', icon: 'ti-clipboard-check' },
    { to: '/purchase-orders', label: 'Đơn mua hàng', icon: 'ti-shopping-cart' },
  ] },
  { title: 'Kho & Công nợ', items: [
    { to: '/inventory', label: 'Tồn kho', icon: 'ti-packages' },
    { to: '/payables', label: 'Công nợ', icon: 'ti-cash' },
    { to: '/payment-requests', label: 'Yêu cầu thanh toán', icon: 'ti-receipt' },
  ] },
  { title: 'Danh mục', key: 'danhmuc', collapsible: true, items: [
    { to: '/suppliers', label: 'Nhà cung cấp', icon: 'ti-truck' },
    { to: '/products', label: 'Sản phẩm', icon: 'ti-box' },
    { to: '/contracts', label: 'Hợp đồng', icon: 'ti-file-certificate' },
    { to: '/warehouses', label: 'Kho', icon: 'ti-building-warehouse' },
    { to: '/units', label: 'Đơn vị tính', icon: 'ti-ruler-2' },
    { to: '/item-groups', label: 'Phân loại', icon: 'ti-category' },
    { to: '/departments', label: 'Phòng ban', icon: 'ti-tag' },
  ] },
  { title: 'Hệ thống', items: [
    { to: '/companies', label: 'Công ty', icon: 'ti-building' },
    { to: '/employees', label: 'Nhân sự', icon: 'ti-users' },
    { to: '/roles', label: 'Vai trò', icon: 'ti-shield' },
  ] },
]
const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items)

const isActive = (path: string, to: string) =>
  to === '/' ? path === '/' : path.startsWith(to)

export default function AppLayout() {
  const { user, logout, updateUser } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(() => {
    try { return JSON.parse(localStorage.getItem('nav_collapsed') || '{}') } catch { return {} }
  })
  const toggle = (k: string) => setCollapsed((s) => {
    const n = { ...s, [k]: !s[k] }
    localStorage.setItem('nav_collapsed', JSON.stringify(n))
    return n
  })
  const current = [...ALL_ITEMS].reverse().find((n) => isActive(loc.pathname, n.to))
  const name = user?.full_name || 'Người dùng'
  const initials = name.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadingAvatar(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/api/auth/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      updateUser({ avatar: res.data.data.avatar })
    } catch (err) {
      alert('Không thể tải ảnh lên. Vui lòng thử lại.')
    } finally {
      setUploadingAvatar(false)
    }
  }

  return (
    <div className="app">
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <aside className={'sidebar' + (open ? ' open' : '')}>
        <div className="brand"><div className="brand-logo"><img src="/logo.svg" alt="DEGO Holding" /></div></div>
        {NAV_GROUPS.map((g, gi) => {
          const isCol = g.collapsible && g.key && collapsed[g.key]
          return (
            <div key={gi}>
              {g.title && (
                g.collapsible ? (
                  <button className="nav-group-title toggle" onClick={() => toggle(g.key!)}>
                    <i className={'ti ' + (isCol ? 'ti-chevron-right' : 'ti-chevron-down')} style={{ fontSize: 13 }} />{g.title}
                  </button>
                ) : <div className="nav-group-title">{g.title}</div>
              )}
              {!isCol && g.items.map((n) => (
                <Link key={n.to} to={n.to} onClick={() => setOpen(false)}
                      className={'nav-item' + (isActive(loc.pathname, n.to) ? ' active' : '')}>
                  <i className={'ti ' + n.icon} />{n.label}
                </Link>
              ))}
            </div>
          )
        })}
      </aside>
      <div className="main">
        <div className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className="icon-btn hamburger" onClick={() => setOpen(true)} aria-label="Menu">
              <i className="ti ti-menu-2" />
            </button>
            <div className="crumb">Mua hàng / {current?.label || ''}</div>
          </div>
          <div className="topbar-right" style={{ position: 'relative' }}>
            <i className="ti ti-bell icon-btn" />
            <div 
              style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 8 }} 
              onClick={() => setProfileOpen(!profileOpen)}
            >
              {user?.avatar ? (
                <img src={user.avatar} alt="avatar" className="avatar" style={{ objectFit: 'cover' }} />
              ) : (
                <span className="avatar">{initials}</span>
              )}
              <span className="user-name" style={{ fontSize: 13 }}>{name}</span>
              <i className="ti ti-chevron-down" style={{ fontSize: 12, color: '#666' }} />
            </div>
            
            {profileOpen && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: 8,
                backgroundColor: 'white',
                borderRadius: 8,
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                width: 250,
                zIndex: 100,
                overflow: 'hidden',
                border: '1px solid #e2e8f0'
              }}>
                <div style={{ padding: 16, borderBottom: '1px solid #eee', backgroundColor: '#f8fafc', display: 'flex', alignItems: 'center', gap: 12 }}>
                  <label style={{ cursor: 'pointer', position: 'relative', display: 'block', flexShrink: 0 }}>
                    {user?.avatar ? (
                      <img src={user.avatar} alt="avatar" style={{ width: 48, height: 48, borderRadius: '50%', objectFit: 'cover', border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }} />
                    ) : (
                      <div style={{ width: 48, height: 48, borderRadius: '50%', backgroundColor: '#0f172a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 600 }}>{initials}</div>
                    )}
                    <div style={{ position: 'absolute', bottom: 0, right: 0, backgroundColor: '#1c9cf0', color: '#fff', width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }}>
                      <i className={uploadingAvatar ? "ti ti-loader" : "ti ti-camera"} style={{ fontSize: 12, animation: uploadingAvatar ? "spin 1s linear infinite" : "none" }} />
                    </div>
                    <input type="file" hidden accept="image/*" onChange={handleAvatarUpload} disabled={uploadingAvatar} />
                  </label>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{user?.full_name}</div>
                    <div style={{ fontSize: 13, color: '#64748b', marginTop: 4, wordBreak: 'break-all' }}>{user?.email}</div>
                  </div>
                </div>
                <div style={{ padding: '8px 0' }}>
                  <div style={{ padding: '8px 16px', fontSize: 13, color: '#475569', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <i className="ti ti-phone" style={{ fontSize: 15 }} /> {user?.phone || 'Chưa cập nhật SĐT'}
                  </div>
                  <div style={{ padding: '8px 16px', fontSize: 13, color: '#475569', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <i className="ti ti-building" style={{ fontSize: 15 }} /> {user?.department_name || 'Chưa có phòng ban'}
                  </div>
                </div>
                <div style={{ borderTop: '1px solid #eee', padding: 8 }}>
                  <button 
                    style={{ width: '100%', textAlign: 'left', padding: '8px 8px', backgroundColor: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', borderRadius: 4, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 500 }}
                    onClick={() => { logout(); nav('/login') }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#fef2f2'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <i className="ti ti-logout" style={{ fontSize: 16 }} /> Đăng xuất
                  </button>
                </div>
              </div>
            )}
            
            {profileOpen && <div style={{ position: 'fixed', inset: 0, zIndex: 99 }} onClick={() => setProfileOpen(false)} />}
          </div>
        </div>
        <div className="content"><Outlet /></div>
      </div>
    </div>
  )
}
