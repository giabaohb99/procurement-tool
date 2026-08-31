import { AlertTriangle, CircleCheck, Clock, FileText, Truck } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { DashboardAlert } from '../api/procurement-dashboard-api'

/** Icon theo loại việc, để quét bằng mắt nhanh hơn đọc chữ. */
const TYPE_ICON: Record<string, typeof AlertTriangle> = {
  delivery: Truck,
  approval: FileText,
  payable: AlertTriangle,
  contract: Clock,
}

/** `danger` = đã trễ/quá hạn, còn lại là sắp tới hạn. */
function toneClass(level: string): string {
  return level === 'danger' ? 'text-destructive' : 'text-warning'
}

/**
 * Danh sách "Việc cần xử lý" — cảnh báo do backend gom sẵn (giao trễ, chờ
 * duyệt, công nợ quá hạn…).
 *
 * Chưa gắn link vì `alert.link` là đường dẫn của bản `frontend` cũ
 * (`/purchase-orders/123`); màn chi tiết ĐMH bên này chưa có nên bấm vào sẽ ra
 * trang trắng — sẽ nối khi màn chi tiết xong.
 */
export function ProcurementAlertList({ alerts }: { alerts: DashboardAlert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <span className="grid size-10 place-items-center rounded-full bg-success/10">
          <CircleCheck className="size-5 text-success" />
        </span>
        <p className="text-sm text-muted-foreground">Không có việc nào cần xử lý.</p>
      </div>
    )
  }

  return (
    <ul className="divide-y">
      {alerts.map((alert, index) => {
        const Icon = TYPE_ICON[alert.type] ?? AlertTriangle
        return (
          <li key={`${alert.type}-${index}`} className="flex gap-3 py-2.5 first:pt-0">
            <Icon className={cn('mt-0.5 size-4 shrink-0', toneClass(alert.level))} />
            <span className="text-sm leading-snug text-foreground">{alert.title}</span>
          </li>
        )
      })}
    </ul>
  )
}
