/**
 * Từ điển tiếng Việt. Hệ thống hiện chỉ chạy tiếng Việt nên chưa cần i18next —
 * để sẵn cấu trúc phẳng `key: string` này, khi nào thêm ngôn ngữ thứ hai chỉ việc
 * copy file sang `en.ts` và đổi hàm `t()` trong `use-translation.ts`.
 */
export const vi = {
  'common.save': 'Lưu',
  'common.cancel': 'Hủy',
  'common.create': 'Thêm mới',
  'common.edit': 'Sửa',
  'common.delete': 'Xóa',
  'common.search': 'Tìm kiếm',
  'common.loading': 'Đang tải…',
  'common.empty': 'Chưa có dữ liệu',
  'common.error': 'Có lỗi xảy ra, vui lòng thử lại',
  'common.confirm': 'Xác nhận',

  'auth.login': 'Đăng nhập',
  'auth.logout': 'Đăng xuất',
  'auth.username': 'Mã nhân viên / Email',
  'auth.password': 'Mật khẩu',
  'auth.loginFailed': 'Đăng nhập thất bại',
  'auth.sessionExpired': 'Phiên làm việc đã hết hạn, vui lòng đăng nhập lại',
  'auth.noPermission': 'Bạn không có quyền truy cập chức năng này',

  'nav.dashboard': 'Tổng quan',
  'nav.sales': 'Bán hàng',
  'nav.inventory': 'Kho',
  'nav.procurement': 'Mua hàng',
  'nav.finance': 'Tài chính',
  'nav.hr': 'Nhân sự',
} as const

export type TranslationKey = keyof typeof vi
