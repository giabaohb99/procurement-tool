import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { fmtVND } from '../utils/money'
import { ConditionalFilter, RestQueryParams } from './conditional-filter'
import { SUPPLIER_PAYABLE_COND_FILTERS } from '../config/conditional-filters'
import SupplierPayablesFilters from './supplier-payables-filters'
import {
  agingLabel, AGING_COLOR, applyPayableFilters, buildPayableStats, EMPTY_PAYABLE_FILTERS,
  hasFilter, PayableFilters, rowStatus, short, ST_COLOR, ST_CREDIT, ST_LABEL,
} from './supplier-payables-stats'

/**
 * Tab "Công nợ" của trang chi tiết NCC — dạng BÁO CÁO DASHBOARD:
 * thanh lọc → KPI → tiến độ thanh toán → tuổi nợ / cơ cấu / trạng thái →
 * biểu đồ theo tháng → khoản cần chú ý. Bảng chi tiết vẫn còn nhưng gập lại.
 * Mọi khối đều tính trên PHẦN ĐÃ LỌC. Quy ước xử lý nợ âm: xem supplier-payables-stats.ts.
 *
 * Tab TỰ GỌI `/api/payables` (không nhận sẵn danh sách) vì BỘ LỌC ĐIỀU KIỆN sinh query param
 * cho backend — mã PO / số hóa đơn / loại nợ / trạng thái đều lọc ở DB.
 */

// Tiền có dấu — nợ âm (trả dư) hiện "-x đ" màu xanh để không nhìn nhầm thành nợ phải trả
const signed = (v: number) => `${v < 0 ? '-' : ''}${fmtVND(Math.abs(v))} đ`

function Stat({ label, value, sub, color, icon, bg }: any) {
  return (
    <div className="card" style={{ padding: 14, flex: 1, minWidth: 168, display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 40, height: 40, borderRadius: 11, flex: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', background: bg, color, fontSize: 19 }}>
        <i className={'ti ' + icon} />
      </div>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: 12.5, color: 'var(--hz-muted)', fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 19, fontWeight: 700, color, lineHeight: 1.2, whiteSpace: 'nowrap' }}>{value}</div>
        {sub && <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>}
      </div>
    </div>
  )
}

/** Thanh ngang: nhãn – giá trị – bar tỉ lệ. Bề rộng theo |giá trị| để số âm vẫn vẽ được. */
function BarRows({ items }: { items: { label: string; value: number; color: string; note?: string }[] }) {
  const max = Math.max(1, ...items.map((i) => Math.abs(i.value)))
  if (!items.some((i) => i.value !== 0)) return <div style={{ color: 'var(--muted)', fontSize: 13 }}>Chưa có dữ liệu</div>
  return (
    <>
      {items.map((it) => (
        <div key={it.label} style={{ marginBottom: 11 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, fontSize: 12.5, marginBottom: 4 }}>
            <span style={{ color: 'var(--navy)', fontWeight: 500 }}>{it.label}{it.note ? <span style={{ color: 'var(--muted)', fontWeight: 400 }}> · {it.note}</span> : null}</span>
            <span style={{ fontWeight: 700, color: it.value < 0 ? '#0284c7' : 'var(--navy)', flex: 'none' }}>{it.value < 0 ? '-' : ''}{fmtVND(Math.abs(it.value))}</span>
          </div>
          <div className="hz-bar-track"><div className="hz-bar-fill" style={{ width: `${(Math.abs(it.value) / max) * 100}%`, background: it.color }} /></div>
        </div>
      ))}
    </>
  )
}

const H3: React.CSSProperties = { margin: '0 0 14px', fontSize: 14.5, fontWeight: 700, color: 'var(--navy)' }

/**
 * Khối ĐÁNH GIÁ NCC (gộp từ tab "Đánh giá" cũ) — KPI giao hàng cả kỳ + số hợp đồng.
 * Đặt TRÊN thanh lọc và không đổi theo bộ lọc công nợ: đây là số của toàn bộ lịch sử giao dịch,
 * lọc theo khoản nợ sẽ làm sai ý nghĩa.
 */
function SupplierScorecard({ kpi, contractCount }: { kpi: any; contractCount: number }) {
  const late = kpi && kpi.rate > 30
  const cell = (label: string, value: any, color?: string) => (
    <div style={{ minWidth: 130 }}>
      <div style={{ fontSize: 12.5, color: 'var(--hz-muted)', fontWeight: 500 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || 'var(--navy)' }}>{value}</div>
    </div>
  )
  return (
    <div className="card" style={{ padding: 18 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        <h3 style={{ ...H3, margin: 0 }}>Đánh giá nhà cung cấp</h3>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>· cả kỳ, không theo bộ lọc bên dưới</span>
        {late && <span className="badge err">Tỷ lệ giao trễ cao (&gt;30%)</span>}
      </div>
      <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
        {kpi ? <>
          {cell('Số lần giao dịch', fmtVND(kpi.trans))}
          {cell('Số lần giao trễ', fmtVND(kpi.late), kpi.late > 0 ? 'var(--red)' : undefined)}
          {cell('Tỷ lệ trễ', `${fmtVND(kpi.rate)}%`, late ? 'var(--red)' : undefined)}
        </> : <div style={{ fontSize: 13, color: '#999', alignSelf: 'center' }}>Chưa có dữ liệu giao dịch.</div>}
        {cell('Số hợp đồng', contractCount)}
      </div>
    </div>
  )
}

function Dashboard({ supplierCode, cond, kpi, contractCount }: {
  supplierCode?: string; cond: RestQueryParams; kpi: any; contractCount: number
}) {
  const navigate = useNavigate()
  const [openDetail, setOpenDetail] = useState(false)
  const [f, setF] = useState<PayableFilters>({ ...EMPTY_PAYABLE_FILTERS })
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  // Gõ trong bảng lọc điều kiện đổi param liên tục → chờ 300ms cho lắng rồi mới gọi API
  const timer = useRef<any>(null)
  useEffect(() => {
    if (!supplierCode) { setRows([]); setLoading(false); return }
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      const params: any = { supplier_code: supplierCode, year: 'all', page_size: 500, ...cond }
      if (f.aging) params.aging = f.aging
      if (f.from) params.incur_from = f.from
      if (f.to) params.incur_to = f.to
      api.get('/api/payables', { params })
        .then((r) => setRows(r.data.data.items))
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(timer.current)
  }, [supplierCode, cond, f.aging, f.from, f.to])

  const filtered = useMemo(() => applyPayableFilters(rows, f), [rows, f])
  const d = useMemo(() => buildPayableStats(filtered), [filtered])

  // Tỉ lệ đã trả — chặn 0..100; tổng ≤ 0 (toàn phiếu điều chỉnh giảm) thì không có gì để chia
  const paidPct = d.total > 0 ? Math.max(0, Math.min(100, (d.paid / d.total) * 100)) : 0
  const maxMonth = Math.max(1, ...d.months.map((x) => Math.abs(x.value)))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SupplierScorecard kpi={kpi} contractCount={contractCount} />
      <SupplierPayablesFilters value={f} onChange={setF} shown={filtered.length} loaded={rows.length} />

      {loading ? (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: '#999' }}>Đang tải công nợ…</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: 'center', color: '#999' }}>
          {hasFilter(f) || Object.keys(cond).length ? <>
            <i className="ti ti-filter-off" style={{ fontSize: 30, display: 'block', marginBottom: 8, color: '#cbd5e1' }} />
            Không có khoản công nợ nào khớp bộ lọc
          </> : <>
            <i className="ti ti-report-money" style={{ fontSize: 34, display: 'block', marginBottom: 8, color: '#cbd5e1' }} />
            Nhà cung cấp này chưa phát sinh công nợ
          </>}
        </div>
      ) : (
      <>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Stat label="Tổng phát sinh" value={signed(d.total)} sub={`${filtered.length} khoản nợ`} color="var(--navy)" bg="#eef2ff" icon="ti-receipt-2" />
        <Stat label="Đã thanh toán" value={signed(d.paid)} color="#16a34a" bg="#dcfce7" icon="ti-circle-check"
          sub={d.paid > d.total ? 'Đã trả vượt tổng phát sinh' : `${paidPct.toFixed(1)}% tổng nợ`} />
        <Stat label="Còn phải trả" value={signed(d.remainNet)}
          sub={d.credit > 0 ? `${d.openCount} khoản nợ · đã trừ ${fmtVND(d.credit)} trả dư` : `${d.openCount} khoản chưa tất toán`}
          color={d.remainNet < 0 ? '#0284c7' : 'var(--teal)'} bg="#e0f2fe" icon="ti-wallet" />
        <Stat label="Quá hạn" value={signed(d.overdue)} sub={`${d.overdueCount} khoản quá hạn`} color="#DC2626" bg="#fee2e2" icon="ti-alert-triangle" />
        {d.credit > 0 && (
          <Stat label="Trả dư / ghi có" value={`-${fmtVND(d.credit)} đ`} sub={`${d.creditCount} khoản NCC còn giữ`} color="#0284c7" bg="#e0f2fe" icon="ti-arrow-back-up" />
        )}
      </div>

      <div className="card" style={{ padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
          <h3 style={{ ...H3, margin: 0 }}>Tiến độ thanh toán</h3>
          <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>Đã trả <b style={{ color: '#16a34a' }}>{fmtVND(d.paid)}</b> / {fmtVND(d.total)} — còn <b style={{ color: d.remainNet < 0 ? '#0284c7' : 'var(--teal)' }}>{signed(d.remainNet)}</b></span>
        </div>
        <div style={{ display: 'flex', height: 14, borderRadius: 8, overflow: 'hidden', background: '#f0f2f9' }}>
          <div style={{ width: `${paidPct}%`, background: '#16a34a', transition: 'width .5s ease' }} title={`Đã trả ${fmtVND(d.paid)}`} />
          <div style={{ flex: 1, background: d.overdue > 0 ? '#fca5a5' : '#7dd3fc' }} title={`Còn phải trả ${fmtVND(d.debt)}`} />
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: 'var(--muted)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <span><span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 3, background: '#16a34a', marginRight: 5 }} />Đã thanh toán</span>
          <span><span style={{ display: 'inline-block', width: 9, height: 9, borderRadius: 3, background: d.overdue > 0 ? '#fca5a5' : '#7dd3fc', marginRight: 5 }} />Còn phải trả{d.overdue > 0 ? ' (có khoản quá hạn)' : ''}</span>
          {d.credit > 0 && <span style={{ color: '#0284c7' }}>Đã trả dư cho NCC {fmtVND(d.credit)} đ — trừ vào lần thanh toán sau</span>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
        <div className="card" style={{ padding: 18 }}>
          <h3 style={H3}>Tuổi nợ (còn phải trả)</h3>
          <BarRows items={d.aging} />
          {d.credit > 0 && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px dashed var(--border)', fontSize: 12, color: '#0284c7' }}>
              <i className="ti ti-info-circle" /> {d.creditCount} khoản trả dư (-{fmtVND(d.credit)} đ) không xếp mốc tuổi nợ.
            </div>
          )}
        </div>
        <div className="card" style={{ padding: 18 }}>
          <h3 style={H3}>Cơ cấu nợ theo loại</h3>
          <BarRows items={d.bySource} />
        </div>
        <div className="card" style={{ padding: 18 }}>
          <h3 style={H3}>Trạng thái khoản nợ</h3>
          <BarRows items={d.byStatus} />
        </div>
      </div>

      {/* alignItems:start — thẻ biểu đồ không bị kéo dài theo thẻ danh sách bên phải */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16, alignItems: 'start' }}>
        <div className="card" style={{ padding: 18 }}>
          <h3 style={H3}>Nợ phát sinh theo tháng</h3>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', minHeight: 150 }}>
            {d.months.map((m) => (
              <div key={m.k} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 4 }}>{short(m.value)}</div>
                {/* maxWidth: 1-2 tháng dữ liệu thì cột không phình ra cả khung */}
                <div title={signed(m.value)} style={{
                  height: Math.max(4, (Math.abs(m.value) / maxMonth) * 110), maxWidth: 54, margin: '0 auto',
                  background: m.value < 0 ? 'linear-gradient(180deg,#fca5a5,#dc2626)' : 'linear-gradient(180deg,#38bdf8,#0284c7)',
                  borderRadius: '6px 6px 0 0',
                }} />
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 6 }}>{m.label}</div>
              </div>
            ))}
            {!d.months.length && <div style={{ color: 'var(--muted)', fontSize: 13 }}>Chưa có dữ liệu</div>}
          </div>
        </div>

        <div className="card" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 8 }}>
            <h3 style={{ ...H3, margin: 0 }}>Khoản nợ cần chú ý</h3>
            {supplierCode && <button className="btn ghost" style={{ padding: '4px 10px', fontSize: 12.5 }} onClick={() => navigate(`/payables?supplier=${encodeURIComponent(supplierCode)}`)}>Mở trang công nợ</button>}
          </div>
          {d.attention.length === 0 && <div style={{ color: 'var(--muted)', fontSize: 13 }}>Không còn khoản nợ nào phải trả</div>}
          {d.attention.map((p) => (
            <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px dashed var(--border)' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.po_code || '—'}{p.invoice_no ? ` · HĐ ${p.invoice_no}` : ''}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>
                  {p.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'} · Hạn trả {p.due_date || '—'}
                </div>
              </div>
              <div style={{ textAlign: 'right', flex: 'none' }}>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--navy)' }}>{fmtVND(p.remaining)}</div>
                <span style={{ fontSize: 11, fontWeight: 600, color: AGING_COLOR[p.aging] || 'var(--muted)' }}>{agingLabel(p.aging || 'Chưa đến hạn')}</span>
              </div>
            </div>
          ))}
          {d.credit > 0 && f.view !== 'credit' && (
            <div style={{ marginTop: 10, fontSize: 12, color: '#0284c7' }}>
              <i className="ti ti-arrow-back-up" /> Có {d.creditCount} khoản trả dư / ghi có — lọc "Xem nhanh → Trả dư" để xem.
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: 18 }}>
        <button onClick={() => setOpenDetail((v) => !v)} style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, fontWeight: 700, color: 'var(--navy)' }}>
          <i className={'ti ' + (openDetail ? 'ti-chevron-down' : 'ti-chevron-right')} />Chi tiết {filtered.length} khoản công nợ{hasFilter(f) ? ' (đã lọc)' : ''}
        </button>
        {openDetail && (
          <div className="items-scroll" style={{ marginTop: 12 }}>
            <table className="items-table" style={{ minWidth: 760 }}>
              <thead><tr><th>Loại</th><th>PO</th><th>Số HĐ</th><th>Ngày PS</th><th>Hạn trả</th><th style={{ textAlign: 'right' }}>Tổng</th><th style={{ textAlign: 'right' }}>Đã trả</th><th style={{ textAlign: 'right' }}>Còn lại</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {filtered.map((p) => {
                  const st = rowStatus(p)
                  return (
                    <tr key={p.id}>
                      <td>{p.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td><td>{p.po_code}</td><td>{p.invoice_no}</td>
                      <td>{p.incur_date}</td><td>{p.due_date}</td>
                      <td style={{ textAlign: 'right' }}>{fmtVND(p.total)}</td><td style={{ textAlign: 'right' }}>{fmtVND(p.paid_amount)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: p.remaining < 0 ? ST_COLOR[ST_CREDIT] : undefined }}>{fmtVND(p.remaining)}</td>
                      <td>
                        {/* chưa có class badge cho "Trả dư" nên tô màu trực tiếp */}
                        <span className={'badge ' + (st === 'paid' ? 'ok' : st === 'partial' ? 'warn' : 'gray')}
                          style={st === ST_CREDIT ? { background: '#e0f2fe', color: ST_COLOR[ST_CREDIT] } : undefined}>
                          {ST_LABEL[st] || st}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
      </>
      )}
    </div>
  )
}

/** Bọc provider của bộ lọc điều kiện — nút "Bộ lọc điều kiện" nằm trong thanh lọc bên dưới. */
export default function SupplierPayablesDashboard({ supplierCode, kpi, contractCount = 0 }: {
  supplierCode?: string
  kpi?: any            // 1 dòng từ /api/reports/matrix — KPI giao hàng cả kỳ
  contractCount?: number
}) {
  const [cond, setCond] = useState<RestQueryParams>({})
  return (
    <ConditionalFilter fields={SUPPLIER_PAYABLE_COND_FILTERS} onChange={setCond}>
      <Dashboard supplierCode={supplierCode} cond={cond} kpi={kpi} contractCount={contractCount} />
    </ConditionalFilter>
  )
}
