import { useCallback, useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { askPrompt } from '../components/confirm'
import HelpSearchBox from '../components/HelpSearchBox'
import HelpTreeNav from '../components/HelpTreeNav'
import { toast } from '../components/toast'
import { buildTree, findPath, type HelpNode } from '../utils/help-tree'
import '../pages/help-center.css'

// Layout riêng cho Trung tâm Hướng dẫn sử dụng (/hdsd) — tách khỏi AppLayout để có
// sidebar dạng cây tài liệu. Đọc: mọi user; sửa: cần quyền setting/write.

export interface HelpOutletContext {
  loadTree: () => Promise<void>
  canEdit: boolean
  tree: HelpNode[]
}

export default function HelpLayout() {
  const { user, can } = useAuth()
  const loc = useLocation()
  const nav = useNavigate()
  const canEdit = can('setting', 'write')

  const [tree, setTree] = useState<HelpNode[]>([])
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const match = loc.pathname.match(/^\/hdsd\/(\d+)/)
  const activeId = match ? parseInt(match[1], 10) : null

  const loadTree = useCallback(async () => {
    try {
      const res = await api.get('/api/v1/help-center/tree')
      setTree(buildTree(res.data.data))
    } catch {
      // client.ts đã toast lỗi; giữ cây cũ để UI không trắng
    }
  }, [])

  useEffect(() => { loadTree() }, [loadTree])

  const toggleExpand = (id: number) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  // Mở sẵn các thư mục cha của bài đang xem (vd vào thẳng link /hdsd/12)
  useEffect(() => {
    if (!activeId || tree.length === 0) return
    const path = findPath(tree, activeId)
    if (!path) return
    setExpanded((prev) => {
      const next = new Set(prev)
      path.slice(0, -1).forEach((c) => next.add(c.id))
      return next
    })
  }, [activeId, tree])

  const createArticle = async (parentId: number | null) => {
    const title = await askPrompt({
      title: parentId ? 'Thêm bài viết con' : 'Thêm mục gốc',
      message: 'Nhập tiêu đề thư mục / bài viết mới:',
      placeholder: 'VD: Hướng dẫn tạo Yêu cầu mua hàng',
      required: true,
    })
    if (!title) return
    try {
      const res = await api.post('/api/v1/help-center', {
        title,
        parent_id: parentId,
        sort_order: parentId ? 0 : tree.length,
      })
      if (parentId) setExpanded((prev) => new Set(prev).add(parentId))
      await loadTree()
      toast.success('Đã tạo bài viết')
      nav(`/hdsd/${res.data.data.id}`)
    } catch {
      // lỗi đã được toast ở interceptor
    }
  }

  const breadcrumbs = activeId ? findPath(tree, activeId) : null
  const displayName = user?.full_name || 'Người dùng'
  const initials = displayName.trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || 'U'

  const outletContext: HelpOutletContext = { loadTree, canEdit, tree }

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: '#fff' }}>
      {sidebarOpen && (
        <aside className="hc-sidebar">
          <div className="hc-sidebar-head">
            <Link to="/" title="Về trang chủ" style={{ display: 'flex', alignItems: 'center' }}>
              <img src="/logo.svg" alt="DEGO Holding" style={{ height: 32, width: 'auto' }} />
            </Link>
            {canEdit && (
              <div style={{ display: 'flex', gap: 4 }}>
                {activeId && (
                  <button className="hc-icon-btn" title="Thêm bài viết con"
                          onClick={() => createArticle(activeId)}>
                    <i className="ti ti-file-plus" style={{ fontSize: 17 }} />
                  </button>
                )}
                <button className="hc-icon-btn" title="Thêm mục gốc"
                        onClick={() => createArticle(null)}>
                  <i className="ti ti-folder-plus" style={{ fontSize: 17 }} />
                </button>
              </div>
            )}
          </div>

          <div className="hc-sidebar-body">
            <HelpTreeNav tree={tree} activeId={activeId} expanded={expanded} onToggle={toggleExpand} />
          </div>
        </aside>
      )}

      <main style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header className="hc-header">
          <button className="hc-icon-btn" title="Ẩn/hiện danh mục"
                  onClick={() => setSidebarOpen((v) => !v)}>
            <i className="ti ti-layout-sidebar" style={{ fontSize: 20 }} />
          </button>
          <div style={{ width: 1, height: 16, background: 'var(--border)' }} />

          <nav aria-label="breadcrumb">
            <ol className="hc-breadcrumb">
              <li><Link to="/hdsd">Hướng dẫn sử dụng</Link></li>
              {breadcrumbs?.map((b, i) => (
                <li key={b.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <i className="ti ti-chevron-right" style={{ fontSize: 12 }} />
                  {i === breadcrumbs.length - 1
                    ? <span style={{ color: 'var(--navy)' }}>{b.title}</span>
                    : <Link to={`/hdsd/${b.id}`}>{b.title}</Link>}
                </li>
              ))}
            </ol>
          </nav>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 20 }}>
            <HelpSearchBox />
            <Link to="/me" title="Tài khoản"
                  style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
              {user?.avatar
                ? <img src={user.avatar} alt="avatar"
                       style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover' }} />
                : <span style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--teal)',
                                 color: '#fff', display: 'grid', placeItems: 'center',
                                 fontSize: 13, fontWeight: 600 }}>{initials}</span>}
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--navy)', whiteSpace: 'nowrap' }}>
                {displayName}
              </span>
            </Link>
          </div>
        </header>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <Outlet context={outletContext} />
        </div>
      </main>
    </div>
  )
}
