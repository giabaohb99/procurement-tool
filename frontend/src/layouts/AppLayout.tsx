import { useState } from 'react'
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

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
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [open, setOpen] = useState(false)
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

  return (
    <div className="app">
      {open && <div className="backdrop" onClick={() => setOpen(false)} />}
      <aside className={'sidebar' + (open ? ' open' : '')}>
        <div className="brand"><i className="ti ti-building-warehouse" />Thu Mua Tool</div>
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
