import { ChevronsUp, ScrollText } from 'lucide-react'
import { Fragment, useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'
import { collapseSameRequest, describeAuditEntry } from './describe-audit-entry'
import { useAuditLogs } from './use-audit-logs'

/** Số dòng hiện thêm mỗi lần bấm "Xem thêm". */
const PAGE_STEP = 10

interface AuditActivityFeedProps {
  /** Tên entity như backend ghi log: `employee`, `company`… */
  entity: string
  entityId: number
  /** Tên cột → nhãn người dùng thấy ở form; cột không có trong bảng bị bỏ khỏi câu. */
  fieldLabels?: Record<string, string>
  /** Danh từ cho dòng tạo mới: "đã tạo ‹hồ sơ này›". */
  createdNoun?: string
}

/**
 * Khối "Hoạt động" kiểu ERPNext (duoc-CR-710): đường dọc có chấm, mỗi dòng một câu
 * "**Dego Admin** đã cập nhật **Phòng ban**, **Công ty** · 3 ngày trước".
 *
 * Khác `AuditTimeline` (khối thẻ dùng ở ~37 màn, giữ nguyên): không có thẻ / tiêu đề riêng — khung bọc
 * ngoài lo tiêu đề; thời gian TƯƠNG ĐỐI (rê chuột ra ngày giờ đầy đủ); các dòng cùng một lượt lưu được
 * gộp làm một. Cùng nguồn dữ liệu `useAuditLogs`, nên cùng luật quyền của `/api/audit-logs`.
 */
export function AuditActivityFeed({
  entity,
  entityId,
  fieldLabels,
  createdNoun,
}: AuditActivityFeedProps) {
  const [visible, setVisible] = useState(PAGE_STEP)
  const { can } = usePermission()
  //  Lối sang màn Nhật ký hệ thống chỉ cho người đọc được màn đó (cùng luật `AuditTimeline`).
  const canReadSystemLogs = can('audit', 'read') || can('setting', 'read')
  const { data, isLoading } = useAuditLogs(entity, entityId)
  const logs = collapseSameRequest(data ?? [])
  const remaining = logs.length - visible

  if (isLoading) return <Skeleton className="h-20 w-full" />
  if (logs.length === 0) {
    return <p className="text-sm text-muted-foreground">Chưa có hoạt động nào.</p>
  }

  return (
    <div>
      {/*  Đường dọc nối các chấm: viền trái của danh sách, chấm đặt đè lên viền. */}
      <ol className="relative ml-1.5 space-y-5 border-l border-border pl-5">
        {logs.slice(0, visible).map((log) => {
          const { verb, fields } = describeAuditEntry(log, fieldLabels, createdNoun)
          return (
            <li key={log.id} className="relative text-sm leading-relaxed">
              <span
                aria-hidden
                className="absolute top-2 -left-[25px] size-2 rounded-full border-2 border-card bg-muted-foreground/60"
              />
              <span className="font-semibold">{log.by}</span> {verb}
              {fields.map((label, i) => (
                <Fragment key={label}>
                  {i === 0 ? ' ' : ', '}
                  <span className="font-semibold">{label}</span>
                </Fragment>
              ))}
              <span className="text-muted-foreground">
                {' · '}
                <time dateTime={log.at} title={formatDateTime(log.at)}>
                  {formatRelativeTime(log.at)}
                </time>
              </span>
              {canReadSystemLogs && log.request_id && (
                <Link
                  to={appRoutes.system.logDetail(log.request_id)}
                  className="ml-2 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground hover:underline"
                  title="Xem lượt gọi API đã sinh ra dòng này (giá trị trước / sau)"
                >
                  <ScrollText className="size-3" />
                  Chi tiết
                </Link>
              )}
            </li>
          )
        })}
      </ol>

      {(remaining > 0 || visible > PAGE_STEP) && (
        <div className="mt-4 flex gap-2">
          {remaining > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setVisible((n) => n + PAGE_STEP)}
            >
              Xem thêm {Math.min(remaining, PAGE_STEP)} hoạt động
              {remaining > PAGE_STEP ? ` (còn ${remaining})` : ''}
            </Button>
          )}
          {visible > PAGE_STEP && (
            <Button type="button" variant="ghost" size="sm" onClick={() => setVisible(PAGE_STEP)}>
              <ChevronsUp />
              Thu gọn
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
