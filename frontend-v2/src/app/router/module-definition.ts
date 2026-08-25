import type { LucideIcon } from 'lucide-react'
import type { ComponentType } from 'react'
import type { RouteObject } from 'react-router-dom'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'

/** Một mục trong menu trái của module. */
export interface ModuleNavItem {
  label: string
  /** Đường dẫn tuyệt đối. */
  path: string
  icon: LucideIcon
  /** Thiếu quyền trên entity này thì ẩn mục. Bỏ trống = luôn hiện. */
  entity?: PermissionEntity
  /**
   * Mục gom NHIỀU màn con dùng khóa khác nhau — hiện khi có quyền trên **bất kỳ**
   * khóa nào trong đây, rồi để chính trang tự ẩn phần không được xem.
   *
   * Sinh ra cho «Thiết lập văn bản»: một mục menu chứa bốn tab chạy trên bốn
   * khóa (`doc_type` · `doc_template` · `security_level` · `external_party`).
   * Gác bằng một khóa duy nhất thì người chỉ giữ *Đơn vị gửi nhận* không vào nổi
   * trang chứa đúng tab của mình, còn người có khóa gác mà thiếu khóa của tab
   * thì vào được rồi bấm tab ăn 403 (CR-157).
   *
   * Khai cùng `entity` thì `entity` được xét trước.
   */
  entities?: PermissionEntity[]
  /** Kiểm tra đúng hành động này trên entity (`read`, `create`, `write`, ...). */
  action?: PermissionAction
  /** Mục quản lý (danh mục, hệ thống): yêu cầu quyền quản lý (`write` | `create` | `delete`). */
  manage?: boolean
  /** Chỉ sáng khi khớp CHÍNH XÁC path (dùng cho mục Tổng quan của module). */
  end?: boolean
  /**
   * Tiêu đề nhóm trên menu trái (vd "Danh mục", "Nghiệp vụ"). Các mục cùng chuỗi
   * này gom lại dưới một tiêu đề. Bỏ trống = đứng riêng ở đầu menu, không tiêu đề.
   */
  group?: string
  /**
   * Huy hiệu nhỏ ở cuối dòng menu — dùng cho những mục có **số việc đang chờ**
   * (vd "Chờ tôi duyệt"). Là một COMPONENT chứ không phải con số, vì con số phải
   * hỏi máy chủ mà `routes.tsx` chỉ là bảng khai báo tĩnh: component tự gọi hook
   * của phân hệ mình và tự ẩn khi không có việc nào.
   *
   * Đừng dùng nó cho nhãn tĩnh kiểu "Mới" — menu đầy huy hiệu thì cái nào cũng
   * hết nổi bật, mà mục đích của nó đúng là để nổi bật.
   */
  badge?: ComponentType
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
