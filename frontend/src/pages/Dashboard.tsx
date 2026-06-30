import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState<any>({})
  const [days, setDays] = useState('30')

  useEffect(() => {
    api.get('/api/dashboard/stats', { params: { days } })
      .then((r) => setStats(r.data.data))
      .catch(() => {})
  }, [days])

  const poMetrics = [
    { label: 'Yêu cầu chờ', value: stats.pr_pending ?? 0, icon: 'ti-file-alert', to: '/purchase-requests?status=submitted', color: 'var(--amber)' },
    { label: 'Đang xử lý', value: stats.pr_processing ?? 0, icon: 'ti-settings', to: '/purchase-requests?status=approved', color: 'var(--teal)' },
    { label: 'Khảo sát chờ', value: stats.survey_pending ?? 0, icon: 'ti-clipboard-check', to: '#', color: '#8e44ad' },
    { label: 'PO đã đặt hàng', value: stats.po_ordered ?? 0, icon: 'ti-shopping-cart', to: '#', color: 'var(--navy)' },
    { label: 'Đã giao', value: stats.po_delivered ?? 0, icon: 'ti-circle-check', to: '#', color: 'var(--green)' },
    { label: 'Giao chưa đủ', value: stats.po_partial ?? 0, icon: 'ti-alert-triangle', to: '#', color: '#d35400' },
    { label: 'Hoàn thành', value: stats.po_completed ?? 0, icon: 'ti-circle-check-filled', to: '#', color: '#27ae60' },
  ]

  const shortcuts = [
    { label: 'Tạo yêu cầu mua mới', icon: 'ti-plus', to: '/purchase-requests/new' },
    { label: 'Danh sách yêu cầu mua', icon: 'ti-file-text', to: '/purchase-requests' },
    { label: 'Nhà cung cấp', icon: 'ti-truck', to: '/suppliers' },
    { label: 'Sản phẩm', icon: 'ti-box', to: '/products' },
  ]

  // Trend analysis config
  const trendsList = stats.trends || []
  const width = 500
  const height = 180
  const padLeft = 30
  const padRight = 10
  const padTop = 15
  const padBottom = 20

  const chartW = width - padLeft - padRight
  const chartH = height - padTop - padBottom

  const maxVal = trendsList.length > 0
    ? Math.max(8, ...trendsList.map((t: any) => Math.max(t.pr || 0, t.po || 0)))
    : 10

  const yTicks = [0, Math.round(maxVal / 2), Math.round(maxVal)]

  const prPoints = trendsList.map((t: any, i: number) => {
    const x = padLeft + (i / Math.max(1, trendsList.length - 1)) * chartW
    const y = padTop + chartH - ((t.pr || 0) / maxVal) * chartH
    return { x, y, val: t.pr, date: t.label }
  })

  const poPoints = trendsList.map((t: any, i: number) => {
    const x = padLeft + (i / Math.max(1, trendsList.length - 1)) * chartW
    const y = padTop + chartH - ((t.po || 0) / maxVal) * chartH
    return { x, y, val: t.po, date: t.label }
  })

  const prPath = prPoints.length > 0
    ? prPoints.map((p: any, i: number) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')
    : ''

  const poPath = poPoints.length > 0
    ? poPoints.map((p: any, i: number) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ')
    : ''

  const prArea = prPoints.length > 0
    ? `${prPath} L ${prPoints[prPoints.length - 1].x} ${padTop + chartH} L ${prPoints[0].x} ${padTop + chartH} Z`
    : ''

  const poArea = poPoints.length > 0
    ? `${poPath} L ${poPoints[poPoints.length - 1].x} ${padTop + chartH} L ${poPoints[0].x} ${padTop + chartH} Z`
    : ''

  const barMetrics = [
    { label: 'Yêu cầu chờ', value: stats.pr_pending ?? 0, color: 'var(--amber)' },
    { label: 'Đang xử lý', value: stats.pr_processing ?? 0, color: 'var(--teal)' },
    { label: 'Khảo sát chờ', value: stats.survey_pending ?? 0, color: '#8e44ad' },
    { label: 'PO đặt hàng', value: stats.po_ordered ?? 0, color: 'var(--navy)' },
    { label: 'Đã giao', value: stats.po_delivered ?? 0, color: 'var(--green)' },
    { label: 'Giao chưa đủ', value: stats.po_partial ?? 0, color: '#d35400' },
    { label: 'Hoàn thành', value: stats.po_completed ?? 0, color: '#27ae60' },
  ]
  const barMax = Math.max(5, ...barMetrics.map(m => m.value))

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Xin chào, {user?.full_name}</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 500 }}>Thời gian:</label>
          <select value={days} onChange={(e) => setDays(e.target.value)} style={{ height: 32, fontSize: 13 }}>
            <option value="7">7 ngày gần nhất</option>
            <option value="30">30 ngày gần nhất</option>
            <option value="all">Tất cả thời gian</option>
          </select>
        </div>
      </div>

      <h3 style={{ margin: '0 0 12px', color: 'var(--navy)', fontSize: 15, fontWeight: 600 }}>Tình trạng hoạt động (PO &amp; PYC)</h3>
      <div className="metric-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', marginBottom: 24 }}>
        {poMetrics.map((m) => (
          <div key={m.label} className="metric-card" style={{ borderLeft: `4px solid ${m.color}` }} onClick={() => m.to !== '#' && navigate(m.to)}>
            <div className="metric-icon" style={{ color: m.color, background: `${m.color}15` }}>
              <i className={'ti ' + m.icon} />
            </div>
            <div>
              <div className="metric-value" style={{ fontSize: 20 }}>{m.value}</div>
              <div className="metric-label" style={{ fontSize: 12.5 }}>{m.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* SVG Charts section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 18, marginBottom: 24 }}>
        <div className="card" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, fontSize: 15, color: 'var(--navy)', fontWeight: 600 }}>Biểu đồ xu hướng phát sinh</h3>
            <div style={{ display: 'flex', gap: 12, fontSize: 11 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, background: 'var(--teal)', borderRadius: 2 }} />Yêu cầu mua</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 10, height: 10, background: 'var(--navy)', borderRadius: 2 }} />Đơn đặt hàng (PO)</span>
            </div>
          </div>
          {trendsList.length > 0 ? (
            <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
              <defs>
                <linearGradient id="prGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--teal)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--teal)" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="poGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--navy)" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="var(--navy)" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              {yTicks.map((tick) => {
                const y = padTop + chartH - (tick / maxVal) * chartH
                return (
                  <g key={tick}>
                    <line x1={padLeft} y1={y} x2={padLeft + chartW} y2={y} stroke="#eef2f5" strokeWidth="1" />
                    <text x={padLeft - 8} y={y + 4} textAnchor="end" style={{ fontSize: 11, fill: 'var(--muted)' }}>{tick}</text>
                  </g>
                )
              })}

              {/* X Labels */}
              {trendsList.map((t: any, i: number) => {
                const x = padLeft + (i / Math.max(1, trendsList.length - 1)) * chartW
                return (
                  <text key={i} x={x} y={height - 4} textAnchor="middle" style={{ fontSize: 11, fill: 'var(--muted)' }}>{t.label}</text>
                )
              })}

              {/* Area Paths */}
              {prArea && <path d={prArea} fill="url(#prGrad)" />}
              {poArea && <path d={poArea} fill="url(#poGrad)" />}

              {/* Line Paths */}
              {prPath && <path d={prPath} fill="none" stroke="var(--teal)" strokeWidth="2.5" strokeLinecap="round" />}
              {poPath && <path d={poPath} fill="none" stroke="var(--navy)" strokeWidth="2.5" strokeLinecap="round" />}

              {/* Data points */}
              {prPoints.map((p: any, i: number) => (
                <circle key={i} cx={p.x} cy={p.y} r="4" fill="#fff" stroke="var(--teal)" strokeWidth="2" style={{ cursor: 'pointer' }}>
                  <title>Yêu cầu mua ngày {p.date}: {p.val}</title>
                </circle>
              ))}
              {poPoints.map((p: any, i: number) => (
                <circle key={i} cx={p.x} cy={p.y} r="4" fill="#fff" stroke="var(--navy)" strokeWidth="2" style={{ cursor: 'pointer' }}>
                  <title>Đơn đặt hàng ngày {p.date}: {p.val}</title>
                </circle>
              ))}
            </svg>
          ) : (
            <div style={{ height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999' }}>Không có dữ liệu</div>
          )}
        </div>

        <div className="card" style={{ padding: 18 }}>
          <h3 style={{ margin: '0 0 12px', fontSize: 15, color: 'var(--navy)', fontWeight: 600 }}>Tỷ lệ trạng thái xử lý</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '5px 0' }}>
            {barMetrics.map((m) => (
              <div key={m.label} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 100, fontSize: 12.5, color: 'var(--ink)', fontWeight: 500 }}>{m.label}</div>
                <div style={{ flex: 1, background: '#f0f4f7', height: 10, borderRadius: 5, overflow: 'hidden' }}>
                  <div style={{ width: `${(m.value / barMax) * 100}%`, background: m.color, height: '100%', borderRadius: 5, transition: 'width 0.4s' }} />
                </div>
                <div style={{ width: 30, fontSize: 13, fontWeight: 700, color: 'var(--navy)', textAlign: 'right' }}>{m.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <h3 style={{ margin: '20px 0 12px', color: 'var(--navy)', fontSize: 15, fontWeight: 600 }}>Thao tác nhanh</h3>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {shortcuts.map((s) => (
          <button key={s.label} className="btn secondary" onClick={() => navigate(s.to)} style={{ height: 38, padding: '0 16px' }}>
            <i className={'ti ' + s.icon} /> {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}
