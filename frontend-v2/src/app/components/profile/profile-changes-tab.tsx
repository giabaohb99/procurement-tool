import { Eye, Undo2 } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import {
  UNDO_STATUS,
  type BotChange,
  type BotChangeDetail,
  type ChangeSnapshot,
} from '@/modules/system/api/bot-changes-api'
import { useBotChange, useBotChanges, useUndoChange } from '@/modules/system/hooks/use-bot-changes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { Switch } from '@/shared/ui/switch'
import { cn } from '@/shared/utils/cn'
import { formatDate, formatDateTime, formatTime } from '@/shared/utils/format-date'

/**
 * Số dòng nạp một lượt. Cửa web cho tới 200 nhưng mỗi dòng backend kiểm lại `can_undo` (vài truy vấn
 * một dòng), nên lấy vừa đủ cho một màn — sổ này là 24 giờ gần nhất, không phải kho tra cứu.
 */
const PAGE_LIMIT = 50

/** Bốn khóa có thể xuất hiện trong ảnh trước / sau, theo thứ tự hiển thị. */
const SNAPSHOT_KEYS = [
  { key: 'fields', label: 'Trường' },
  { key: 'lines', label: 'Dòng' },
  { key: 'leave', label: 'Nghỉ phép' },
  { key: 'status', label: 'Trạng thái' },
] as const

/**
 * Tab «Bot đã ghi gì» ở Trang cá nhân (ai-CR-185, phase 15.3).
 *
 * Bot ghi gì vào ERP thay mình thì mình phải THẤY được và RÚT LẠI được trong 24 giờ — hợp đồng ở
 * `doc/agent-hub/18-so-thay-doi-va-hoan-tac.md`. Mặc định chỉ sổ của chính mình; người có
 * `agent_group.read` (quản lý bot AI) có công tắc «Xem của mọi người». Nút Hoàn tác chỉ bật khi
 * backend bảo `can_undo` (lý do tắt nằm ở `undo_reason`), và lúc bấm backend kiểm lại từ đầu — nên
 * 409 ở đây là chuyện thường (phiếu vừa bị người khác sửa), không phải lỗi màn.
 */
export function ProfileChangesTab() {
  const { can } = usePermission()
  //  Gác ở giao diện để người thường không bao giờ gửi `all=1` rồi ăn 403.
  const isManager = can('agent_group', 'read')
  const [allUsers, setAllUsers] = useState(false)
  const showAll = isManager && allUsers
  const [detailId, setDetailId] = useState<number | null>(null)

  const { data, isLoading, isError } = useBotChanges(PAGE_LIMIT, showAll)
  //  Chỉ lấy `mutateAsync` (tham chiếu ổn định) để `askUndo` không đổi mỗi lượt render kéo bảng dựng lại cột.
  const { mutateAsync: undoAsync } = useUndoChange()
  /** `disabled={isPending}` không chặn bấm đúp (state chỉ đổi ở lượt render sau) — chặn bằng ref đổi ngay trong tick. */
  const busy = useRef(false)

  const askUndo = useCallback(
    async (row: BotChange) => {
      if (busy.current) return
      busy.current = true
      try {
        const ok = await confirm({
          title: 'Hoàn tác thay đổi của bot',
          message: `Rút lại: ${row.summary}?`,
          confirmLabel: 'Hoàn tác',
          tone: 'default',
        })
        if (ok) await undoAsync(row.id)
      } catch {
        //  Lỗi đã hiện toast trong hook (đúng `message` của phong bì).
      } finally {
        busy.current = false
      }
    },
    [undoAsync],
  )

  const columns = useMemo<DataTableColumn<BotChange>[]>(() => {
    const cols: DataTableColumn<BotChange>[] = [
      { key: 'when', header: 'Lúc', width: 100, cell: (r) => formatShortDateTime(r.when) },
    ]
    if (showAll) {
      cols.push({ key: 'user', header: 'Người', width: 140, cell: (r) => r.user_name || `#${r.user_id}` })
    }
    cols.push(
      {
        key: 'doc_code',
        header: 'Phiếu',
        width: 130,
        cell: (r) => {
          const text = r.doc_code || `${r.entity_label} #${r.entity_id}`
          return r.url ? (
            <Link
              to={r.url}
              title={r.entity_label}
              className="font-medium text-primary hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {text}
            </Link>
          ) : (
            <span title={r.entity_label}>{text}</span>
          )
        },
      },
      { key: 'action', header: 'Hành động', width: 110, cell: (r) => r.action_label },
      { key: 'summary', header: 'Tóm tắt', hideable: false, wrap: true, cell: (r) => r.summary },
      { key: 'source', header: 'Kênh', width: 90, cell: (r) => r.source_label },
      { key: 'undo_status', header: 'Trạng thái', width: 150, cell: (r) => <UndoStatusCell row={r} /> },
      {
        key: 'undo',
        header: 'Hoàn tác',
        width: 110,
        align: 'center',
        hideable: false,
        cell: (r) => (
          //  Nút tắt không nhận sự kiện chuột, nên `title` đặt ở thẻ bọc mới hiện được lý do.
          <span
            title={r.can_undo ? undefined : r.undo_reason || 'Không hoàn tác được dòng này.'}
            className="inline-flex"
            onClick={(e) => e.stopPropagation()}
          >
            <Button
              type="button"
              size="xs"
              variant="outline"
              disabled={!r.can_undo}
              aria-label={`Hoàn tác: ${r.summary}`}
              onClick={() => void askUndo(r)}
            >
              <Undo2 className="size-3" /> Hoàn tác
            </Button>
          </span>
        ),
      },
    )
    return cols
  }, [showAll, askUndo])

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
          <SectionHeading>Bot đã ghi gì</SectionHeading>
          {isManager && (
            <div className="flex items-center gap-2">
              <Switch id="bot-changes-all-users" checked={allUsers} onCheckedChange={setAllUsers} />
              <Label htmlFor="bot-changes-all-users" className="cursor-pointer font-normal">
                Xem của mọi người
              </Label>
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p className="flex items-start gap-1.5 text-muted-foreground">
            <Eye className="mt-0.5 size-4 shrink-0" />
            Mọi phiếu bot tạo, sửa, xóa hay gửi duyệt thay bạn đều ghi ở đây. Rút lại được trong 24 giờ khi
            phiếu còn ở Nháp / Bị trả lại và chưa ai sửa chen; dòng đã gửi duyệt hay lập bộ tài khoản chỉ ghi
            sổ. Bấm vào dòng để xem giá trị trước / sau.
          </p>
          <DataTable
            columns={columns}
            rows={data?.items}
            getRowId={(r) => r.id}
            isLoading={isLoading}
            isError={isError}
            emptyMessage={showAll ? 'Bot chưa ghi thay đổi nào.' : 'Bot chưa ghi thay đổi nào cho bạn.'}
            errorMessage="Không tải được sổ thay đổi."
            storageKey="profile.bot-changes"
            onRowClick={(r) => setDetailId(r.id)}
          />
        </CardContent>
      </Card>

      <ChangeDetailDialog id={detailId} onClose={() => setDetailId(null)} />
    </div>
  )
}

/** `13/10 09:30` — cột hẹp, sổ chỉ 24 giờ gần nhất nên năm là thừa. */
function formatShortDateTime(value: string): string {
  const day = formatDate(value)
  if (!day) return ''
  return `${day.slice(0, 5)} ${formatTime(value)}`
}

function UndoStatusCell({ row }: { row: BotChange }) {
  if (row.undo_of) {
    return <span className="text-muted-foreground">Hoàn tác của #{row.undo_of}</span>
  }
  const tone =
    row.undo_status === UNDO_STATUS.DONE
      ? TONE_CLASS.done
      : row.undo_status === UNDO_STATUS.BLOCKED
        ? TONE_CLASS.danger
        : TONE_CLASS.neutral
  return (
    <Badge variant="outline" className={cn('border-transparent', tone)}>
      {row.undo_status_label}
    </Badge>
  )
}

interface ChangeDetailDialogProps {
  id: number | null
  onClose: () => void
}

/** Hộp chi tiết một dòng: hai cột Trước / Sau, chỉ các khóa có trong ảnh chụp. */
function ChangeDetailDialog({ id, onClose }: ChangeDetailDialogProps) {
  const { data, isLoading } = useBotChange(id)
  return (
    <Dialog open={id !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 pr-6 text-base">
            <span>{data?.summary || 'Chi tiết thay đổi'}</span>
            {id !== null && <span className="font-mono text-sm text-muted-foreground">#{id}</span>}
          </DialogTitle>
          <DialogDescription>
            {data ? <ChangeMetaLine row={data} /> : 'Giá trị trước và sau khi bot ghi.'}
          </DialogDescription>
        </DialogHeader>
        {isLoading || !data ? (
          <Skeleton className="h-40" />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            <SnapshotColumn title="Trước" snapshot={data.before} />
            <SnapshotColumn title="Sau" snapshot={data.after} />
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function ChangeMetaLine({ row }: { row: BotChangeDetail }) {
  const parts = [
    formatDateTime(row.when),
    row.doc_code ? `${row.entity_label} ${row.doc_code}` : row.entity_label,
    row.action_label,
    row.source_label,
    row.undo_of ? `Hoàn tác của #${row.undo_of}` : row.undo_status_label,
  ].filter(Boolean)
  return <>{parts.join(' · ')}</>
}

interface SnapshotColumnProps {
  title: string
  snapshot: ChangeSnapshot | null
}

function SnapshotColumn({ title, snapshot }: SnapshotColumnProps) {
  const present = snapshot ? SNAPSHOT_KEYS.filter(({ key }) => snapshot[key] !== undefined) : []
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border">
      <h4 className="border-b bg-muted/50 px-3 py-1.5 text-xs font-semibold">{title}</h4>
      <div className="space-y-2 p-3 text-xs">
        {!snapshot && <p className="text-muted-foreground">(trống)</p>}
        {snapshot && present.length === 0 && !snapshot.truncated && (
          <p className="text-muted-foreground">(không có trường nào)</p>
        )}
        {present.map(({ key, label }) => (
          <div key={key}>
            <div className="mb-0.5 font-medium text-muted-foreground">{label}</div>
            <pre className="whitespace-pre-wrap break-all rounded bg-muted/40 p-2 font-mono">
              {JSON.stringify(snapshot?.[key], null, 1)}
            </pre>
          </div>
        ))}
        {snapshot?.truncated && <p className="text-muted-foreground">(đã cắt bớt)</p>}
      </div>
    </section>
  )
}
