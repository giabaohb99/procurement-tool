import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import Pagination from '../../components/Pagination'
import SegmentedFilter from './segmented-filter'

// Nhãn + màu + icon cho từng loại việc cần làm (cố định, không phụ thuộc dữ liệu đang lọc)
const TASK_TYPES: { key: string; label: string; short: string; color: string; icon: string }[] = [
  { key: 'pr', label: 'YCMH chờ duyệt', short: 'YCMH', color: '#2563eb', icon: 'ti-file-invoice' },
  { key: 'sr', label: 'Khảo sát chờ duyệt', short: 'Khảo sát', color: '#0891b2', icon: 'ti-clipboard-search' },
  { key: 'po', label: 'ĐMH chờ duyệt', short: 'ĐMH', color: '#7c3aed', icon: 'ti-shopping-cart' },
  { key: 'late', label: 'Giao hàng trễ', short: 'Giao trễ', color: '#d97706', icon: 'ti-truck-delivery' },
  { key: 'payable', label: 'Công nợ quá hạn', short: 'Quá hạn', color: '#dc2626', icon: 'ti-cash' },
]
const TASK_META = Object.fromEntries(TASK_TYPES.map((t) => [t.key, t]))

/** Tổng số việc mọi loại từ `by_type` của API — dùng cho badge trên tab. */
export const sumTaskCounts = (byType: Record<string, any> | undefined) =>
  Object.values(byType || {}).reduce((a: number, b: any) => a + Number(b || 0), 0)

/** Tab "Việc cần làm" — danh sách việc đang chờ chính mình xử lý, bấm vào đi thẳng tới chứng từ. */
export default function TasksTab({ onCount }: { onCount?: (n: number) => void }) {
  const nav = useNavigate()
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [byType, setByType] = useState<Record<string, number>>({})
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const timer = useRef<any>(null)

  async function load(p = page, s = pageSize, t = type, qq = q) {
    setLoading(true)
    const params: any = { page: p, page_size: s }
    if (t) params.type = t
    if (qq.trim()) params.q = qq.trim()
    try {
      const r = await api.get('/api/dashboard/tasks', { params })
      const d = r.data.data
      setItems(d.items || []); setTotal(d.total || 0); setByType(d.by_type || {})
      // Badge trên tab đếm TỔNG mọi loại, không đổi theo bộ lọc đang chọn
      onCount?.(sumTaskCounts(d.by_type))
    } finally { setLoading(false) }
  }
  // Đổi loại → lọc lại (chủ động chọn, không tự lọc trước)
  useEffect(() => { setPage(1); load(1, pageSize, type, q) /* eslint-disable-next-line */ }, [type])
  // Tìm kiếm: debounce 350ms
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => { setPage(1); load(1, pageSize, type, q) }, 350)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line
  }, [q])
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, type, q) }

  const allCount = Object.values(byType).reduce((a, b) => a + b, 0)
  const options = [
    { key: '', label: 'Tất cả', count: allCount },
    ...TASK_TYPES.map((t) => ({ key: t.key, label: t.short, count: byType[t.key] || 0 })),
  ]
  const activeLabel = type ? TASK_META[type]?.label : ''

  return (
    <div>
      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <SegmentedFilter options={options} value={type} onChange={setType} />
        <div style={{ flex: '1 1 240px', maxWidth: 340, position: 'relative' }}>
          <input value={q} placeholder="Tìm theo mã / tên / nội dung…" onChange={(e) => setQ(e.target.value)} style={{ paddingLeft: 36 }} />
          <i className="ti ti-search" style={{ position: 'absolute', left: 13, top: 12, color: '#b6c2d9', fontSize: 15 }} />
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {loading && items.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>Đang tải…</div>
        )}
        {!loading && items.length === 0 && (
          <div style={{ padding: '40px 20px', textAlign: 'center' }}>
            <i className="ti ti-circle-check" style={{ fontSize: 34, color: 'var(--green)' }} />
            <div style={{ marginTop: 10, fontSize: 14.5, fontWeight: 600, color: 'var(--navy)' }}>
              {q || type ? 'Không có việc nào khớp bộ lọc' : 'Không có việc nào cần xử lý'}
            </div>
            <div style={{ marginTop: 4, fontSize: 13, color: 'var(--muted)' }}>
              {q || type ? 'Thử bỏ bớt từ khóa hoặc chọn "Tất cả".' : 'Việc chờ bạn duyệt hoặc theo dõi sẽ hiện ở đây.'}
            </div>
          </div>
        )}
        {items.map((t, i) => {
          const m = TASK_META[t.type] || { color: '#64748b', icon: 'ti-point' }
          return (
            <div
              key={i}
              onClick={() => t.link && nav(t.link)}
              className="clickable"
              style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', borderTop: i ? '1px solid #f1f5f9' : 0, cursor: 'pointer' }}
            >
              {/* Ô icon nền màu theo loại việc — phân biệt loại nhanh hơn chữ */}
              <span
                style={{
                  width: 36, height: 36, borderRadius: 10, flex: 'none', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', background: m.color + '18', color: m.color,
                }}
              >
                <i className={'ti ' + m.icon} style={{ fontSize: 18 }} />
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
                  {t.code} {t.title ? <span style={{ color: 'var(--muted)', fontWeight: 500 }}>· {t.title}</span> : null}
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 3 }}>
                  <span style={{ fontWeight: 700, color: m.color }}>{t.label}</span>
                  {t.subtitle ? <span> · {t.subtitle}</span> : null}
                </div>
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8', whiteSpace: 'nowrap' }}>{t.date}</div>
              <i className="ti ti-chevron-right" style={{ color: '#cbd5e1' }} />
            </div>
          )
        })}
      </div>

      {total > 0 && (
        <div style={{ fontSize: 12.5, color: 'var(--muted)', margin: '10px 2px 0' }}>
          {activeLabel ? `Đang lọc: ${activeLabel} · ` : ''}{total} việc
        </div>
      )}
      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
