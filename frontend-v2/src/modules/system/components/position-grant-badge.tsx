import { Badge } from '@/shared/ui/badge'

/**
 * Huy hiệu «Theo chức vụ: <tên>» (duoc-CR-653) — đánh dấu vai trò do HỆ THỐNG tự cấp theo chức vụ,
 * để quản trị biết dòng này sẽ đổi theo chức vụ chứ không phải do ai gán tay.
 */
export function PositionGrantBadge({ positionName }: { positionName: string }) {
  return (
    <Badge variant="secondary" className="shrink-0 whitespace-nowrap" title="Hệ thống tự cấp theo chức vụ. Muốn bỏ riêng cho người này: sửa gói hoặc đổi chức vụ của họ.">
      Theo chức vụ: {positionName}
    </Badge>
  )
}
