/**
 * duoc-CR-784 — luật thuần của biểu đồ giá THEO THÀNH PHẦN của Lịch sử mua hàng chế độ sản phẩm (đúng một sản phẩm được chọn,
 * máy chủ trả `series_by_code`): kiểu đường theo vai trò, hàng dữ liệu chung cho màn hình và bản in, nhãn chú giải, trục giá.
 *
 * Màu gán theo VAI TRÒ chứ không theo thứ tự có mặt (luật bộ màu biểu đồ trong `index.css`: lọc bớt chuỗi không được đổi màu
 * chuỗi còn lại). Bộ màu chỉ có 4 tông đã kiểm mù màu nên đường thứ 5 (thùng) dùng xám của chữ phụ và nét đứt.
 */
import { formatDate } from '@/shared/utils/format-date'

import type { PackagingHistorySeriesLine } from '../types/packaging-cost-types'
import { historyRoleText, priceAxisDomain } from './packaging-history'

export interface HistoryLineStyle {
  /** Màu cho giao diện (token biểu đồ, sáng / tối tự đổi). */
  css: string
  /** Màu cho bản in (SVG tĩnh, không có biến CSS của giao diện). */
  print: string
  /** `strokeDasharray`; rỗng = nét liền. */
  dash: string
}

/** Năm kiểu đường theo thứ tự vai trò chai → thùng. */
export const HISTORY_LINE_STYLES: readonly HistoryLineStyle[] = [
  { css: 'var(--chart-1)', print: '#2a78d6', dash: '' },
  { css: 'var(--chart-2)', print: '#eb6834', dash: '' },
  { css: 'var(--chart-3)', print: '#1baf7a', dash: '' },
  { css: 'var(--chart-4)', print: '#eda100', dash: '' },
  { css: 'var(--muted-foreground)', print: '#5a5a5a', dash: '5 3' },
]

/**
 * Kiểu đường của từng đường (cùng thứ tự `lines`): vai trò n lấy kiểu thứ n; vai trò lạ hoặc đã bị đường khác lấy (một sản phẩm
 * khai hai mã cùng vai trò) thì lấy kiểu còn trống đầu tiên, hết trống thì quay vòng.
 */
export function assignHistoryLineStyles(lines: readonly PackagingHistorySeriesLine[]): HistoryLineStyle[] {
  const taken = new Set<number>()
  return lines.map((line, index) => {
    const wanted = line.role - 1
    let slot = wanted >= 0 && wanted < HISTORY_LINE_STYLES.length && !taken.has(wanted) ? wanted : -1
    if (slot < 0) slot = HISTORY_LINE_STYLES.findIndex((_, i) => !taken.has(i))
    if (slot < 0) slot = index % HISTORY_LINE_STYLES.length
    taken.add(slot)
    return HISTORY_LINE_STYLES[slot]
  })
}

/** Chú giải = vai trò + mã ("Chai · CPT0105"); vai trò lạ thì chỉ mã. */
export function historyLineLegend(line: Pick<PackagingHistorySeriesLine, 'role' | 'code'>): string {
  const role = historyRoleText(line)
  return role ? `${role} · ${line.code}` : line.code
}

/** Khóa dữ liệu của đường thứ `index` trong hàng biểu đồ. */
export const historyLineKey = (index: number): string => `line${index}`

/** Một hàng của biểu đồ: nhãn ngày + giá của từng đường có lần mua ở hàng này (khóa `line{i}`). */
export type HistorySeriesRow = { label: string; date: string } & Record<string, number | string | undefined>

/**
 * Các đường → hàng dữ liệu chung, theo ngày tăng dần. Mỗi lần mua là MỘT điểm (như biểu đồ một mã): nhiều lần mua của cùng một mã
 * trong một ngày thành nhiều hàng liên tiếp cùng nhãn ngày, nên hàng của một ngày nhiều bằng số lần mua nhiều nhất của một mã
 * trong ngày đó. Đường không có lần mua ở hàng nào thì để trống ở hàng ấy (biểu đồ nối qua chỗ trống).
 */
export function buildSeriesRows(lines: readonly PackagingHistorySeriesLine[]): HistorySeriesRow[] {
  const byDate = new Map<string, Map<number, number[]>>()
  lines.forEach((line, index) => {
    for (const point of line.points) {
      const day = byDate.get(point.date) ?? new Map<number, number[]>()
      day.set(index, [...(day.get(index) ?? []), point.price])
      byDate.set(point.date, day)
    }
  })
  const rows: HistorySeriesRow[] = []
  for (const date of [...byDate.keys()].sort()) {
    const day = byDate.get(date) as Map<number, number[]>
    const depth = Math.max(...[...day.values()].map((prices) => prices.length))
    for (let j = 0; j < depth; j += 1) {
      const row: HistorySeriesRow = { label: formatDate(date), date }
      for (const [index, prices] of day) if (j < prices.length) row[historyLineKey(index)] = prices[j]
      rows.push(row)
    }
  }
  return rows
}

/** Trục giá chung cho mọi đường (không bắt đầu từ 0 — xem `priceAxisDomain`). */
export function seriesAxisDomain(lines: readonly PackagingHistorySeriesLine[]): [number, number] {
  return priceAxisDomain(lines.flatMap((line) => line.points.map((point) => point.price)))
}
