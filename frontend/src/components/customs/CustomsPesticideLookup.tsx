// Cột «Tìm thuốc khác» + «Tra cứu nhanh» của trang chi tiết thuốc BVTV (01/10/2026, đồng bộ bản v2
// `customs-pesticide-lookup-sidebar.tsx`, bê theo cột trái của trang nguồn danhmuc.thuocbvtv.com):
// đang đọc một thuốc mà muốn tra thuốc khác thì gõ / chọn ngay tại đây. Bấm «Lọc» hay một phân nhóm
// là mở mục «Thuốc BVTV» với đúng bộ lọc đó (`buildPesticideListSearch`).
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import SearchSelect from '../SearchSelect'
import { customsSectionPath } from '../../config/customs-sections'
import { buildPesticideListSearch } from '../../utils/customs-pesticide'
import { toSentenceCaseIfShouting } from '../../utils/customs-pesticide-display'

const LIST_PATH = customsSectionPath('pesticides')
const TITLE = { display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: 14, margin: '0 0 10px' } as const

export default function CustomsPesticideLookup({ currentPestGroup }: { currentPestGroup: string }) {
  const navigate = useNavigate()
  const [options, setOptions] = useState<any>(null)
  const [q, setQ] = useState('')
  const [pestGroup, setPestGroup] = useState('')
  const [sector, setSector] = useState('')
  const dirty = q.trim() !== '' || pestGroup !== '' || sector !== ''

  useEffect(() => {
    api.get('/api/customs/pesticides/options', { _silent: true } as any).then((r) => setOptions(r.data.data)).catch(() => {})
  }, [])

  function submit(e: FormEvent) {
    e.preventDefault()
    navigate(`${LIST_PATH}?${buildPesticideListSearch({ q, pestGroup, sector })}`)
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <form onSubmit={submit} style={{ padding: 16, borderBottom: '1px solid var(--border)', display: 'grid', gap: 10 }}>
        <div style={TITLE}><i className="ti ti-search" style={{ color: 'var(--muted)' }} />Tìm thuốc khác</div>
        <input value={q} onChange={(e) => setQ(e.target.value)} aria-label="Tìm thuốc BVTV"
          placeholder="Tên thuốc, hoạt chất, công ty…" />
        <SearchSelect value={pestGroup} placeholder="Tất cả phân nhóm" autoSelectSingle={false}
          options={(options?.pest_groups || []).map((g: any) => ({ value: g.value, label: g.value }))}
          onChange={setPestGroup} />
        <SearchSelect value={sector} placeholder="Tất cả lĩnh vực" autoSelectSingle={false}
          options={(options?.sectors || []).map((g: any) => ({ value: g.value, label: toSentenceCaseIfShouting(g.value) }))}
          onChange={setSector} />
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" className="btn" style={{ flex: 1, justifyContent: 'center' }}>
            <i className="ti ti-search" />Lọc
          </button>
          <button type="button" className="btn ghost" disabled={!dirty}
            onClick={() => { setQ(''); setPestGroup(''); setSector('') }}>Xóa bộ lọc</button>
        </div>
      </form>

      <nav style={{ padding: 16 }} aria-label="Tra cứu nhanh theo phân nhóm">
        <div style={TITLE}><i className="ti ti-bolt" style={{ color: 'var(--muted)' }} />Tra cứu nhanh</div>
        {(options?.pest_groups || []).map((g: any) => {
          const current = g.value === currentPestGroup
          return (
            <Link key={g.value} to={`${LIST_PATH}?${buildPesticideListSearch({ pestGroup: g.value })}`}
              aria-current={current ? 'true' : undefined} title={g.value}
              style={{
                display: 'flex', justifyContent: 'space-between', gap: 8, padding: '6px 8px', borderRadius: 6,
                fontSize: 14, textDecoration: 'none',
                color: current ? 'var(--teal)' : 'var(--ink)', fontWeight: current ? 600 : 400,
                background: current ? 'var(--info-bg)' : undefined,
              }}>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{g.value}</span>
              <span style={{ color: 'var(--muted)', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                {Number(g.count).toLocaleString('vi-VN')}
              </span>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
