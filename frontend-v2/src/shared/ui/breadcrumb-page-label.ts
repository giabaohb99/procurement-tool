import { createContext, useContext, type ReactNode } from 'react'

/**
 * Chữ cấp cuối của breadcrumb khi cấp đó là "trang đang đứng" — khung phân hệ (`ModuleLayout`) cấp, `null` ở ngoài
 * phân hệ hoặc ở trang chi tiết. Đặt ở `shared/` để `PageHeader` đọc được mà không phải với lên `app/`.
 */
export const BreadcrumbPageLabelContext = createContext<string | null>(null)

/**
 * Tiêu đề trang có lặp đúng chữ cuối của breadcrumb không (duoc-CR-714, anh Được: "nếu trùng thì bỏ cái dưới đi").
 * So chữ đã bỏ khoảng trắng hai đầu, không phân biệt hoa thường; tiêu đề là JSX (kèm huy hiệu…) thì không so.
 */
export function useIsBreadcrumbDuplicate(title: ReactNode): boolean {
  const label = useContext(BreadcrumbPageLabelContext)
  if (!label || typeof title !== 'string') return false
  return title.trim().toLocaleLowerCase('vi') === label.trim().toLocaleLowerCase('vi')
}
