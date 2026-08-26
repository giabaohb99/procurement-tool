import { Boxes, Factory, ShoppingCart, Users, type LucideIcon } from 'lucide-react'

/**
 * Phân hệ chứa các BẢNG dữ liệu có thể Nhập/Xuất — dùng chung cho hộp thoại Nhập
 * và Xuất (chọn phân hệ trước, rồi chọn bảng trong phân hệ đó) và cột "Phân hệ"
 * trên các bảng nhật ký.
 *
 * `id` khớp `moduleId` (import) / trường `module` từ backend (export). `accent` là
 * cặp lớp nền + chữ, LẤY ĐÚNG màu thẻ phân hệ ở Trang chủ (`modules/<m>/routes.tsx`).
 */
export interface DataModule {
  id: string
  label: string
  icon: LucideIcon
  /** Màu thẻ ở Trang chủ, vd 'bg-rose-50 text-rose-600'. */
  accent: string
}

export const DATA_MODULES: DataModule[] = [
  { id: 'hr', label: 'Nhân sự', icon: Users, accent: 'bg-rose-50 text-rose-600 dark:bg-rose-950/40' },
  { id: 'procurement', label: 'Thu mua', icon: ShoppingCart, accent: 'bg-sky-50 text-sky-600 dark:bg-sky-950/40' },
  { id: 'production', label: 'Sản xuất', icon: Factory, accent: 'bg-teal-50 text-teal-600 dark:bg-teal-950/40' },
  { id: 'inventory', label: 'Kho', icon: Boxes, accent: 'bg-amber-50 text-amber-600 dark:bg-amber-950/40' },
]

export function getDataModule(id: string): DataModule | undefined {
  return DATA_MODULES.find((m) => m.id === id)
}
