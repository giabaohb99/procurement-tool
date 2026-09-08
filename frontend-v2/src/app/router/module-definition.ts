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
   * **Còn sáng khi đang ở những đường này nữa.** Dùng cho mục menu gom nhiều màn
   * có ĐƯỜNG DẪN RIÊNG (khác `entities`, vốn dành cho nhiều khóa quyền trên cùng
   * một đường).
   *
   * Sinh ra cho cụm *Nghỉ phép* (04/09/2026): năm màn giữ nguyên năm đường cũ —
   * link trong thư báo việc duyệt trỏ thẳng `/hr/leave-requests/{id}` — nhưng
   * menu chỉ còn một mục, chuyển qua lại bằng thanh tab trong trang. Không khai
   * đây thì mở «Lịch nghỉ» xong cả menu trái tối om, không mục nào sáng.
   */
  matchPaths?: string[]
  /**
   * **Không vẽ trên menu trái**, nhưng vẫn là một mục khai báo đầy đủ.
   *
   * Vẫn tính trong `canAccessRoute` (gõ thẳng URL màn không có quyền vẫn bị chặn
   * tử tế) và trong `canOpenModule`. Dùng khi nhiều màn gom về một mục menu:
   * mục gom mang `matchPaths`, các màn con mang `hidden` để GIỮ NGUYÊN khóa
   * quyền riêng của từng màn — bỏ hẳn chúng đi thì `/hr/leave-types` không còn
   * mục nào khớp và rơi về nhánh "cho xem", tức mất chốt gác phía giao diện.
   */
  hidden?: boolean
  /**
   * **Đường dẫn phụ trỏ sang phân hệ KHÁC.** Mục vẫn nằm trong menu phân hệ này
   * nhưng `path` nằm ngoài `module.path`, bấm vào là chuyển hẳn sang phân hệ kia.
   *
   * Sinh ra cho Thu mua (31/08/2026): người mua hàng tra công nợ và lên đề nghị
   * thanh toán suốt ngày, bắt họ quay ra màn chọn phân hệ rồi vào Tài chính là
   * thừa hai cú bấm cho việc làm mỗi ngày.
   *
   * Hai chỗ CỐ Ý xử khác mục thường:
   * - `module-registry.test.ts` bỏ qua nó ở khẳng định "mục menu nằm trong đường
   *   dẫn của chính phân hệ", nhưng đổi lại bắt path phải trỏ vào một phân hệ có
   *   thật trong bảng đăng ký — gõ sai đường dẫn thì test đỏ chứ không ra 404.
   * - `canOpenModule` KHÔNG đếm nó: người chỉ có `payable.read` mà thấy thẻ Thu
   *   mua mở, vào trong rỗng tuếch thì đúng lại lỗi ngày 27/08.
   */
  crossModule?: boolean
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
   * Class Tailwind tô ô icon trên thẻ chọn phân hệ. Mỗi phân hệ một màu để nhận
   * ra bằng mắt thay vì phải đọc chữ.
   *
   * Khuôn bắt buộc: **`bg-<màu>-500/10 text-<màu>-600 dark:text-<màu>-400`**.
   *
   * ⚠️ Nền phải là màu ĐẬM PHA ALPHA (`-500/10`), KHÔNG được dùng bậc nhạt đặc
   * (`bg-rose-50`). Bậc nhạt có độ sáng 96–98% nên nó trắng ở MỌI chế độ nền —
   * bật nền tối là 20 ô icon thành 20 mảng trắng chóe trên trang tối (lỗi thấy
   * được 27/08/2026). Alpha thì lộ nền phía sau nên tự đúng ở cả hai chế độ.
   * Chữ cũng phải có biến thể `dark:` vì bậc 600 quá tối trên nền tối.
   *
   * Màu này CỐ Ý không đi theo bảng màu người dùng chọn: nó là dấu chỉ đường
   * (Nhân sự = hồng, Thu mua = xanh lơ...), suy ra từ bảng màu thì cả 20 phân hệ
   * chung một sắc và mất luôn tác dụng nhận diện.
   *
   * Có test canh khuôn này ở `module-registry.test.ts`.
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
  /**
   * Phân hệ TỰ MANG KHUNG riêng thay vì dùng `ModuleLayout` (sidebar nghiệp vụ).
   * Route của nó gắn thẳng dưới `ProtectedRoute`, và `routes.tsx` của phân hệ
   * phải tự khai layout + `errorElement` cho nhánh của mình.
   *
   * Sinh ra cho Diễn đàn (QĐ-D6): mạng nội bộ một cột kiểu bảng tin, sidebar
   * chứng từ không có nghĩa ở đó.
   */
  customLayout?: boolean
  /** Tab điều hướng bên trong module. */
  nav: ModuleNavItem[]
  /** Route con, gắn vào bên trong `AppLayout`. */
  routes: RouteObject[]
}
