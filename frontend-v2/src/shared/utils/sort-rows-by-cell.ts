import { byIdDescending, sortRowsBy, type SortDir, type SortValue } from './compare-sort-values'

/**
 * Sắp xếp phía trình duyệt cho bảng TẢI TRỌN một lần theo cột người dùng bấm (duoc-CR-744).
 *
 * Dùng cho các hàng đợi mà endpoint trả hết, không phân trang và không nhận `sort_by`: *Cần tôi duyệt* /
 * *Tôi đã duyệt* của Đơn nghỉ phép · Đặt phòng · Phiếu nghỉ bù · Thanh toán nghỉ phép, tab Văn bản đến.
 * Xếp TRƯỚC khi cắt trang nên đúng trên cả tập. Phạm vi phân trang phía máy chủ KHÔNG đi qua đây - nó gửi
 * `sort_by` lên máy chủ, xếp lại một trang ở trình duyệt là xếp sai (đơn ở trang 2 không bao giờ nổi lên).
 *
 * Luật so sánh nằm ở `compare-sort-values.ts` (ô trống xuống cuối ở cả hai chiều, số 0 là giá trị thật);
 * trùng giá trị thì `id` giảm dần để thứ tự không đổi giữa các lần dựng.
 *
 * Mỗi khóa xếp theo ĐÚNG giá trị ô đang hiện do nơi gọi khai trong `getters`.
 */
export type CellGetters<T> = Record<string, (row: T) => SortValue>

/**
 * Trả BẢN SAO đã xếp. Khóa rỗng hoặc không có trong `getters` thì giữ nguyên thứ tự gốc
 * (nhịp thứ ba của tiêu đề cột = thôi sắp xếp).
 */
export function sortRowsByCell<T extends { id: number }>(
  rows: readonly T[],
  sortBy: string,
  sortDir: SortDir,
  getters: CellGetters<T>,
): T[] {
  const getCell = sortBy ? getters[sortBy] : undefined
  if (!getCell) return [...rows]
  return sortRowsBy(rows, getCell, sortDir, byIdDescending)
}
