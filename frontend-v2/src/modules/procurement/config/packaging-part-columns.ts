/**
 * duoc-CR-784 — năm cột thành phần của định mức bao bì, nối số vai trò (`PackagingRole` backend) với cột
 * mã của bảng `tab_packaging_bom`. Tên hiển thị lấy từ bộ mã sinh TS (`packagingRoleLabel`), không gõ ở đây.
 * `perCarton` = giá tính cho cả thùng, chia quy cách thùng khi cộng vào chi phí /chai.
 */
export const PACKAGING_PART_COLUMNS = [
  { role: 1, field: 'bottle_code', perCarton: false },
  { role: 2, field: 'cap_code', perCarton: false },
  { role: 3, field: 'label_code', perCarton: false },
  { role: 4, field: 'carton_label_code', perCarton: true },
  { role: 5, field: 'carton_code', perCarton: true },
] as const
