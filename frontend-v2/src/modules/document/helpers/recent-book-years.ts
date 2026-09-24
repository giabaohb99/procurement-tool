/**
 * Bốn năm gần nhất — đủ để tra sổ cũ mà không phải gõ tay.
 *
 * Dùng chung cho MỌI ô chọn năm của một sổ văn bản: `BookCounterCard` (tab
 * «Thông tin sổ») và `BookDocumentsTab` (tab «Văn bản trong sổ», duoc-CR-474) phải
 * liệt kê y hệt nhau — hai tab của CÙNG một sổ mà hai danh sách năm khác nhau
 * thì người dùng chọn "Năm 2023" ở tab này mà tab kia không có lựa chọn đó.
 *
 * Tách thành tệp riêng (không export thẳng từ `book-counter-card.tsx`) để
 * tránh cảnh báo `react-refresh/only-export-components` — file component chỉ
 * nên xuất component.
 */
export function recentBookYears(): number[] {
  const now = new Date().getFullYear()
  return [now, now - 1, now - 2, now - 3]
}
