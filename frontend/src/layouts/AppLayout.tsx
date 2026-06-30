import { useState } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const NAV = [
  { to: '/', label: 'Trang chủ', icon: 'ti-layout-dashboard' },
  { to: '/purchase-requests', label: 'Yêu cầu mua', icon: 'ti-file-text' },
  { to: '/surveys-supplier', label: 'Khảo sát NCC', icon: 'ti-clipboard-search' },
  { to: '/surveys-product', label: 'Khảo sát SP', icon: 'ti-clipboard-check' },
  { to: '/companies', label: 'Công ty', icon: 'ti-building' },
  { to: '/suppliers', label: 'Nhà cung cấp', icon: 'ti-truck' },
  { to: '/products', label: 'Sản phẩm', icon: 'ti-box' },
  { to: '/warehouses', label: 'Kho', icon: 'ti-building-warehouse' },
  { to: '/units', label: 'Đơn vị tính', icon: 'ti-ruler-2' },
  { to: '/item-groups', label: 'Phân loại', icon: 'ti-category' },
  { to: '/brands', label: 'Thương hiệu', icon: 'ti-tag' },
  { to: '/employees', label: 'Nhân viên', icon: 'ti-users' },
]

const isActive = (path: string, to: string) =>
  to === '/' ? path === '/' : path.startsWith(to)

export default function AppLayout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const current = [...NAV].reverse().find((n) => isActive(loc.pathname, n.to))
  const name = user?.full_name || 'Người dùng'
  const initials = name.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  return (
    <div className="app">
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <aside className={'sidebar' + (open ? ' open' : '')}>
        <div className="brand"><i className="ti ti-building-warehouse" />Thu Mua Tool</div>
        {NAV.map((n) => (
          <Link key={n.to} to={n.to} onClick={() => setOpen(false)}
                className={'nav-item' + (isActive(loc.pathname, n.to) ? ' active' : '')}>
            <i className={'ti ' + n.icon} />{n.label}
          </Link>
        ))}
      </aside>
      <div className="main">
        <div className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className="icon-btn hamburger" onClick={() => setOpen(true)} aria-label="Menu">
              <i className="ti ti-menu-2" />
            </button>
            <div className="crumb">Mua hàng / {current?.label || ''}</div>
          </div>
          <div className="topbar-right">
            <i className="ti ti-bell icon-btn" />
            <span className="avatar">{initials}</span>
            <span className="user-name" style={{ fontSize: 13 }}>{name}</span>
            <button className="btn ghost" onClick={() => { logout(); nav('/login') }}>Đăng xuất</button>
          </div>
        </div>
        <div className="content"><Outlet /></div>
      </div>
    </div>
  )
}
