import { Lock } from 'lucide-react'

/**
 * Dải cảnh báo khi người xem KHÔNG được xem tiền của kế hoạch nhân sự — cùng khuôn với
 * `SensitiveFieldsNotice` của hồ sơ. Bắt buộc nói ra: cột tiền bị gỡ, nhìn vào thì tưởng kế hoạch
 * chưa ai lập chi phí.
 */
export function PayrollHiddenNotice() {
  return (
    <div className="flex items-start gap-2 rounded-md border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground">
      <Lock className="mt-0.5 size-4 shrink-0" />
      <span>
        Số tiền của kế hoạch đang ẩn với bạn: chỉ người đọc được hợp đồng lao động của pháp nhân này mới
        thấy lương, chi phí khác và bảng Tổng. Bạn vẫn xem và sửa được <strong>số người cần có</strong> và
        căn cứ; bấm Lưu <strong>không làm mất</strong> số tiền người khác đã nhập.
      </span>
    </div>
  )
}
