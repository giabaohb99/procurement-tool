import type { ReportMetricGoodDirection, ReportMetricKind } from '../types/report-analytics'

/**
 * Phần trăm thay đổi so với kỳ trước. `null` khi MỘT trong hai vế là `null`
 * (chỉ số dẫn xuất mẫu số 0 ở kỳ này hoặc kỳ trước — xem `ReportMetricValues`),
 * không phải số hữu hạn, hoặc kỳ trước bằng 0: "tăng vô hạn %" không nói được
 * gì, màn hình ghi "—"/"Chưa có kỳ trước".
 */
export function percentChange(current: number | null, previous: number | null): number | null {
  if (current === null || previous === null) return null
  if (!Number.isFinite(current) || !Number.isFinite(previous) || previous === 0) return null
  return ((current - previous) / Math.abs(previous)) * 100
}

/** Tỷ lệ phần trăm an toàn: mẫu 0 thì `null` (chưa có giao hàng nào để đo). */
export function ratePercent(part: number, total: number): number | null {
  if (!Number.isFinite(part) || !Number.isFinite(total) || total <= 0) return null
  return (part / total) * 100
}

/**
 * Chênh lệch ĐIỂM phần trăm: `current − previous`. Dùng cho chỉ số
 * `kind: 'percent'` — so % TƯƠNG ĐỐI của một tỷ lệ đọc sai nghĩa (80%→40% là
 * "−50%" tương đối nhưng thực chất giảm 40 ĐIỂM), nên đơn vị đúng ở đây là
 * điểm phần trăm, không phải % thay đổi.
 */
export function percentPointChange(current: number | null, previous: number | null): number | null {
  if (current === null || previous === null) return null
  if (!Number.isFinite(current) || !Number.isFinite(previous)) return null
  return current - previous
}

export interface MetricChange {
  value: number | null
  unit: '%' | 'điểm'
}

/**
 * Thay đổi hiển thị của MỘT chỉ số — đơn vị đi theo `kind` do backend khai:
 * `percent` → điểm phần trăm (`percentPointChange`), còn lại → % tương đối
 * (`percentChange`). Điểm gọi DUY NHẤT cho thẻ KPI (`ReportKpiRow`,
 * `ReportOverviewKpiStrip`) và cột bảng "Xem theo" (`ReportGroupedTable`) để
 * ba nơi đó không lệch quy ước với nhau.
 */
export function resolveMetricChange(
  current: number | null,
  previous: number | null,
  kind: ReportMetricKind,
): MetricChange {
  if (kind === 'percent') return { value: percentPointChange(current, previous), unit: 'điểm' }
  return { value: percentChange(current, previous), unit: '%' }
}

/** Định dạng thay đổi có dấu: "+12,3%" · "−4 điểm". Dùng chung cho thẻ KPI VÀ ô bảng. */
export function formatMetricChange(change: number, unit: '%' | 'điểm'): string {
  const abs = Math.abs(change).toLocaleString('vi-VN', { maximumFractionDigits: 1 })
  const sign = change > 0 ? '+' : change < 0 ? '−' : ''
  return unit === '%' ? `${sign}${abs}%` : `${sign}${abs} điểm`
}

/**
 * "Nhãn" TRẠNG THÁI của một thay đổi — phân biệt bốn tình huống hay bị gộp
 * chung thành một con số dễ đọc sai:
 *  - `'unavailable'` — thiếu một trong hai vế (chưa có dữ liệu để so), KHÔNG vẽ gì.
 *  - `'new'` — kỳ trước bằng 0, kỳ này > 0: đây là chỉ số MỚI phát sinh, không
 *    phải "tăng vô hạn %" (`percentChange` trả `null` đúng lúc này — coi `null`
 *    kèm `compareValue === 0` là tín hiệu để phân biệt với `'unavailable'` thật).
 *    Chỉ áp cho các `kind` tính % TƯƠNG ĐỐI; `kind: 'percent'` tính CHÊNH ĐIỂM
 *    nên kỳ trước 0 vẫn ra một con số có nghĩa (vd 0% → 12% = "+12 điểm").
 *  - `'flat'` — làm tròn về đúng 0 (vd 0,04% làm tròn 1 chữ số thập phân).
 *  - `'value'` — có một con số thật để hiện.
 */
export type MetricChangeKind = 'unavailable' | 'new' | 'flat' | 'value'

export interface MetricChangeDescription {
  kind: MetricChangeKind
  /** Chuỗi đã định dạng sẵn: "+20%", "−4,4 điểm", "Mới", "Không đổi". Rỗng khi `unavailable`. */
  text: string
  /** Màu theo `metric.good` — `'neutral'` khi chiều không mang nghĩa tốt/xấu. */
  tone: 'good' | 'bad' | 'neutral'
  direction: 'up' | 'down' | 'flat' | null
}

/**
 * Gộp `resolveMetricChange` + việc phân loại/tô màu vào MỘT hàm — nguồn DUY
 * NHẤT cho cả "pill" thay đổi (dòng Tổng của bảng "Xem theo", thẻ KPI) lẫn dòng
 * tooltip của các dòng nhóm, để ba nơi đó không tự suy diễn ba kiểu khác nhau.
 */
export function describeMetricChange(
  current: number | null,
  compareValue: number | null,
  kind: ReportMetricKind,
  good: ReportMetricGoodDirection,
): MetricChangeDescription {
  if (current === null || compareValue === null) {
    return { kind: 'unavailable', text: '', tone: 'neutral', direction: null }
  }

  const { value: change, unit } = resolveMetricChange(current, compareValue, kind)
  if (change === null) {
    //  `percentChange` trả `null` khi mẫu (kỳ trước) bằng 0 — dù kỳ này > 0
    //  ("Mới") hay CŨNG bằng 0 ("Không đổi", cả hai kỳ đều chưa phát sinh gì).
    //  Chỉ thật sự "chưa có dữ liệu" khi kỳ trước là số khác 0 nhưng không hữu
    //  hạn (NaN/Infinity) — trường hợp đó đã bị chặn ở `current/compareValue
    //  === null` phía trên, nên tới đây `compareValue === 0` luôn đúng.
    if (compareValue === 0) {
      return current > 0
        ? { kind: 'new', text: 'Mới', tone: 'neutral', direction: null }
        : { kind: 'flat', text: 'Không đổi', tone: 'neutral', direction: 'flat' }
    }
    return { kind: 'unavailable', text: '', tone: 'neutral', direction: null }
  }

  const rounded = Math.round(change * 10) / 10
  if (rounded === 0) {
    return { kind: 'flat', text: 'Không đổi', tone: 'neutral', direction: 'flat' }
  }

  const direction: 'up' | 'down' = rounded > 0 ? 'up' : 'down'
  const tone = !good ? 'neutral' : direction === good ? 'good' : 'bad'
  return { kind: 'value', text: formatMetricChange(rounded, unit), tone, direction }
}

/**
 * Đuôi chữ cạnh nhãn ±% trên thẻ KPI. Cố ý NGẮN: năm thẻ chung một hàng thì
 * "so với cùng kỳ năm trước" bị cắt cụt thành "so với cùng kỳ năm trư…".
 */
export function compareCaption(compareMode: 'previous' | 'year' | 'none'): string {
  return compareMode === 'year' ? 'so với năm trước' : 'so với kỳ trước'
}
