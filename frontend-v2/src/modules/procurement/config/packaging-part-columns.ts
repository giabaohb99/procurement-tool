/**
 * duoc-CR-784 — năm cột thành phần của định mức bao bì, nối số vai trò (`PackagingRole` backend) với cột
 * mã của bảng `tab_packaging_bom`. Tên hiển thị lấy từ bộ mã sinh TS (`packagingRoleLabel`), không gõ ở đây.
 * `perCarton` = giá tính cho cả thùng, chia quy cách thùng khi cộng vào chi phí /chai. `sortKey` = khóa `sort_by` máy chủ
 * nhận cho cột đó (xếp theo giá đang áp của thành phần) — khớp `PART_SORT_ROLES` của `impact_service.py`.
 */
export const PACKAGING_PART_COLUMNS = [
  { role: 1, sortKey: 'part_bottle', field: 'bottle_code', perCarton: false },
  { role: 2, sortKey: 'part_cap', field: 'cap_code', perCarton: false },
  { role: 3, sortKey: 'part_label', field: 'label_code', perCarton: false },
  { role: 4, sortKey: 'part_carton_label', field: 'carton_label_code', perCarton: true },
  { role: 5, sortKey: 'part_carton', field: 'carton_code', perCarton: true },
] as const
