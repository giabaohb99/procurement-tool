/**
 * duoc-CR-784 — mảnh nhỏ dùng chung của các bản in cụm Giá bao bì (bản v1): ô mã chọn nhiều (chỉ đọc), hàng thẻ số liệu.
 * Class (`ms-box`, `mchip`, `kpi`...) là của `packaging-print.css`, chỉ có tác dụng dưới gốc `.pp` của khung in.
 */

/** Trần số chip hiện ra — chọn cả nhóm là vài trăm mã, in hết thì ô lọc chiếm cả trang. */
const MAX_CHIPS = 30

/** Ô mã đã chọn (giống ô chọn nhiều của bản mẫu nhưng chỉ đọc); không chọn mã nào thì hiện câu `emptyText`. */
export function PrintChipsBox({ codes, emptyText }: { codes: readonly string[]; emptyText: string }) {
  return (
    <div className="ms-box">
      {codes.length === 0 && <span className="ph">{emptyText}</span>}
      {codes.slice(0, MAX_CHIPS).map((c) => <span key={c} className="mchip">{c}</span>)}
      {codes.length > MAX_CHIPS && <span className="mchip more">+{codes.length - MAX_CHIPS} mã nữa</span>}
    </div>
  )
}

/** Một thẻ số liệu của bản in: số to (kèm đơn vị nhỏ), tối đa hai dòng phụ, `tone` tô màu số (tăng = đỏ). */
export interface PrintKpiItem { label: string; value: string; unit?: string; sub?: string; detail?: string; tone?: 'up' | 'down' }

/** Hàng thẻ số liệu (nhãn nhỏ, số navy to). Giá trị dài (khoảng ngày, câu "Không có…") hạ cỡ chữ để khỏi tràn thẻ. */
export function PrintKpis({ items, hint }: { items: readonly PrintKpiItem[]; hint?: string }) {
  return (
    <div className="kpis">
      {items.map((it, i) => (
        <div key={it.label} className="panel kpi">
          <div className="k">{it.label}</div>
          <div className={['v', it.value.length > 12 && 'long', it.tone].filter(Boolean).join(' ')}>
            {it.value}{it.unit && <small> {it.unit}</small>}
          </div>
          {it.sub && <div className={it.tone ? `s ${it.tone}` : 's'}>{it.sub}</div>}
          {it.detail && <div className="s dt">{it.detail}</div>}
          {i === 0 && hint && <div className="s">{hint}</div>}
        </div>
      ))}
    </div>
  )
}
