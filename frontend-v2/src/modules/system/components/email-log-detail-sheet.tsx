import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { CopyButton } from '@/shared/ui/copy-button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import { useEmailLogDetail } from '../hooks/use-email-logs'
import { emailStatusTone } from '../utils/email-log-format'

interface EmailLogDetailSheetProps {
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
 * Ngăn CHI TIẾT MỘT THƯ (bao-CR-721): đủ câu lỗi nguyên văn của máy chủ thư.
 *
 * Trên bảng câu lỗi bị cắt một dòng; ở đây in nguyên, có nút chép để dán vào phiếu hỗ
 * trợ. Không có nút gửi lại — thư là hệ quả của một bước nghiệp vụ, sửa nguyên nhân
 * (hộp thư, địa chỉ người nhận) rồi để bước đó gửi lại.
 */
export function EmailLogDetailSheet({ logId, onClose }: EmailLogDetailSheetProps) {
  const { data, isLoading, isError } = useEmailLogDetail(logId)

  return (
    <Sheet open={logId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-2xl">
        <SheetHeader className="border-b">
          <SheetTitle className="flex flex-wrap items-center gap-2">
            {data ? (
              <>
                <Badge className={cn(TONE_CLASS[emailStatusTone(data.status)])}>{data.status_label}</Badge>
                <span className="text-sm font-normal">{data.event_label || 'Thư gửi thẳng'}</span>
              </>
            ) : (
              'Chi tiết thư'
            )}
          </SheetTitle>
          <SheetDescription className="font-mono text-xs">#{logId}</SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {isLoading && <Skeleton className="h-40 w-full" />}
          {isError && <p className="text-sm text-destructive">Không tải được chi tiết thư.</p>}
          {data && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Lúc ghi">{formatDateTime(data.created_at) || <span>—</span>}</Field>
                <Field label="Lúc gửi xong">{formatDateTime(data.sent_at) || <span>—</span>}</Field>
                <Field label="Người nhận">
                  <span className="inline-flex items-center gap-1">
                    {data.to_email || <span>—</span>}
                    {data.to_email && <CopyButton value={data.to_email} label="địa chỉ người nhận" />}
                  </span>
                </Field>
                <Field label="Người gửi (hộp thư danh nghĩa)">
                  {data.from_email || <span className="text-muted-foreground">SMTP dùng chung</span>}
                </Field>
                <Field label="Loại thư">
                  {data.event_label}
                  {data.event && (
                    <span className="ml-1 font-mono text-xs text-muted-foreground">({data.event})</span>
                  )}
                </Field>
                <Field label="Trạng thái">{data.status_label}</Field>
              </div>
              <Field label="Tiêu đề">{data.subject || <span>—</span>}</Field>
              <div>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">Câu lỗi nguyên văn</p>
                  {data.error && <CopyButton value={data.error} label="câu lỗi" />}
                </div>
                {data.error ? (
                  <pre className="mt-1 max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-md border bg-muted/40 p-3 font-mono text-xs">
                    {data.error}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground">Không có lỗi.</p>
                )}
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
