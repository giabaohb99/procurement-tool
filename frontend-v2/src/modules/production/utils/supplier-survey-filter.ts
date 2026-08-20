/** Giá trị "không lọc" của ô chọn trạng thái — Radix Select cấm `value=""`. */
export const SURVEY_APPROVE_ALL = '__all__'

/**
 * Lọc dòng khảo sát ở phía giao diện.
 *
 * `/api/survey-report/by-supplier` trả một cục không phân trang, không nhận tham
 * số lọc — nên lọc nằm ở đây.
 *
 * Từ khóa dò TỪNG Ô rồi mới `some`, KHÔNG nối các ô thành một chuỗi: nối lại thì
 * gõ "ABC 0123" sẽ khớp nhầm phần đuôi ô này với phần đầu ô kế bên, ra kết quả
 * không giải thích được cho người dùng.
 *
 * Không bỏ dấu tiếng Việt — giữ đúng cách so khớp của bản đang chạy thật, để
 * người quen tay không thấy kết quả đổi khác sau khi đổi màn.
 */
export function filterSurveyLines<T extends { line_approve: string }>(
  rows: T[],
  keyword: string,
  approve: string,
  searchable: (row: T) => Array<string | number | null | undefined>,
): T[] {
  const query = keyword.trim().toLowerCase()

  return rows.filter((row) => {
    if (approve !== SURVEY_APPROVE_ALL && row.line_approve !== approve) return false
    if (!query) return true
    return searchable(row).some((value) =>
      String(value ?? '')
        .toLowerCase()
        .includes(query),
    )
  })
}
