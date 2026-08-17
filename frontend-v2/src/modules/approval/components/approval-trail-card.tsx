import { CircleDot, Printer, ShieldCheck } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { useApprovalTrail } from '../hooks/use-approvals'
import { INSTANCE_STATUS, TASK_STATUS } from '../types/approval'

interface ApprovalTrailCardProps {
  instanceId: number
  className?: string
}

/**
 * BẢN IN DẤU VẾT DUYỆT (I20) — ai duyệt, lúc nào, ý kiến gì.
 *
 * *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là
 * một tờ giấy in ra được, không phải một ảnh chụp màn hình"*.
 *
 * Câu chữ của từng dòng do **backend dựng** (`sentence`), không ghép ở đây: bản
 * in trên web và bản xuất ra tệp phải đọc ra đúng một câu, mà ghép ở hai nơi thì
 * sớm muộn cũng lệch.
 *
 * Thẻ này dùng được trên trang chi tiết của MỌI loại chứng từ — nó chỉ cần
 * `instanceId`.
 */
export function ApprovalTrailCard({ instanceId, className }: ApprovalTrailCardProps) {
  const { data } = useApprovalTrail(instanceId)

  const instance = data?.instance
  const lines = data?.lines ?? []
  const tasks = data?.tasks ?? []
  const dangCho = tasks.filter((row) => row.status === TASK_STATUS.pending)

  return (
    <Card className={cn('print:border-0 print:shadow-none', className)}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldCheck className="size-4 text-muted-foreground" />
          Dấu vết duyệt
          {instance && (
            <Badge
              variant={
                instance.status === INSTANCE_STATUS.approved
                  ? 'default'
                  : instance.status === INSTANCE_STATUS.blocked
                    ? 'destructive'
                    : 'outline'
              }
            >
              {instance.status_label}
            </Badge>
          )}
        </CardTitle>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="print:hidden"
          onClick={() => window.print()}
        >
          <Printer className="size-4" />
          In
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {instance && (
          <p className="text-sm text-muted-foreground">
            Luồng «{instance.flow_name}» bản {instance.flow_version}
            {instance.started_by_name && ` · ${instance.started_by_name} trình duyệt`}
            {instance.started_at && ` ngày ${formatDate(instance.started_at)}`}
          </p>
        )}

        {/*  Phiếu KẸT phải nói ra chứ không im lặng: nó không tự đi tiếp, và
             không ai biết là đang thiếu người nếu màn hình không kêu. */}
        {instance?.status === INSTANCE_STATUS.blocked && (
          <p className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-sm">
            <b>Phiếu đang kẹt:</b> {instance.finish_reason}
          </p>
        )}

        {lines.length === 0 ? (
          <p className="text-sm text-muted-foreground">Chưa có thao tác nào.</p>
        ) : (
          <ol className="space-y-3">
            {lines.map((line) => (
              <li key={line.id} className="flex gap-3">
                <CircleDot className="mt-1 size-3.5 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm">
                    {/*  Câu do backend dựng — đây là câu sẽ in ra giấy. */}
                    <span className="font-medium">{line.sentence}</span>
                    {line.node_name && (
                      <span className="text-muted-foreground"> · {line.node_name}</span>
                    )}
                  </p>
                  {line.comment && (
                    <p className="mt-0.5 text-sm text-muted-foreground">“{line.comment}”</p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {formatDate(line.created_at)}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}

        {dangCho.length > 0 && (
          <div className="border-t pt-3">
            <p className="text-sm font-medium">Đang chờ</p>
            <ul className="mt-1 space-y-1">
              {dangCho.map((row) => (
                <li key={row.id} className="text-sm text-muted-foreground">
                  {row.assignee_name} — {row.node_name || `bước ${row.node_seq}`}
                  {row.due_at && ` · hạn ${formatDate(row.due_at)}`}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
