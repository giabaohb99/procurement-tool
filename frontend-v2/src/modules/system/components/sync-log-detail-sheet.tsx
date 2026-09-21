import { ListTree, RotateCw, TriangleAlert } from 'lucide-react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { RETRYABLE_SYNC_STATUSES, SYNC_GRAIN, type SyncLogDetail } from '../api/sync-log-api'
import { useRetrySyncLog, useSyncLogDetail } from '../hooks/use-sync-logs'
import { syncStatusTone } from '../utils/sync-log-format'

interface SyncLogDetailSheetProps {
  /** `null` = đóng ngăn. */
  logId: number | null
  onClose: () => void
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <div className="min-w-0 break-words text-sm">{children}</div>
    </div>
  )
}

/**
 * Ngăn CHI TIẾT MỘT DÒNG SỔ — nguyên văn lỗi + nguyên cục dữ liệu bên kia gửi.
 *
 * Nút *Chạy lại* cố ý CHỈ nằm ở đây, không đặt thành nút trên từng dòng bảng.
 * Chạy lại là gọi ngược sang hệ ngoài; bấm nó mà chưa đọc câu lỗi thì phần lớn
 * lần bấm là vô ích (khóa hết hạn, phiếu bên kia đã xóa — chạy bao nhiêu lần
 * cũng hỏng y hệt). Bắt mở dòng ra mới bấm được là bắt nhìn thấy lý do trước.
 */
export function SyncLogDetailSheet({ logId, onClose }: SyncLogDetailSheetProps) {
  const { can } = usePermission()
  const navigate = useNavigate()
  const { data, isLoading, isError } = useSyncLogDetail(logId)
  const retry = useRetrySyncLog()

  const canRetry =
    can('sync_log', 'write') && data && RETRYABLE_SYNC_STATUSES.includes(data.status)

  return (
    <Sheet open={logId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-3xl">
        <SheetHeader className="border-b">
          <SheetTitle className="flex flex-wrap items-center gap-2">
            {data ? (
              <>
                <Badge className={cn(TONE_CLASS[syncStatusTone(data.status)])}>
                  {data.status_label}
                </Badge>
                <span className="text-sm font-normal">
                  {data.source_label} · {data.entity_label || data.job_label || '—'}
                </span>
              </>
            ) : (
              'Chi tiết dòng sổ đồng bộ'
            )}
          </SheetTitle>
          <SheetDescription className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs">#{logId}</span>
            {data?.legacy_id && (
              <>
                <span className="font-mono text-xs">{data.legacy_id}</span>
                <CopyButton value={data.legacy_id} label="mã bên app cũ" />
              </>
            )}
          </SheetDescription>
        </SheetHeader>

        {isLoading && (
          <div className="space-y-3 p-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}

        {isError && (
          <div className="p-4">
            <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
              Không đọc được dòng sổ này. Dòng THÀNH CÔNG cũ hơn sáu tháng đã được
              dọn định kỳ; dòng lỗi thì giữ vĩnh viễn nên vẫn phải tra ra được.
            </p>
          </div>
        )}

        {data && <SyncLogDetailBody data={data} />}

        {data && (
          <div className="flex items-center justify-between gap-3 border-t p-4">
            <p className="text-xs text-muted-foreground">
              Chạy lại sinh một dòng MỚI ở trạng thái chờ — dòng này giữ nguyên lịch sử.
            </p>
            <div className="flex shrink-0 items-center gap-2">
              {/*  Từ một LƯỢT CHẠY bấm xuống đúng đám bản ghi nó vừa ghi. Đây là
                   thứ hai bảng nhật ký riêng ngày trước không làm được, và là lý
                   do `tab_sync_log` gộp cả hai hạt vào một bảng. */}
              {data.grain === SYNC_GRAIN.RUN && (
                <Button
                  variant="outline"
                  onClick={() => {
                    onClose()
                    navigate(`${appRoutes.system.syncLogs}?run_id=${data.id}`)
                  }}
                >
                  <ListTree className="size-4 mr-1.5" />
                  Bản ghi của lượt này
                </Button>
              )}
              {canRetry && (
                <Button onClick={() => retry.mutate(data.id)} disabled={retry.isPending}>
                  <RotateCw className="size-4 mr-1.5" />
                  Chạy lại
                </Button>
              )}
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  )
}

function SyncLogDetailBody({ data }: { data: SyncLogDetail }) {
  const isRun = data.grain === SYNC_GRAIN.RUN

  return (
    <div className="min-h-0 flex-1 space-y-4 overflow-auto p-4">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Field label="Hạt">{data.grain_label || '—'}</Field>
        <Field label="Chiều">{data.direction_label || '—'}</Field>
        <Field label="Hành động">{data.action_label || '—'}</Field>
        <Field label="Ghi lúc">{formatDateTime(data.created_at) || '—'}</Field>
        <Field label="Thử lần cuối">{data.last_tried_at || '—'}</Field>
        <Field label="Kết thúc">{data.finished_at || '—'}</Field>
        {isRun ? (
          <>
            <Field label="Công việc">{data.job_label || '—'}</Field>
            <Field label="Con trỏ từ">
              <span className="font-mono text-xs">{data.cursor_from || '—'}</span>
            </Field>
            <Field label="Con trỏ tới">
              <span className="font-mono text-xs">{data.cursor_to || '—'}</span>
            </Field>
            <Field label="Kéo về">
              <span className="tabular-nums">{data.fetched}</span>
            </Field>
            <Field label="Đã ghi">
              <span className="tabular-nums">{data.written}</span>
            </Field>
            <Field label="Bỏ qua">
              <span className="tabular-nums">{data.skipped}</span>
            </Field>
          </>
        ) : (
          <>
            <Field label="Mã bên app cũ">
              <span className="font-mono text-xs">{data.legacy_id || '—'}</span>
            </Field>
            <Field label="Mã bên ERP">
              {/*  0 nghĩa là CHƯA tạo được bản ghi tương ứng — khác hẳn "chưa
                   tra", nên hiện chữ chứ không hiện số 0 trần. */}
              <span className="tabular-nums">{data.local_id || 'Chưa có'}</span>
            </Field>
            <Field label="Thuộc lượt chạy">
              {data.run_id ? `#${data.run_id}` : 'Không sinh từ lượt chạy nào'}
            </Field>
            <Field label="Số lần đã thử">
              <span className="tabular-nums">{data.attempt_count}</span>
            </Field>
            <Field label="Băm nội dung">
              <span className="font-mono text-xs">{data.content_hash || '—'}</span>
            </Field>
            <Field label="Mã sự kiện">
              <span className="font-mono text-xs">{data.event_id || '—'}</span>
            </Field>
          </>
        )}
      </div>

      {data.warning_labels.length > 0 && (
        <div className="rounded-lg border border-warning/40 bg-warning/5 p-3">
          <p className="mb-2 flex items-center gap-1.5 text-sm font-medium text-warning">
            <TriangleAlert className="size-4" />
            Cảnh báo dữ liệu
          </p>
          {/*  Cờ sống được cả trên dòng THÀNH CÔNG: phiếu đã vào ERP nhưng có ô
               do máy suy ra hoặc bịa mặc định. Đây là chỗ duy nhất nhìn ra. */}
          <div className="flex flex-wrap gap-1.5">
            {data.warning_labels.map((label) => (
              <Badge key={label} className={cn(TONE_CLASS.pending)}>
                {label}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="mb-1 text-xs text-muted-foreground">Nguyên văn bên kia trả về</p>
        <pre className="max-h-48 overflow-auto rounded-lg border bg-muted/40 p-3 text-xs whitespace-pre-wrap break-words">
          {data.message || '(không có)'}
        </pre>
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">Nguyên cục dữ liệu nhận được</p>
          {data.payload && <CopyButton value={data.payload} label="cục dữ liệu" />}
        </div>
        {/*  CHUỖI thô, không tô màu JSON và không `JSON.parse`: đúng lúc hỏng thì
             cục này thường không phải JSON hợp lệ, mà chỗ này tồn tại để thấy
             thứ ĐÃ THẬT SỰ nhận được, không phải thứ hệ thống hiểu được. */}
        <pre className="max-h-96 overflow-auto rounded-lg border bg-muted/40 p-3 font-mono text-xs whitespace-pre-wrap break-all">
          {data.payload || '(không lưu cục dữ liệu nào cho dòng này)'}
        </pre>
      </div>
    </div>
  )
}
