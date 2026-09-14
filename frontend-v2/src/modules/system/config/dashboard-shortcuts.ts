import {
  AtSign,
  Database,
  FileDown,
  FileUp,
  History,
  MailCheck,
  MonitorSmartphone,
  ShieldCheck,
  SlidersHorizontal,
  type LucideIcon,
} from 'lucide-react'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

export interface SystemShortcut {
  label: string
  description: string
  path: string
  icon: LucideIcon
  /** Khóa quyền của màn — cùng khóa mà mục menu trái đang dùng. */
  entity: PermissionEntity
  /**
   * Đòi quyền SỬA (`create|write|delete`) thay vì `read`. Phải khai y hệt mục
   * menu tương ứng trong `system/routes.tsx` — lệch một cái là thẻ hiện ra rồi
   * bấm vào ăn 403, hoặc ngược lại: màn vào được mà trang Tổng quan giấu mất.
   */
  manage?: boolean
}

/**
 * Lối tắt trên trang Tổng quan phân hệ Quản trị.
 *
 * ⚠️ **Phải phủ ĐỦ mục menu trái.** Tới 14/09/2026 danh sách này bỏ sót ba màn
 * đã có trong menu — *Hộp thư gửi*, *Phiên đăng nhập*, *Xuất dữ liệu* — nên trang
 * Tổng quan nói rằng phân hệ có 5 việc trong khi nó có 8. Lỗi im lặng: thêm màn
 * mới thì ai cũng nhớ khai `nav`, không ai nhớ khai lối tắt. Nay có
 * `dashboard-shortcuts.test.ts` so hai danh sách, thiếu là test đỏ.
 *
 * ⚠️ **Thứ tự khai bám theo `nav`** để hai chỗ đọc ra cùng một mạch, và để 8 thẻ
 * lấp kín hai hàng bốn cột — 5 thẻ như cũ là để lẻ một thẻ trơ trọi ở hàng hai,
 * đúng thứ `ModuleDashboard` đã ghi chú là muốn tránh.
 *
 * Tách khỏi `system-dashboard-page.tsx` để test import được mà không kéo theo cả
 * trang, và để không dính `react-refresh/only-export-components`.
 */
export const SYSTEM_DASHBOARD_SHORTCUTS: SystemShortcut[] = [
  {
    label: 'Cấu hình hệ thống',
    description: 'Quy trình duyệt, email gửi đi, kho lưu trữ tệp.',
    path: appRoutes.system.settings,
    icon: SlidersHorizontal,
    entity: 'setting',
    manage: true,
  },
  {
    //  duoc-CR-397: tách khỏi Cấu hình hệ thống thành trang riêng.
    label: 'Mẫu email thông báo',
    description: 'Bật/tắt và sửa nội dung email thông báo cho từng bước.',
    path: appRoutes.system.emailTemplates,
    icon: MailCheck,
    entity: 'setting',
    manage: true,
  },
  {
    label: 'Sao lưu CSDL',
    description: 'Quản lý, tạo mới và tải bản sao lưu dữ liệu hệ thống.',
    path: appRoutes.system.backups,
    icon: Database,
    entity: 'backup',
    manage: true,
  },
  {
    label: 'Hộp thư gửi',
    description: 'Địa chỉ gửi danh nghĩa dùng lúc ban hành văn bản.',
    path: appRoutes.system.mailboxes,
    icon: AtSign,
    entity: 'mailbox',
    manage: true,
  },
  {
    label: 'Nhật ký hệ thống',
    description: 'Lịch sử ghi nhận toàn bộ thao tác (thêm, sửa, xóa, duyệt...) của người dùng.',
    path: appRoutes.system.auditLogs,
    icon: History,
    entity: 'setting',
    manage: true,
  },
  {
    label: 'Phiên đăng nhập',
    description: 'Phiên đang mở toàn hệ — đá phiên hoặc bắt đăng nhập lại.',
    path: appRoutes.system.sessions,
    icon: MonitorSmartphone,
    entity: 'login_session',
    manage: true,
  },
  {
    //  duoc-CR-396: màn này nay THUỘC phân hệ Quản trị, không còn là lối tắt
    //  mượn từ Nhân sự nữa — xem ghi chú ở `appRoutes.system.permissions`.
    label: 'Phân quyền tài khoản',
    description: 'Vai trò, ma trận chức năng và phạm vi dữ liệu của từng tài khoản.',
    path: appRoutes.system.permissions,
    icon: ShieldCheck,
    entity: 'role',
    manage: true,
  },
  {
    label: 'Nhập dữ liệu',
    description: 'Nạp dữ liệu hàng loạt từ tệp Excel, chạy thử, theo dõi kết quả và hoàn tác.',
    path: appRoutes.system.imports,
    icon: FileUp,
    entity: 'import',
  },
  {
    label: 'Xuất dữ liệu',
    description: 'Nhật ký các lần xuất dữ liệu ra tệp.',
    path: appRoutes.system.exports,
    icon: FileDown,
    entity: 'setting',
  },
]
