import { EyeOff, Globe, MonitorSmartphone, TriangleAlert } from 'lucide-react'
import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { CopyButton } from '@/shared/ui/copy-button'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDateTime } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

import type { SystemLogAuditEntry, SystemLogSessionInfo } from '../api/system-log-api'
import { useSystemLogDetail } from '../hooks/use-system-logs'
import { formatDuration, httpStatusHint, httpStatusTone } from '../utils/system-log-format'
import { SystemLogChangeTable } from './system-log-change-table'

interface SystemLogDetailSheetProps {
  /** `null` = đóng ngăn. Mở bằng cách truyền `request_id` dạng chuỗi có gạch nối. */
  requestId: string | null
  onClose: () => void
}

/**
 * Ngăn CHI TIẾT MỘT LƯỢT GỌI — bốn tab (bao-CR-407, §8.3).
 *
 * Bốn tab là bốn bảng dưới CSDL đọc theo cùng một `request_id`: *Tổng quan* kể
 * chuyện (`tab_audit_log`), *Request* là sự thật kỹ thuật (`tab_request_log`),
 * *Thay đổi* là từng trường (`tab_change_log`), *Phiên* là thiết bị
 * (`tab_login_session`). Gộp chúng vào một trang cuộn dài thì lượt gọi nào cũng
 * phải cuộn qua ba phần không liên quan để tới phần mình cần.
 */
export function SystemLogDetailSheet({ requestId, onClose }: SystemLogDetailSheetProps) {
  const { data, isLoading, isError } = useSystemLogDetail(requestId)

  return (
    <Sheet open={Boolean(requestId)} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-3xl">
        <SheetHeader className="border-b">
          <SheetTitle className="flex flex-wrap items-center gap-2">
            {data ? (
              <>
                <span className="font-mono text-sm">{data.request.method}</span>
                <span className="min-w-0 break-all text-sm font-normal">{data.request.path}</span>
              </>
            ) : (
              'Chi tiết lượt gọi'
            )}
          </SheetTitle>
          <SheetDescription className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs">{requestId}</span>
            {requestId && <CopyButton value={requestId} label="mã lượt gọi" />}
          </SheetDescription>
        </SheetHeader>

        {isLoading && (
          <div className="space-y-3 p-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        )}

        {isError && (
          <div className="p-4">
            <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
              Không đọc được lượt gọi này. Nhật ký chỉ giữ 16 tháng — mã cũ hơn mốc đó đã bị dọn.
            </p>
          </div>
        )}

        {data && (
          <Tabs defaultValue="overview" className="flex min-h-0 flex-1 flex-col gap-0">
            <TabsList className="m-4 mb-0 w-fit shrink-0">
              <TabsTrigger value="overview">Tổng quan</TabsTrigger>
              <TabsTrigger value="request">Request</TabsTrigger>
              <TabsTrigger value="changes">
                Thay đổi
                {data.can_read_changes && data.changes.length > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {data.changes.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="session">Phiên</TabsTrigger>
            </TabsList>

            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              <TabsContent value="overview" className="mt-0 space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <InfoRow label="Lúc" value={formatDateTime(data.request.at)} />
                  <InfoRow
                    label="Người thao tác"
                    value={data.request.user_name || `Tài khoản #${data.request.user_id}`}
                  />
                  <InfoRow
                    label="Kết quả"
                    value={
                      <span className="flex items-center gap-2">
                        <Badge
                          className={cn(TONE_CLASS[httpStatusTone(data.request.http_status)])}
                        >
                          {data.request.http_status || '—'}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {httpStatusHint(data.request.http_status)}
                        </span>
                      </span>
                    }
                  />
                  <InfoRow label="Mất" value={formatDuration(data.request.duration_ms)} />
                </div>

                <AuditStory entries={data.audit} />
              </TabsContent>

              <TabsContent value="request" className="mt-0 space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <InfoRow label="Đường (đã gom)" value={data.request.route || '—'} mono />
                  <InfoRow label="Nguồn" value={data.request.source_label || '—'} />
                  <InfoRow label="IP" value={data.request.ip || '—'} mono />
                  <InfoRow label="Thiết bị" value={data.request.device || '—'} />
                  <InfoRow label="Tham số URL" value={data.request.query_string || '—'} mono />
                  <InfoRow label="Trang gọi từ" value={data.request.referer || '—'} mono />
                  <InfoRow label="Mã lỗi" value={data.request.error_code || '—'} mono />
                  <InfoRow label="Phiên" value={data.request.session_id || '—'} />
                </div>

                {data.can_read_changes ? (
                  <div className="space-y-3">
                    <CodeBlock title="Thân yêu cầu" text={data.request.request_body} />
                    <CodeBlock title="Thân trả về" text={data.request.response_body} />
                    <CodeBlock
                      title="Chi tiết lỗi"
                      text={data.request.error_detail}
                      tone="danger"
                    />
                  </div>
                ) : (
                  <div className="flex items-start gap-2 rounded-lg border border-dashed border-input bg-muted/40 p-4 text-sm text-muted-foreground">
                    <EyeOff className="mt-0.5 size-4 shrink-0" />
                    <div>
                      <p className="font-medium text-foreground">
                        Thân yêu cầu / trả về và chi tiết lỗi bị ẩn
                      </p>
                      <p className="mt-0.5">
                        Ba phần này cần khóa quyền{' '}
                        <span className="font-mono text-xs">change_log</span> vì thân yêu cầu chứa
                        đúng những giá trị người dùng vừa gõ.
                      </p>
                    </div>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="changes" className="mt-0">
                <SystemLogChangeTable changes={data.changes} canRead={data.can_read_changes} />
              </TabsContent>

              <TabsContent value="session" className="mt-0">
                <SessionPanel session={data.session} />
              </TabsContent>
            </div>
          </Tabs>
        )}
      </SheetContent>
    </Sheet>
  )
}

interface InfoRowProps {
  label: string
  value: ReactNode
  mono?: boolean
}

function InfoRow({ label, value, mono = false }: InfoRowProps) {
  return (
    <div className="min-w-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <div className={cn('mt-0.5 break-words text-sm', mono && 'font-mono text-xs')}>{value}</div>
    </div>
  )
}

/**
 * Dòng thời gian NGHIỆP VỤ của lượt gọi.
 *
 * Rỗng là chuyện bình thường chứ không phải lỗi: lượt `GET`, lượt ăn 403, lượt
 * 500 chết trước khi vào service đều không đẻ ra dòng audit nào — và đó chính là
 * những lượt màn này tồn tại để bày ra.
 */
function AuditStory({ entries }: { entries: SystemLogAuditEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
        Lượt gọi này không ghi dòng nghiệp vụ nào — thường gặp ở lượt chỉ xem, lượt bị chặn, hoặc
        lượt hỏng trước khi chạy tới phần xử lý.
      </p>
    )
  }

  return (
    <ol className="space-y-2">
      {entries.map((entry) => (
        <li key={entry.id} className="rounded-lg border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{entry.action_label || entry.action}</Badge>
            {entry.doc_code && <span className="font-mono text-xs">{entry.doc_code}</span>}
            <span className="text-xs text-muted-foreground">{formatDateTime(entry.at)}</span>
          </div>
          <p className="mt-1.5 text-sm">{entry.message || '—'}</p>
          {entry.changed_fields && (
            <p className="mt-1 font-mono text-xs text-muted-foreground break-all">
              {entry.changed_fields}
            </p>
          )}
        </li>
      ))}
    </ol>
  )
}

function SessionPanel({ session }: { session: SystemLogSessionInfo | null }) {
  if (!session) {
    return (
      <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
        Lượt gọi này không gắn phiên đăng nhập nào — việc nền, script, hoặc lượt gọi khi chưa đăng
        nhập.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {session.ip_changed && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" />
          <div>
            <p className="font-medium">Phiên này đổi IP giữa chừng</p>
            <p className="mt-0.5 text-muted-foreground">
              Vào từ {session.ip}, dùng tiếp từ {session.last_seen_ip}. Có thể chỉ là đổi mạng, cũng
              có thể là token bị mang sang máy khác.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <InfoRow
          label="Thiết bị"
          value={
            <span className="flex items-center gap-1.5">
              <MonitorSmartphone className="size-3.5 shrink-0 text-muted-foreground" />
              {session.device_label || '—'}
            </span>
          }
        />
        <InfoRow
          label="Hệ điều hành / trình duyệt"
          value={[session.os, session.browser].filter(Boolean).join(' · ') || '—'}
        />
        <InfoRow
          label="IP đăng nhập"
          value={
            <span className="flex items-center gap-1.5 font-mono text-xs">
              <Globe className="size-3.5 shrink-0 text-muted-foreground" />
              {session.ip || '—'}
            </span>
          }
        />
        <InfoRow label="IP lần cuối" value={session.last_seen_ip || '—'} mono />
        <InfoRow label="Đăng nhập lúc" value={formatDateTime(session.created_at)} />
        <InfoRow label="Hoạt động cuối" value={formatDateTime(session.last_seen_at)} />
        <InfoRow label="Hết hạn" value={formatDateTime(session.expires_at) || '—'} />
        <InfoRow
          label="Bị cắt lúc"
          value={session.revoked_at ? formatDateTime(session.revoked_at) : 'Chưa bị cắt'}
        />
      </div>
    </div>
  )
}

interface CodeBlockProps {
  title: string
  text?: string
  tone?: 'default' | 'danger'
}

/**
 * Khối JSON / traceback.
 *
 * `undefined` nghĩa là backend đã lược (không có quyền) — nhưng nhánh đó đã được
 * chặn ở tầng trên, nên ở đây rỗng chỉ còn nghĩa *lượt gọi vốn không có phần
 * này* (GET không có thân, lượt chạy trót lọt không có traceback). Vẫn nói rõ
 * thay vì vẽ một khung trống.
 */
function CodeBlock({ title, text, tone = 'default' }: CodeBlockProps) {
  const body = (text ?? '').trim()

  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="flex items-center justify-between gap-2 border-b bg-muted/50 px-3 py-1.5">
        <span className="text-xs font-medium">{title}</span>
        {body && <CopyButton value={body} label={title.toLowerCase()} />}
      </div>
      {body ? (
        <pre
          className={cn(
            'max-h-72 overflow-auto p-3 text-xs whitespace-pre-wrap break-all',
            tone === 'danger' && 'text-destructive',
          )}
        >
          {body}
        </pre>
      ) : (
        <p className="p-3 text-xs italic text-muted-foreground">Không có nội dung.</p>
      )}
    </div>
  )
}
