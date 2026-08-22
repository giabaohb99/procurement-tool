/**
 * Lọc + tổng hợp số liệu cho dashboard "Công nợ" ở màn chi tiết NCC.
 * Tách riêng khỏi phần vẽ để hàm tính thuần (dễ đọc, dễ sửa, dễ test).
 *
 * CÔNG NỢ ÂM (remaining < 0) là có thật: trả dư cho NCC, hoặc hóa đơn điều chỉnh giảm /
 * trả hàng (total âm). Quy ước xử lý ở đây:
 *   - `debt`   = CHỈ phần còn phải trả dương → dùng cho tuổi nợ, quá hạn, danh sách cần chú ý.
 *   - `credit` = tổng phần âm (đã đổi dấu, luôn ≥ 0) → tách thành chỉ số "Trả dư / ghi có" riêng.
 *   - `remainNet` = debt − credit → số dư thực còn nợ NCC (có thể âm nếu ta đang trả dư).
 * Khoản âm KHÔNG được xếp vào mốc tuổi nợ (không thể "quá hạn" một khoản mình không nợ).
 */

export const AGING_ORDER = ['Chưa đến hạn', '1-30', '31-60', '61-90', '>90']
export const AGING_COLOR: Record<string, string> = {
  'Chưa đến hạn': '#16a34a', '1-30': '#F6AD37', '31-60': '#EA580C', '61-90': '#DC2626', '>90': '#991B1B',
}
/**
 * Khóa trạng thái dùng trong dashboard này = MÃ của B-05 (`unpaid | partial | paid`) CỘNG
 * THÊM một khóa bịa: `ST_CREDIT`.
 *
 * `ST_CREDIT` KHÔNG có trong `tab_payable.status` và không có trong bộ mã ở
 * `backend/app/core/status_codes.py` — nó chỉ tồn tại ở màn này, suy ra từ `remaining < 0`
 * (xem `rowStatus`). Đừng gửi nó lên API làm tham số lọc: backend không có dòng nào mang
 * giá trị đó nên bảng sẽ rỗng mà không báo lỗi gì.
 */
export const ST_CREDIT = 'credit'
export const ST_LABEL: Record<string, string> = {
  unpaid: 'Chờ thanh toán', partial: 'Thanh toán một phần', paid: 'Đã thanh toán',
  [ST_CREDIT]: 'Trả dư / ghi có',
}
export const ST_COLOR: Record<string, string> = {
  unpaid: '#8592ae', partial: '#F6AD37', paid: '#16a34a', [ST_CREDIT]: '#0284c7',
}
export const ST_KEYS = ['unpaid', 'partial', 'paid', ST_CREDIT]
export const agingLabel = (a: string) => (a === 'Chưa đến hạn' ? a : `Quá hạn ${a} ngày`)

/** Trạng thái hiển thị — khoản âm ghi đè thành "Trả dư" dù DB vẫn lưu `paid`. */
export const rowStatus = (p: any) => ((p.remaining || 0) < 0 ? ST_CREDIT : p.status)

/** Rút gọn tiền cho nhãn biểu đồ (KPI vẫn hiện đủ số). */
export const short = (v: number) => {
  const n = Math.abs(v || 0)
  if (n >= 1e9) return (v / 1e9).toFixed(2).replace(/\.?0+$/, '') + ' tỷ'
  if (n >= 1e6) return (v / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(/\.0$/, '') + ' tr'
  if (n >= 1e3) return Math.round(v / 1e3) + 'k'
  return String(Math.round(v || 0))
}

/**
 * Lọc CƠ BẢN của tab. Các điều kiện còn lại (mã PO, số hóa đơn, loại nợ, trạng thái)
 * đã chuyển sang BỘ LỌC ĐIỀU KIỆN → gửi thẳng lên API, không xử lý ở đây.
 * `aging` / `from` / `to` cũng do API lọc; chỉ `view` phải tính ở client vì
 * "trả dư" (remaining < 0) không có tham số tương ứng ở backend.
 */
export type PayableFilters = {
  view: string        // '' | open | overdue | credit — preset xem nhanh (client)
  aging: string       // '' | Chưa đến hạn | 1-30 | 31-60 | 61-90 | >90  (API)
  from: string        // ngày phát sinh từ (YYYY-MM-DD) (API)
  to: string          // ngày phát sinh đến (API)
}

export const EMPTY_PAYABLE_FILTERS: PayableFilters = { view: '', aging: '', from: '', to: '' }

export const hasFilter = (f: PayableFilters) =>
  Object.values(f).some((v) => String(v || '').trim() !== '')

/** Ngày phát sinh dùng để nhóm theo tháng — ưu tiên incur_date, thiếu thì lấy created_at. */
const incurOf = (p: any) => String(p.incur_date || p.created_at || '').slice(0, 10)

export function applyPayableFilters(rows: any[], f: PayableFilters): any[] {
  if (!f.view) return rows
  return rows.filter((p) => {
    const rem = p.remaining || 0
    if (f.view === 'open') return rem > 0
    if (f.view === 'overdue') return rem > 0 && p.aging && p.aging !== 'Chưa đến hạn'
    if (f.view === 'credit') return rem < 0
    return true
  })
}

export function buildPayableStats(rows: any[]) {
  const sum = (list: any[], f: (p: any) => number) => list.reduce((s, p) => s + (f(p) || 0), 0)
  const total = sum(rows, (p) => p.total)
  const paid = sum(rows, (p) => p.paid_amount)

  const debtRows = rows.filter((p) => (p.remaining || 0) > 0)
  const creditRows = rows.filter((p) => (p.remaining || 0) < 0)
  const debt = sum(debtRows, (p) => p.remaining)
  const credit = -sum(creditRows, (p) => p.remaining)   // đổi dấu → luôn ≥ 0
  const overdueRows = debtRows.filter((p) => p.aging && p.aging !== 'Chưa đến hạn')

  const aging = AGING_ORDER.map((k) => {
    const g = debtRows.filter((p) => (p.aging || 'Chưa đến hạn') === k)
    return {
      label: agingLabel(k), value: sum(g, (p) => p.remaining),
      color: AGING_COLOR[k], note: g.length ? `${g.length} khoản` : '',
    }
  })
  const bySource = [
    { key: 'goods', label: 'Hàng hóa', color: '#00AEEF' },
    { key: 'shipping', label: 'Vận chuyển', color: '#7C8DB5' },
  ].map((s) => {
    const g = rows.filter((p) => p.source_type === s.key)
    return { label: s.label, value: sum(g, (p) => p.total), color: s.color, note: g.length ? `${g.length} khoản` : '' }
  })
  const byStatus = ST_KEYS.map((k) => {
    const g = rows.filter((p) => rowStatus(p) === k)
    // Nhóm "Trả dư" đo bằng số dư âm (tổng phát sinh của phiếu điều chỉnh giảm không nói lên gì)
    const value = k === ST_CREDIT ? sum(g, (p) => p.remaining) : sum(g, (p) => p.total)
    return { label: ST_LABEL[k], value, color: ST_COLOR[k], note: g.length ? `${g.length} khoản` : '' }
  }).filter((x) => x.note || x.label !== ST_LABEL[ST_CREDIT])   // ẩn dòng "Trả dư" khi không có

  // Phát sinh theo tháng — 6 tháng gần nhất CÓ dữ liệu
  const m = new Map<string, number>()
  rows.forEach((p) => {
    const k = incurOf(p).slice(0, 7)
    if (k.length === 7) m.set(k, (m.get(k) || 0) + (p.total || 0))
  })
  const months = [...m.entries()].sort((a, b) => a[0].localeCompare(b[0])).slice(-6)
    .map(([k, v]) => ({ k, label: `T${Number(k.slice(5, 7))}/${k.slice(2, 4)}`, value: v }))

  // Cần chú ý: quá hạn nặng nhất trước, rồi tới số tiền còn lại lớn nhất
  const attention = [...debtRows].sort((a, b) =>
    (AGING_ORDER.indexOf(b.aging) - AGING_ORDER.indexOf(a.aging)) || (b.remaining - a.remaining)).slice(0, 6)

  return {
    total, paid, debt, credit, remainNet: debt - credit,
    overdue: sum(overdueRows, (p) => p.remaining), overdueCount: overdueRows.length,
    openCount: debtRows.length, creditCount: creditRows.length,
    aging, bySource, byStatus, months, attention,
  }
}
