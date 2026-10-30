import { ChangePasswordDialog } from '@/app/components/profile/change-password-dialog'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'

/**
 * Mục "Đổi mật khẩu" trong nhóm Bảo mật & hiển thị (P0 doc 21 §6.5). Dùng lại đúng hộp thoại của nút trong thẻ
 * Tài khoản ở mục Thông tin cá nhân — nút cũ giữ nguyên, người quen chỗ cũ vẫn tìm thấy.
 */
export function ProfilePasswordCard() {
  return (
    <Card>
      <CardHeader>
        <SectionHeading>Mật khẩu đăng nhập ERP</SectionHeading>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-muted-foreground">
          Đổi mật khẩu khi nghi người khác biết, hoặc định kỳ cho an toàn. Đổi xong bạn không bị đăng xuất; các máy
          đang đăng nhập xem ở mục Thiết bị của tôi.
        </p>
        <ChangePasswordDialog />
      </CardContent>
    </Card>
  )
}
