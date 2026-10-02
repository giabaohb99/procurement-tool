import { AlertTriangle } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'

interface ReportErrorCardProps {
  /** Câu lỗi backend trả (`extractErrorMessage`) — 403 thiếu quyền theo `group_by`, 422 kỳ sai… */
  message: string
  onReset: () => void
}

/**
 * Thẻ lỗi khi `/summary` gọi hỏng (M6) — trang KHÔNG được kẹt cứng: một
 * đường link chia sẻ mang `?group_by=supplier` mà người nhận không có quyền
 * NCC, hay tham số kỳ gõ tay sai, vẫn phải có lối quay lại mà không cần tự sửa
 * URL bằng tay. Thay hẳn khối KPI/biểu đồ/bảng (rỗng, dễ đọc nhầm là "chưa có
 * số liệu") khi đang lỗi — `ReportAnalyticsPage` chỉ dựng thẻ này lúc `isError`.
 */
export function ReportErrorCard({ message, onReset }: ReportErrorCardProps) {
  return (
    <Card className="flex flex-col items-start gap-3 border-destructive/30 bg-destructive/5 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" aria-hidden />
        <div>
          <p className="text-sm font-medium text-destructive">Không tải được báo cáo</p>
          <p className="mt-0.5 text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
      <Button variant="outline" size="sm" onClick={onReset} className="shrink-0">
        Đặt lại bộ lọc
      </Button>
    </Card>
  )
}
