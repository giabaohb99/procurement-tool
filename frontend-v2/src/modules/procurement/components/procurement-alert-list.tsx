import { AlertTriangle, ChevronDown, CircleCheck, Clock, FileText, Truck } from 'lucide-react'
import { useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { DashboardAlert } from '../api/procurement-dashboard-api'

/**
 * Số việc bày sẵn ở khổ điện thoại trước khi phải bấm «Xem thêm».
 *
 * Ba, vì mỗi câu cảnh báo ở đây dài **ba đến bốn dòng** — backend nhét cả tên
 * sản phẩm lẫn ngày hẹn vào một chuỗi (`Giao hàng TRỄ: PO00130 · Thùng Tago
 * chai HDPE 500ml x 40 chai (60x35.5x21.5cm) (hẹn 2026-07-05)`), đo được ~80px
 * một việc ở 390px. Ba việc ≈ 240px, xấp xỉ đúng phần mà ô cuộn 320px của màn
 * rộng bày ra một lúc. Cắt ở đây KHÔNG giấu gì thêm so với màn rộng: nút nói rõ
 * còn mấy việc, mà backend thì trả tối đa **6** việc (`alerts[:6]`) nên câu dài
 * nhất nút này in ra là «Xem thêm 3 việc».
 */
const MOBILE_PREVIEW = 3

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
  const isMobile = useIsMobile()
  const [expanded, setExpanded] = useState(false)

  //  Khổ điện thoại cắt bớt NGAY TẠI DANH SÁCH thay vì nhét cả danh sách vào
  //  một ô cuộn cao 320px như màn rộng: ô cuộn lồng trong trang cuộn thì trên
  //  máy cảm ứng ngón tay đặt vào đúng khối này là kéo danh sách con, trang
  //  đứng im — người dùng tưởng trang bị treo. Nút bấm nói rõ còn bao nhiêu
  //  việc, mà số đó thì cái thanh cuộn không nói được.
  const hidden = isMobile && !expanded ? Math.max(0, alerts.length - MOBILE_PREVIEW) : 0
  const shown = hidden > 0 ? alerts.slice(0, MOBILE_PREVIEW) : alerts

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
    <>
      <ul className="divide-y">
        {shown.map((alert, index) => {
          const Icon = TYPE_ICON[alert.type] ?? AlertTriangle
          return (
            <li key={`${alert.type}-${index}`} className="flex gap-3 py-2.5 first:pt-0">
              <Icon className={cn('mt-0.5 size-4 shrink-0', toneClass(alert.level))} />
              <span className="text-sm leading-snug text-foreground">{alert.title}</span>
            </li>
          )
        })}
      </ul>

      {hidden > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="mt-2 w-full text-muted-foreground"
          onClick={() => setExpanded(true)}
        >
          <ChevronDown />
          Xem thêm {hidden} việc
        </Button>
      )}
    </>
  )
}
