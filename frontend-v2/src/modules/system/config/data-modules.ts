import { Boxes, Car, Factory, ShoppingCart, Stamp, Users, type LucideIcon } from 'lucide-react'

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
  /**
   * Màu thẻ ở Trang chủ, vd 'border-rose-500 bg-rose-50 text-rose-600'. Gồm cả màu
   * viền: ô bấm chọn phân hệ (ModuleTablePicker) thêm `border-2` để hiện viền; thẻ
   * Phân hệ (ModuleBadge) không đặt bề rộng viền nên lớp `border-*` ở đây vô hại.
   */
  accent: string
}

export const DATA_MODULES: DataModule[] = [
  { id: 'hr', label: 'Nhân sự', icon: Users, accent: 'border-rose-500 bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400' },
  { id: 'procurement', label: 'Thu mua', icon: ShoppingCart, accent: 'border-sky-500 bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-400' },
  { id: 'production', label: 'Sản xuất', icon: Factory, accent: 'border-teal-500 bg-teal-50 text-teal-600 dark:bg-teal-950/40 dark:text-teal-400' },
  { id: 'inventory', label: 'Kho', icon: Boxes, accent: 'border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400' },
  { id: 'vehicle-booking', label: 'Đặt xe', icon: Car, accent: 'border-orange-500 bg-orange-50 text-orange-600 dark:bg-orange-950/40 dark:text-orange-400' },
  { id: 'seal', label: 'Duyệt dấu', icon: Stamp, accent: 'border-rose-500 bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400' },
]

export function getDataModule(id: string): DataModule | undefined {
  return DATA_MODULES.find((m) => m.id === id)
}
