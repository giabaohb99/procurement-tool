import type { DataTableColumn } from '@/shared/data-table'

/**
 * Sắp xếp bảng *Kết quả khảo sát đã duyệt* ở hai màn xử lý (YCBG và YCMH) — duoc-CR-738.
 *
 * Bản v1 bấm tiêu đề cột là sắp phía server (`SurveyRequestProcess.tsx`); v2 thiếu nên NSTM
 * không xếp được theo giá / ngày khảo sát. Hai màn gọi chung một hàm backend
 * `available_survey_lines` nên bảng khóa dưới đây dùng chung, khai MỘT chỗ.
 */

export type AvailableSurveyLineSortDir = 'asc' | 'desc'

export interface AvailableSurveyLineSort {
  /** Khóa sắp xếp backend; rỗng = chưa chọn cột, backend xếp mới nhất trước. */
  sortBy: string
  sortDir: AvailableSurveyLineSortDir
}

export const NO_AVAILABLE_SURVEY_LINE_SORT: AvailableSurveyLineSort = { sortBy: '', sortDir: 'desc' }

/**
 * Khóa cột v2 → khóa `sort_by` backend. CHỈ gồm cột có trong `sort_cols` của
 * `backend/app/modules/survey_request/line_service.py::available_survey_lines`; khóa lạ
 * backend lặng lẽ bỏ qua và xếp theo `id` giảm dần, nên cột không có ở đây (Phân loại KS,
 * Phiếu KS, nút gắn) KHÔNG được bật sắp xếp — bật lên là mũi tên đổi mà thứ tự đứng im.
 * Cột NCC hiện TÊN (thiếu tên thì mã) nên sắp theo đúng chữ đó (`supplier_name`, duoc-CR-744) -
 * khác bản v1 từng sắp theo mã.
 */
export const AVAILABLE_SURVEY_LINE_SORT_KEYS: Readonly<Record<string, string>> = {
  supplier: 'supplier_name',
  product: 'product_name',
  price: 'price_by_volume',
  moq: 'moq',
  unit: 'quote_unit',
  result_date: 'result_date',
}

/** Cột thời gian: bấm lần đầu là muốn xem khảo sát MỚI nhất trước. */
const DESC_FIRST_KEYS = new Set(['result_date'])

/** Bật sắp xếp cho cột có khóa backend; cột khác giữ nguyên. */
export function withAvailableSurveyLineSort<T>(columns: DataTableColumn<T>[]): DataTableColumn<T>[] {
  return columns.map((column) => {
    const sortKey = AVAILABLE_SURVEY_LINE_SORT_KEYS[column.key]
    if (!sortKey) return column
    return {
      ...column,
      sortable: true,
      sortKey,
      ...(DESC_FIRST_KEYS.has(column.key) ? { sortDescFirst: true } : {}),
    }
  })
}

/**
 * Tham số gửi API. Chưa chọn cột thì KHÔNG gửi `sort_by` / `sort_dir` — để backend xếp mặc
 * định (mới nhất trước) và khóa truy vấn khớp đúng lượt gọi trước khi có sắp xếp.
 */
export function toAvailableSurveyLineSortParams(
  sort: AvailableSurveyLineSort,
): { sort_by?: string; sort_dir?: AvailableSurveyLineSortDir } {
  if (!sort.sortBy) return {}
  return { sort_by: sort.sortBy, sort_dir: sort.sortDir }
}
