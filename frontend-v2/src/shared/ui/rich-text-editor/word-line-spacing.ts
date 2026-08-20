/**
 * GIÃN DÒNG: số trên thanh công cụ CHÍNH LÀ `line-height` của CSS.
 *
 * ⚠️ Trước 20/08/2026 chỗ này nhân thêm 1,15 để "nhìn giống Word": Word đo một
 * dòng đơn theo số đo của bộ phông (Times New Roman = 1,15 × cỡ chữ), còn CSS đo
 * theo cỡ chữ, nên "1,5 dòng" của Word tương đương `line-height: 1.725`.
 *
 * Về lý thuyết thì đúng, nhưng dùng thì hỏng, và người dùng bắt được:
 *
 * - Trang giấy (`.doc-page`) để sẵn `line-height: 1.15`. Đoạn chưa đặt gì thì ăn
 *   theo số đó. Bấm nấc **1,0** ghi ra đúng `1.15` — **không đổi một pixel nào**,
 *   nhìn như tính năng chết. Trên văn bản 217 có 136 đoạn thì 110 đoạn rơi vào
 *   đúng ca này.
 * - Số ghi xuống dữ liệu thành số lẻ vô nghĩa (`1.3225`, `1.725`), ai mở HTML ra
 *   xem cũng tưởng hỏng.
 *
 * Chốt với người dùng 20/08/2026: **giãn dòng 1 là 1**. Đổi lại thì bản nhập từ
 * Word hiển thị chật hơn bản gốc chừng 15% — chấp nhận, vì đoán ý người bấm
 * quan trọng hơn khớp từng pixel với Word.
 *
 * Bỏ ở đây thì phải bỏ **cả hai đầu** cho khớp: `docx_html.py` (nhập) và
 * `html_docx.py` (xuất) bên backend cũng đã gỡ hệ số này.
 */

/** Giãn dòng của trang giấy khi đoạn không đặt riêng — khai ở `.doc-page`. */
export const DEFAULT_LINE_SPACING = 1.15

/** Số trên thanh công cụ = `line-height` CSS, không quy đổi. */
export function wordLineSpacingToCss(lines: number): string {
  //  Vẫn làm tròn: ô "Tùy chỉnh" nhận số thực nên vẫn có đuôi dấu phẩy động.
  return String(Number(lines.toFixed(4)))
}

/**
 * Đọc ngược `line-height` của đoạn đang đứng ra số dòng kiểu Word.
 *
 * `null` khi đoạn không đặt giãn dòng riêng, hoặc khi giá trị là chiều cao tuyệt
 * đối (`18px` — Word gọi là "Exactly", tệp .docx nhập vào có thể mang theo):
 * không quy ra "mấy dòng" được nên thanh công cụ không tick nấc nào cả.
 */
export function cssToWordLineSpacing(value: string | null | undefined): number | null {
  if (!value) return null
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return null
  return Number(parsed.toFixed(2))
}

/**
 * Đọc số người dùng gõ ở ô "Tùy chỉnh".
 *
 * Nhận cả dấu phẩy thập phân ("1,3") vì đó là cách gõ số của tiếng Việt.
 * `null` = gõ sai hoặc ngoài khoảng cho phép.
 */
export function parseLineSpacingInput(raw: string): number | null {
  const value = Number(raw.trim().replace(',', '.'))
  if (!Number.isFinite(value)) return null
  if (value < MIN_LINE_SPACING || value > MAX_LINE_SPACING) return null
  return value
}

/** Khoảng cho phép của ô tùy chỉnh — bằng Word: hẹp nhất 0,5 dòng, rộng nhất 10. */
export const MIN_LINE_SPACING = 0.5
export const MAX_LINE_SPACING = 10
