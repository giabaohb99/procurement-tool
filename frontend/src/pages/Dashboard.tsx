import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const money = (v: number) => {
  const n = Math.abs(v || 0)
  if (n >= 1e9) return (v / 1e9).toFixed(2).replace(/\.?0+$/, '') + ' tỷ'
  if (n >= 1e6) return Math.round(v / 1e6) + ' tr'
  if (n >= 1e3) return Math.round(v / 1e3) + 'k'
  return String(Math.round(v || 0))
}
const full = (v: number) => Math.round(v || 0).toLocaleString('vi-VN') + ' đ'
const CAT_COLORS = ['#00AEEF', '#92C83E', '#F6AD37', '#7C8DB5', '#CBD5E1']
const PO_ST: Record<string, { l: string; c: string }> = {
  draft: { l: 'Nháp', c: '#64748b' }, submitted: { l: 'Chờ duyệt', c: '#D97706' },
  approved: { l: 'Đã duyệt', c: '#00AEEF' }, partial: { l: 'Giao 1 phần', c: '#EA580C' },
  received: { l: 'Đã nhận', c: '#16a34a' }, completed: { l: 'Hoàn thành', c: '#0d9488' },
  cancelled: { l: 'Đã hủy', c: '#b91c1c' },
}
const AGING_COLORS = ['#16a34a', '#F6AD37', '#EA580C', '#E24B4A']

function BarList({ items, fmt }: { items: any[]; fmt?: (v: number) => string }) {
  if (!items || items.length === 0) return <div style={{ color: 'var(--hz-muted)', fontSize: 13 }}>Chưa có dữ liệu</div>
  const max = Math.max(1, ...items.map((i) => i.value || 0))
  return (
    <>
      {items.map((it, i) => (
        <div key={i} style={{ marginBottom: 11 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, marginBottom: 4, gap: 8 }}>
            <span style={{ color: 'var(--navy)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{it.label || it.name}</span>
            <span style={{ fontWeight: 700, color: 'var(--navy)', flex: 'none' }}>{fmt ? fmt(it.value) : it.value}</span>
          </div>
          <div className="hz-bar-track"><div className="hz-bar-fill" style={{ width: `${(it.value / max) * 100}%`, background: it.color || '#00AEEF' }} /></div>
        </div>
      ))}
    </>
  )
}

function Donut({ items }: { items: { label: string; value: number; color: string; display?: string }[] }) {
  if (!items || items.length === 0) return <div style={{ color: 'var(--hz-muted)', fontSize: 13 }}>Chưa có dữ liệu</div>
  const total = items.reduce((s, i) => s + (i.value || 0), 0) || 1
  const C = 2 * Math.PI * 45
  let acc = 0
  const arcs = items.map((it) => {
    const len = (it.value / total) * C
    const seg = { len, off: -acc, color: it.color }
    acc += len
    return seg
  })
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, justifyContent: 'center', width: '100%', padding: '10px 0' }}>
      <svg viewBox="0 0 120 120" style={{ width: 110, height: 110, flex: 'none' }}>
        <g transform="rotate(-90 60 60)" fill="none" strokeWidth="16">
          <circle cx="60" cy="60" r="45" stroke="#f0f2f9" />
          {arcs.map((a, i) => (
            <circle key={i} cx="60" cy="60" r="45" stroke={a.color} strokeDasharray={`${a.len} ${C - a.len}`} strokeDashoffset={a.off} />
          ))}
        </g>
        <text x="60" y="58" textAnchor="middle" style={{ fontSize: 9, fill: 'var(--hz-muted)', fontWeight: 700, letterSpacing: '0.05em' }}>TỔNG</text>
        <text x="60" y="73" textAnchor="middle" style={{ fontSize: 12, fill: 'var(--navy)', fontWeight: 800 }}>{money(total)}</text>
      </svg>
      <div style={{ fontSize: 12.5, lineHeight: 1.8, width: 170, flex: 'none' }}>
        {items.map((it, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
              <span style={{ width: 8, height: 8, borderRadius: 3, background: it.color, flex: 'none' }} />
              <span style={{ color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{it.label}</span>
            </span>
            <span style={{ fontWeight: 700, color: 'var(--navy)', flex: 'none' }}>{it.display ?? it.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [d, setD] = useState<any>(null)

  async function handleApprove(id: number) {
    if (!confirm('Bạn có chắc chắn muốn duyệt đơn hàng này?')) return
    try {
      await api.post(`/api/purchase-orders/${id}/approve`)
      alert('Đã duyệt đơn hàng thành công!')
      api.get('/api/dashboard/overview').then((r) => setD(r.data.data)).catch(() => {})
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Lỗi khi duyệt đơn hàng')
    }
  }

  async function handleReject(id: number) {
    const reason = prompt('Nhập lý do từ chối đơn hàng:')
    if (reason === null) return
    try {
      await api.post(`/api/purchase-orders/${id}/reject`, { reason: reason || 'Từ chối từ Dashboard' })
      alert('Đã từ chối đơn hàng thành công!')
      api.get('/api/dashboard/overview').then((r) => setD(r.data.data)).catch(() => {})
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Lỗi khi từ chối đơn hàng')
    }
  }

  async function handleApprovePR(id: number) {
    if (!confirm('Bạn có chắc chắn muốn duyệt yêu cầu mua hàng này?')) return
    try {
      await api.post(`/api/purchase-requests/${id}/approve`, {})
      alert('Đã duyệt yêu cầu mua hàng thành công!')
      api.get('/api/dashboard/overview').then((r) => setD(r.data.data)).catch(() => {})
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Lỗi khi duyệt yêu cầu mua hàng')
    }
  }

  async function handleRejectPR(id: number) {
    const reason = prompt('Nhập lý do từ chối yêu cầu mua hàng:')
    if (reason === null) return
    try {
      await api.post(`/api/purchase-requests/${id}/reject`, { reason: reason || 'Từ chối từ Dashboard' })
      alert('Đã từ chối yêu cầu mua hàng thành công!')
      api.get('/api/dashboard/overview').then((r) => setD(r.data.data)).catch(() => {})
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Lỗi khi từ chối yêu cầu mua hàng')
    }
  }

  useEffect(() => {
    api.get('/api/dashboard/overview').then((r) => setD(r.data.data)).catch(() => {})
  }, [])

  const k = d?.kpi || {}
  const cats = d?.categories || []
  const totalSpendVal = cats.reduce((s: number, c: any) => s + (c.cost || 0), 0)
  const kpis = [
    { label: 'Tổng chi tiêu', value: money(totalSpendVal), icon: 'ti-coin', color: '#00AEEF', tint: '#E5F7FF', to: '/purchase-orders', trend: 'Số liệu năm 2026', trendColor: 'var(--hz-muted)' },
    { label: 'Yêu cầu chờ duyệt (PRs)', value: k.pr_pending ?? 0, icon: 'ti-file-alert', color: '#D97706', tint: '#FFF6E5', to: '/purchase-requests?status=submitted', trend: 'Cần phê duyệt gấp', trendColor: '#E24B4A' },
    { label: 'Đơn hàng hoạt động (POs)', value: k.po_ordered ?? 0, icon: 'ti-shopping-cart', color: '#4318FF', tint: '#ebe8ff', to: '/purchase-orders', trend: 'Đang theo dõi tiến độ', trendColor: '#00AEEF' },
    { label: 'Công nợ quá hạn', value: money(k.overdue ?? 0), icon: 'ti-alert-triangle', color: '#E24B4A', tint: '#FEECEC', to: '/payables', trend: (k.overdue ?? 0) > 0 ? 'Cần đối soát thanh toán' : 'Không có nợ xấu', trendColor: (k.overdue ?? 0) > 0 ? '#E24B4A' : '#92C83E' },
  ]

  // Biểu đồ cột 12 tháng (khóa chiều cao 240 để không "to đùng")
  const cost = d?.cost_12m || []
  const cw = 760, ch = 240, pl = 54, pr = 12, pt = 22, pb = 28
  const iw = cw - pl - pr, ih = ch - pt - pb
  const cmax = Math.max(1, ...cost.map((c: any) => c.value || 0))
  const cTicks = [0, cmax / 2, cmax]
  const bw = (iw / Math.max(1, cost.length)) * 0.5



  const po_status = (d?.po_status || []).map((s: any) => ({ label: s.label, value: s.value, color: PO_ST[s.key]?.c || '#00AEEF' }))
  const ap_aging = (d?.ap_aging || []).map((a: any, i: number) => ({ label: a.label, value: a.value, color: AGING_COLORS[i] }))
  const top_sup = d?.top_suppliers || []
  const dept = d?.dept_spend || []
  const alerts = d?.alerts || []
  const low = d?.low_stock || []
  const recent = d?.recent_pos || []
  const recent_prs = d?.recent_prs || []

  return (
    <div>
      {/* Header */}
      <div className="hz-head" style={{ marginBottom: 20 }}>
        <div>
          <p className="hz-hello">Chào mừng trở lại</p>
          <h2 className="hz-name" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {user?.full_name || 'Bạn'}
            {k.pr_pending ? (
              <span style={{ fontSize: 11, fontWeight: 600, background: '#FEECEC', color: '#E24B4A', padding: '3px 10px', borderRadius: 20 }}>
                {k.pr_pending} PYC chờ duyệt
              </span>
            ) : null}
          </h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <i className="ti ti-search" style={{ position: 'absolute', left: 12, color: 'var(--hz-muted)' }} />
            <input type="text" placeholder="Tìm kiếm nhanh..." style={{ paddingLeft: 34, height: 40, width: 220, borderRadius: 12, border: '1px solid #eef1f8', fontSize: 13, outline: 'none' }} />
          </div>
          <button className="btn" style={{ background: '#00AEEF', color: '#fff', borderRadius: 12, height: 40, padding: '0 16px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, border: 'none', cursor: 'pointer' }} onClick={() => navigate('/purchase-requests/new')}>
            <i className="ti ti-plus" />Tạo yêu cầu mua
          </button>
        </div>
      </div>

      {/* KPI (8 thẻ) */}
      <div className="hz-stats">
        {kpis.map((m) => (
          <div key={m.label} className="hz-stat" onClick={() => navigate(m.to)}>
            <div className="hz-stat-ic" style={{ background: m.tint, color: m.color }}><i className={'ti ' + m.icon} /></div>
            <div style={{ minWidth: 0 }}>
              <div className="hz-stat-label">{m.label}</div>
              <div className="hz-stat-val">{m.value}</div>
              <div style={{ fontSize: 11, color: m.trendColor, marginTop: 4, fontWeight: 500 }}>{m.trend}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Chi phí 12 tháng + Cơ cấu phân loại */}
      <div className="hz-grid">
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <div>
              <h3 className="hz-title" style={{ marginBottom: 2 }}>Chi phí mua hàng theo tháng</h3>
              <span className="hz-sub" style={{ display: 'block' }}>Giá trị nhận hàng · năm {d?.year || ''}</span>
            </div>
            <div style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
              <select style={{ height: 32, borderRadius: 8, fontSize: 12, padding: '0 8px', border: '1px solid #eef1f8', outline: 'none', background: '#fff', cursor: 'pointer' }}>
                <option>Năm {d?.year || 2026}</option>
              </select>
              <button className="btn secondary" style={{ height: 32, padding: '0 10px', fontSize: 12, borderRadius: 8, display: 'flex', alignItems: 'center', gap: 4, background: '#fff', border: '1px solid #eef1f8', cursor: 'pointer' }} onClick={() => alert('Đang xuất báo cáo chi phí...')}>
                <i className="ti ti-download" /> Xuất
              </button>
            </div>
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <svg viewBox={`0 0 ${cw} ${ch}`} preserveAspectRatio="none" style={{ width: '100%', height: 240, display: 'block' }}>
              {cTicks.map((t, i) => {
                const y = pt + ih - (t / cmax) * ih
                return (
                  <g key={i}>
                    <line x1={pl} y1={y} x2={pl + iw} y2={y} stroke="#eef1f8" />
                    <text x={pl - 8} y={y + 4} textAnchor="end" style={{ fontSize: 11, fill: 'var(--hz-muted)' }}>{money(t)}</text>
                  </g>
                )
              })}
              {cost.map((c: any, i: number) => {
                const x = pl + (i + 0.5) * (iw / cost.length)
                const actualVal = c.value || 0
                const hActual = (actualVal / cmax) * ih
                return (
                  <g key={i}>
                    {actualVal > 0 && (
                      <rect x={x - bw / 2} y={pt + ih - hActual} width={bw} height={hActual} rx="3" fill="#00AEEF">
                        <title>{c.label}: {full(actualVal)}</title>
                      </rect>
                    )}
                    {actualVal > 0 && (
                      <text x={x} y={pt + ih - hActual - 5} textAnchor="middle" style={{ fontSize: 10, fill: 'var(--navy)', fontWeight: 700 }}>
                        {money(actualVal)}
                      </text>
                    )}
                    <text x={x} y={ch - 8} textAnchor="middle" style={{ fontSize: 10.5, fill: 'var(--hz-muted)' }}>{c.label}</text>
                  </g>
                )
              })}
            </svg>
          </div>
        </div>

        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="hz-title" style={{ marginBottom: 14 }}>Cơ cấu theo phân loại</h3>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <Donut items={cats.map((c: any, i: number) => ({ label: c.name, value: c.cost, color: CAT_COLORS[i % CAT_COLORS.length], display: `${c.pct}%` }))} />
          </div>
        </div>
      </div>

      {/* Yêu cầu mua hàng gần đây (Recent Requisitions) & Hiệu suất NCC */}
      <div className="hz-grid">
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 20px 10px' }}>
            <h3 className="hz-title">Yêu cầu mua gần đây</h3>
            <span style={{ fontSize: 13, color: 'var(--teal)', fontWeight: 600, cursor: 'pointer' }} onClick={() => navigate('/purchase-requests')}>Xem tất cả</span>
          </div>
          <div className="items-scroll">
            <table style={{ margin: 0, minWidth: 600 }}>
              <thead>
                <tr>
                  <th>Mã phiếu</th>
                  <th>Người yêu cầu / Nội dung</th>
                  <th>Bộ phận</th>
                  <th style={{ textAlign: 'right' }}>Giá trị</th>
                  <th>Trạng thái</th>
                  <th style={{ textAlign: 'center', width: 90 }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {recent_prs.length === 0 ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--hz-muted)', padding: 18 }}>Chưa có yêu cầu mua</td></tr>
                ) : (
                  recent_prs.map((r: any) => (
                    <tr key={r.id} className="clickable" onClick={() => navigate(`/purchase-requests/${r.id}`)}>
                      <td style={{ fontWeight: 600, color: 'var(--teal)' }}>{r.code}</td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{r.requester || '—'}</div>
                        <div style={{ fontSize: 11, color: 'var(--hz-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 160 }}>{r.description}</div>
                      </td>
                      <td>{r.department}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700 }}>{full(r.total)}</td>
                      <td>
                        <span className="badge" style={{
                          background: r.status === 'submitted' ? '#fff6e5' : r.status === 'approved' ? '#e7f8ec' : r.status === 'rejected' ? '#fdecea' : '#f1f5f9',
                          color: r.status === 'submitted' ? '#d97706' : r.status === 'approved' ? '#16a34a' : r.status === 'rejected' ? '#b91c1c' : '#64748b'
                        }}>
                          {r.status === 'submitted' ? 'Chờ duyệt' : r.status === 'approved' ? 'Đã duyệt' : r.status === 'rejected' ? 'Từ chối' : 'Nháp'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {r.status === 'submitted' ? (
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                            <button style={{
                              width: 26, height: 26, borderRadius: '50%', border: 'none', background: '#e7f8ec', color: '#16a34a',
                              cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12
                            }} title="Duyệt yêu cầu" onClick={(e) => { e.stopPropagation(); handleApprovePR(r.id); }}>
                              <i className="ti ti-check" />
                            </button>
                            <button style={{
                              width: 26, height: 26, borderRadius: '50%', border: 'none', background: '#fdecea', color: '#b91c1c',
                              cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12
                            }} title="Từ chối yêu cầu" onClick={(e) => { e.stopPropagation(); handleRejectPR(r.id); }}>
                              <i className="ti ti-x" />
                            </button>
                          </div>
                        ) : (
                          <span style={{ color: 'var(--hz-muted)' }}>—</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 className="hz-title">Top nhà cung cấp</h3>
            <span style={{ fontSize: 13, color: 'var(--teal)', fontWeight: 600, cursor: 'pointer' }} onClick={() => navigate('/suppliers')}>Xem tất cả</span>
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {(() => {
              const items = top_sup.slice(0, 4)
              const maxVal = Math.max(1, ...items.map((x: any) => x.value || 0))
              return items.length === 0 ? (
                <div style={{ color: 'var(--hz-muted)', fontSize: 13, textAlign: 'center' }}>Chưa có dữ liệu nhà cung cấp</div>
              ) : items.map((s: any, idx: number) => {
                const pct = Math.round(((s.value || 0) / maxVal) * 100)
                const colors = ['#00AEEF', '#92C83E', '#7c3aed', '#d97706']
                const barColor = colors[idx % colors.length]
                return (
                  <div key={idx} style={{ marginBottom: 15 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 5 }}>
                      <span style={{ fontWeight: 600, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 180 }} title={s.label}>{s.label}</span>
                      <span style={{ fontWeight: 700, color: 'var(--navy)', flex: 'none' }}>{money(s.value)}</span>
                    </div>
                    <div style={{ height: 6, background: '#f0f2f9', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ width: `${pct}%`, height: '100%', background: barColor, borderRadius: 4 }} />
                    </div>
                  </div>
                )
              })
            })()}
          </div>
        </div>
      </div>

      {/* Trạng thái đơn + Tuổi nợ */}
      <div className="hz-grid half">
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="hz-title" style={{ marginBottom: 12 }}>Trạng thái đơn hàng</h3>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <Donut items={po_status.map((s: any) => ({ label: s.label, value: s.value, color: s.color, display: String(s.value) }))} />
          </div>
        </div>
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="hz-title" style={{ marginBottom: 12 }}>Tuổi nợ (còn phải trả)</h3>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <BarList items={ap_aging} fmt={money} />
          </div>
        </div>
      </div>

      {/* Top NCC + Chi tiêu bộ phận */}
      <div className="hz-grid half">
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="hz-title" style={{ marginBottom: 12 }}>Top nhà cung cấp theo giá trị</h3>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <BarList items={top_sup} fmt={money} />
          </div>
        </div>
        <div className="hz-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 className="hz-title" style={{ marginBottom: 12 }}>Chi tiêu theo bộ phận</h3>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <BarList items={dept} fmt={money} />
          </div>
        </div>
      </div>

      {/* Cảnh báo cần xử lý (Full Width) */}
      <div className="hz-card" style={{ display: 'flex', flexDirection: 'column', marginBottom: 20 }}>
        <h3 className="hz-title" style={{ marginBottom: 12 }}>Cảnh báo cần xử lý</h3>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {alerts.length === 0 ? <div style={{ color: 'var(--hz-muted)', fontSize: 13 }}>Không có cảnh báo</div> : alerts.map((a: any, i: number) => (
            <div key={i} onClick={() => a.link && navigate(a.link)} style={{ display: 'flex', gap: 9, alignItems: 'flex-start', padding: '10px 0', fontSize: 13, cursor: 'pointer', borderBottom: i < alerts.length - 1 ? '1px solid #f2f4fa' : 'none' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', marginTop: 5, flex: 'none', background: a.level === 'danger' ? '#E24B4A' : '#D97706' }} />
              <span style={{ color: 'var(--navy)', lineHeight: 1.4 }}>{a.title}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
