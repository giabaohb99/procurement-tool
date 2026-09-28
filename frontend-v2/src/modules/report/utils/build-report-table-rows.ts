import type { ReportGroupRow, ReportMetricValues } from '../types/report-analytics'

/** Khóa của hàng TỔNG giả — `DataTable` không có dòng chân riêng (xem `ReportGroupedTable`). */
export const REPORT_TOTAL_ROW_KEY = '__total__'

export interface ReportTableRow {
  key: string
  label: string
  current: ReportMetricValues
  compare: ReportMetricValues | null
  isTotal: boolean
  /**
   * Mọi chỉ số kỳ NÀY đều 0/`null` — dòng chỉ còn xuất hiện vì kỳ SO SÁNH có dữ
   * liệu (backend gộp cả hai kỳ khi liệt kê nhóm). Hiện mờ và xếp SAU các dòng
   * còn hoạt động, xem `partitionByActivity` bên dưới. Dòng Tổng không bao giờ
   * mang cờ này dù `totals.current` toàn 0 — khi đó cả bảng đã đổi sang màn hình
   * "Kỳ này chưa có dữ liệu" (`ReportGroupedTable`), không phải một dòng mờ.
   */
  isEmpty: boolean
}

/** Mọi giá trị trong `values` đều `null` hoặc `0` — coi là "không có phát sinh". */
export function isMetricValuesEmpty(values: ReportMetricValues): boolean {
  return Object.values(values).every((v) => v === null || v === 0)
}

/**
 * Dựng dòng cho bảng "Xem theo" của trang báo cáo: hàng TỔNG (tính độc lập ở
 * backend, KHÔNG cộng các nhóm — dimension nhiều-giá-trị như PIC/loại nghỉ thì
 * tổng ≠ tổng các nhóm) luôn đứng ĐẦU, sau đó là các nhóm ĐANG HOẠT ĐỘNG, cuối
 * cùng mới tới các nhóm RỖNG kỳ này (`isMetricValuesEmpty`).
 *
 * `DataTable` chỉ vẽ đúng thứ tự mảng truyền vào (xem `docs/ui/table.md`) —
 * không tự sắp lại — nên sắp xếp theo cột phải làm Ở ĐÂY, phía client: dữ liệu
 * nhóm của một báo cáo tối đa vài trăm dòng, không phân trang, gọi lại API chỉ
 * để đổi hướng sắp là phí một lượt gọi.
 *
 * `sortBy = null` giữ nguyên thứ tự backend trả (đã sắp theo chỉ số đầu giảm
 * dần — phase-01 `report_aggregate.aggregate`) TRONG TỪNG nhóm hoạt động/rỗng.
 */
export function buildReportTableRows(
  totals: { current: ReportMetricValues; compare: ReportMetricValues | null },
  groups: ReportGroupRow[],
  sortBy: string | null,
  sortDir: 'asc' | 'desc' = 'desc',
): ReportTableRow[] {
  const totalRow: ReportTableRow = {
    key: REPORT_TOTAL_ROW_KEY,
    label: 'Tổng',
    current: totals.current,
    compare: totals.compare,
    isTotal: true,
    isEmpty: false,
  }

  const rows: ReportTableRow[] = groups.map((g) => ({
    key: g.key,
    label: g.label,
    current: g.current,
    compare: g.compare,
    isTotal: false,
    isEmpty: isMetricValuesEmpty(g.current),
  }))

  function sortRows(list: ReportTableRow[]): ReportTableRow[] {
    if (!sortBy) return list
    const dir = sortDir === 'asc' ? 1 : -1
    return [...list].sort((a, b) => dir * ((a.current[sortBy] ?? 0) - (b.current[sortBy] ?? 0)))
  }

  const active = sortRows(rows.filter((r) => !r.isEmpty))
  const inactive = sortRows(rows.filter((r) => r.isEmpty))

  return [totalRow, ...active, ...inactive]
}
