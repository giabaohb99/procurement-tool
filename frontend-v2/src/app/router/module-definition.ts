import type { LucideIcon } from 'lucide-react'
import type { RouteObject } from 'react-router-dom'

import type { PermissionEntity } from '@/core/authorization/permission-types'

/** Một mục trong menu trái của module. */
export interface ModuleNavItem {
  label: string
  /** Đường dẫn tuyệt đối. */
  path: string
  icon: LucideIcon
  /** Thiếu quyền trên entity này thì ẩn mục. Bỏ trống = luôn hiện. */
  entity?: PermissionEntity
  /** Chỉ sáng khi khớp CHÍNH XÁC path (dùng cho mục Tổng quan của module). */
  end?: boolean
  /**
   * Tiêu đề nhóm trên menu trái (vd "Danh mục", "Nghiệp vụ"). Các mục cùng chuỗi
   * này gom lại dưới một tiêu đề. Bỏ trống = đứng riêng ở đầu menu, không tiêu đề.
   */
  group?: string
}

/**
 * Hợp đồng mà MỌI module ERP phải khai báo (file `modules/<ten>/routes.tsx`).
 * Thêm module = tạo thư mục + thêm 1 dòng vào `module-registry.ts`; màn chọn
 * phân hệ và thanh điều hướng tự cập nhật theo, không phải sửa gì thêm.
 */
export interface ErpModule {
  /** Định danh duy nhất, kebab-case — trùng tên thư mục. */
  id: string
  /** Nhãn tiếng Việt hiện trên thẻ và header. */
  title: string
  /** Mô tả ngắn hiện dưới tên ở màn chọn phân hệ. */
  description: string
  icon: LucideIcon
  /** Đường dẫn gốc; cũng dùng để xác định module đang mở. */
  path: string
  /**
   * Cặp class Tailwind tô màu icon trên thẻ. Mỗi phân hệ một màu để nhận ra
   * bằng mắt thay vì phải đọc chữ.
   */
  accent: string
  /**
   * Bật/tắt cả phân hệ. `false` = không hiện trên màn chọn phân hệ, không đăng ký
   * route (vào thẳng URL cũng ra 404). Dùng để giữ sẵn khung phân hệ chưa tới lượt
   * làm mà không phải xóa code — bật lại chỉ cần đổi một chữ.
   */
  enabled: boolean
  /**
   * Entity phân quyền để ẩn/hiện cả module. Người dùng không có quyền nào trên
   * entity này thì không thấy phân hệ đó. Bỏ trống = ai cũng thấy.
   */
  entity?: PermissionEntity
  /**
   * Phân hệ nằm ở APP KHÁC (vd Trung tâm Hướng dẫn sử dụng chạy riêng cổng
   * 8082): ô trên màn chọn phân hệ mở tab mới thay vì điều hướng nội bộ.
   *
   * Là HÀM chứ không phải chuỗi vì địa chỉ có thể phải kèm token bàn giao phiên,
   * mà token thì đổi theo lần đăng nhập. Module dạng này khai `path: ''`,
   * `nav: []`, `routes: []` và bị loại khỏi router.
   */
  externalUrl?: () => string
  /** Tab điều hướng bên trong module. */
  nav: ModuleNavItem[]
  /** Route con, gắn vào bên trong `AppLayout`. */
  routes: RouteObject[]
}
