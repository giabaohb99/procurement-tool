import type { DossierCustomRow } from '../types/dossier-custom-row'

/**
 * Câu nhắc của MỘT hàng, hoặc `undefined` khi hàng đó ổn.
 *
 * ⚠️ Mỗi ca một câu riêng — gộp thành «dữ liệu không hợp lệ» thì người dùng
 * biết có gì đó sai mà không biết sai ở đâu, mà hai ca dưới đây phải sửa ở hai
 * chỗ khác nhau.
 *
 * ⚠️ KHÔNG còn ca «trùng mã với ô của loại» (bỏ 17/09/2026): loại tụt xuống
 * thành KHUÔN được đổ vào chính bảng này, nên chỉ còn MỘT nguồn khai — không có
 * gì để mà trùng nữa.
 *
 * ⚠️ Hàng CHƯA ĐẶT TÊN thì KHÔNG báo gì: người dùng vừa bấm «Thêm trường» và
 * chưa kịp gõ. `fromCustomRows` bỏ hẳn hàng đó lúc gửi nên nó vô hại.
 */
export function problemOf(
  row: DossierCustomRow,
  index: number,
  rows: DossierCustomRow[],
): string | undefined {
  if (!row.key) return undefined

  if (rows.findIndex((r) => r.key === row.key) !== index) {
    return `«${row.key}» trùng với một trường riêng khác. Hai ô cùng mã thì chỉ một giá trị được lưu.`
  }
  //  Backend ném «Ô chọn «X» phải khai ít nhất một mục» — bắt trước ở đây thì
  //  câu nhắc nằm ngay dưới hàng, không phải một toast rời khỏi chỗ đang sai.
  if (row.type === 'select' && row.options.length === 0) {
    return `«${row.label || row.key}» là ô chọn nhưng chưa khai mục nào.`
  }
  return undefined
}

/** Câu nhắc ĐẦU TIÊN của cả danh sách — dùng để chặn submit. */
export function firstProblem(rows: DossierCustomRow[]): string | undefined {
  for (const [index, row] of rows.entries()) {
    const problem = problemOf(row, index, rows)
    if (problem) return problem
  }
  return undefined
}
