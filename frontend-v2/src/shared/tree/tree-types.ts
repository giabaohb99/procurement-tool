/**
 * Kiểu DÙNG CHUNG của cây chọn (`TreeView`) — thư mục văn bản (phase 05) và cây
 * tệp theo phiên bản (phase 09, `document-file-tree.tsx`) đều dựng trên type
 * này, đừng khai lại shape riêng ở từng nơi dùng.
 *
 * `T` là dữ liệu GỐC của nơi gọi (bản ghi thư mục, tệp đính kèm…) — `TreeView`
 * không đọc vào bên trong nó, chỉ truyền lại nguyên vẹn cho `renderIcon` /
 * `renderBadge` / `renderTrailing` của nơi dùng.
 */
export interface TreeNode<T = unknown> {
  id: string | number
  label: string
  children?: TreeNode<T>[]
  /** Dữ liệu gốc của node — nơi dùng tự đọc thêm field riêng qua đây. */
  data?: T
  /**
   * ÉP hiện chevron mở/đóng dù `children` đang rỗng/`undefined` — dùng cho
   * node kiểu "thư mục" biết chắc CÓ THỂ có con (thư mục con hoặc lá lười tải
   * sau, ví dụ văn bản trong thư mục văn bản) nhưng chưa nạp/chưa có gì lúc
   * dựng cây. Bỏ trống = hành vi cũ (chevron chỉ hiện khi `children` thật sự
   * có phần tử).
   */
  expandable?: boolean
}

/** Một dòng ĐÃ TRẢI PHẲNG — dùng cho vẽ bảng ảo/điều hướng bàn phím tuần tự. */
export interface FlatTreeNode<T = unknown> {
  id: string | number
  label: string
  /** 0 = gốc. */
  depth: number
  parentId: string | number | null
  hasChildren: boolean
  data?: T
}
