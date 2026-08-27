import { ThemePresetPicker } from '@/shared/theme/theme-preset-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

/**
 * GIAO DIỆN — người dùng tự chọn bảng màu cho tài khoản mình.
 *
 * Lựa chọn lưu ở máy chủ theo tài khoản (`tab_user_preference`), nên đăng nhập
 * ở máy khác hay trình duyệt khác vẫn thấy đúng bảng màu đã chọn. Không ảnh
 * hưởng ai khác — đây không phải cấu hình toàn hệ.
 *
 * ⚠️ Màn này CỐ Ý không có công tắc Sáng·Tối·Theo hệ thống. Nó đã nằm sẵn trong
 * popover ảnh đại diện, ở đây chỉ là bản sao thứ hai của cùng một thiết lập —
 * mà `ThemeSwitch` lại là bản thu nhỏ cho popover nên bày ra thẻ rộng thì giãn
 * thành một thanh rỗng, xấu (gỡ ngày 27/08/2026 theo yêu cầu).
 *
 * Không bọc trong `Card`: cả trang chỉ làm đúng một việc, thêm một lớp khung
 * viền quanh lưới thẻ chỉ tổ đóng khung trong khung.
 */
export function AppearancePage() {
  return (
    <PageContainer>
      <PageHeader
        title="Giao diện"
        description="Chọn bảng màu cho riêng tài khoản của bạn. Bấm là đổi ngay, không cần lưu; lựa chọn theo tài khoản nên đăng nhập ở máy khác vẫn giữ nguyên."
      />

      <ThemePresetPicker />
    </PageContainer>
  )
}
