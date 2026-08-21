import { Check, CircleDashed, CircleDot, MinusCircle, ShieldCheck, X } from 'lucide-react'
import { useState } from 'react'

import { ApprovalActionDialog } from '@/modules/approval/components/approval-action-dialog'
import { ApprovalTrailCard } from '@/modules/approval/components/approval-trail-card'
import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, ApprovalTask } from '@/modules/approval/types/approval'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { useMyDocumentTask } from '../hooks/use-my-document-approvals'

interface DocumentApprovalTabProps {
  instance: ApprovalInstance | null | undefined
  /** Văn bản đang mở — để tìm việc duyệt của chính người đọc. */
  documentId: number
}

/** Bộ mặt của một chặng, gộp từ trạng thái các việc thuộc chặng đó. */
function trangThaiChang(viec: ApprovalTask[], seq: number, instance: ApprovalInstance) {
  const cua = viec.filter((row) => row.node_seq === seq)
  if (cua.some((row) => row.status === TASK_STATUS.rejected)) return 'tu-choi'
  if (cua.some((row) => row.status === TASK_STATUS.pending)) return 'dang-cho'
  if (cua.length > 0 && cua.every((row) => row.status === TASK_STATUS.skippedDuplicate))
    return 'tu-qua'
  if (cua.some((row) => row.status === TASK_STATUS.approved)) return 'xong'
  //  Chưa có việc nào ở chặng này: hoặc chưa tới lượt, hoặc phiếu đã dừng trước
  //  khi tới đây. Cả hai đều vẽ như nhau — chặng chưa chạm tới.
  return instance.current_seq > seq ? 'khong-chay' : 'chua-toi'
}

const HINH = {
  xong: {
    icon: Check,
    nut: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    nhan: 'Đã duyệt',
  },
  'dang-cho': {
    icon: CircleDot,
    nut: 'border-sky-200 bg-sky-50 text-sky-700',
    nhan: 'Đang chờ',
  },
  'tu-choi': {
    icon: X,
    nut: 'border-destructive/30 bg-destructive/5 text-destructive',
    nhan: 'Từ chối',
  },
  'tu-qua': {
    icon: MinusCircle,
    nut: 'border-border bg-muted text-muted-foreground',
    nhan: 'Tự qua vì trùng người',
  },
  'chua-toi': {
    icon: CircleDashed,
    nut: 'border-border bg-background text-muted-foreground',
    nhan: 'Chưa tới lượt',
  },
  'khong-chay': {
    icon: CircleDashed,
    nut: 'border-border bg-muted text-muted-foreground',
    nhan: 'Không chạy',
  },
} as const

/**
 * Tab PHÊ DUYỆT của trang chi tiết văn bản: phiếu này đang đi tới đâu.
 *
 * Trang chi tiết trước đây không nói gì về luồng duyệt ngoài hai chữ «Đang
 * duyệt», nên người soạn không biết chờ ai còn người vừa ký không biết mình
 * đang đứng ở khúc nào của một luồng bốn bước.
 *
 * Hai kiểu bước dễ đọc nhầm nên phải phân biệt bằng mắt:
 *
 * - **nhiều người trong CÙNG một chặng** — mỗi người một dòng con, thấy ngay còn
 *   thiếu chữ ký nào;
 * - **tự qua vì trùng người duyệt** — KHÁC "đã duyệt", vẽ mờ và nói rõ, vì gộp
 *   làm một là bản in nói dối rằng có thêm một người đã xem xét.
 *
 * **Nút duyệt CÓ ở đây (21/08/2026)** — nhưng chỉ hiện với đúng người đang cầm
 * việc, và vẫn là hộp thoại chung của bộ máy duyệt chứ không phải một đường
 * riêng của phân hệ Văn bản. Bản trước cố ý không có nút và bắt sang «Việc của
 * tôi»: người duyệt phải rời văn bản đang đọc để đi bấm ở một danh sách, hoặc
 * ký mà chưa mở văn bản ra.
 */
export function DocumentApprovalTab({ instance, documentId }: DocumentApprovalTabProps) {
  const viecCuaToi = useMyDocumentTask(documentId)
  const [dangXuLy, setDangXuLy] = useState(false)

  if (!instance) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          Văn bản này chưa vào bộ máy duyệt nhiều bước.
          <br />
          Nó đi theo luồng duyệt một bước cũ, hoặc chưa được gửi duyệt lần nào.
        </CardContent>
      </Card>
    )
  }

  const viec = instance.tasks ?? []
  const chang = [...new Set((instance.steps ?? []).map((buoc) => buoc.seq))].sort((a, b) => a - b)

  return (
    <div className="space-y-4">
      <Card className="gap-0 py-0">
        <CardHeader className="flex min-h-16 flex-row items-center justify-between gap-4 border-b px-5 py-4">
          <CardTitle className="text-base">
            Luồng «{instance.flow_name}» bản {instance.flow_version}
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge
              variant={
                instance.status === INSTANCE_STATUS.approved
                  ? 'default'
                  : instance.status === INSTANCE_STATUS.blocked ||
                      instance.status === INSTANCE_STATUS.rejected
                    ? 'destructive'
                    : 'outline'
              }
            >
              {instance.status_label}
            </Badge>
            {/*  Chỉ đúng người đang cầm việc mới thấy nút. Bày cho mọi người là
                 đẻ lại đúng cái đường tắt mà bộ máy duyệt vừa bịt. */}
            {viecCuaToi && (
              <Button type="button" size="sm" onClick={() => setDangXuLy(true)}>
                <ShieldCheck className="size-4" />
                Duyệt / Trả lại
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="px-5 py-5">
          <ol aria-label="Các chặng phê duyệt" className="max-w-5xl">
            {chang.map((seq, index) => {
              const ten =
                (instance.steps ?? []).find((buoc) => buoc.seq === seq)?.name || `Bước ${seq}`
              const trang_thai = trangThaiChang(viec, seq, instance)
              const { icon: Icon, nut, nhan } = HINH[trang_thai]
              const nguoi = viec.filter((row) => row.node_seq === seq)
              const dangHienTai = instance.status === INSTANCE_STATUS.running && seq === instance.current_seq

              return (
                <li
                  key={seq}
                  className="relative flex gap-4 pb-6 last:pb-0"
                  aria-current={dangHienTai ? 'step' : undefined}
                >
                  {index < chang.length - 1 && (
                    <span
                      data-testid="approval-flow-step-rail"
                      aria-hidden="true"
                      className="approval-flow-step-rail"
                    />
                  )}
                  <span
                    className={cn(
                      'relative z-10 grid size-8 shrink-0 place-items-center rounded-full border',
                      nut,
                    )}
                    aria-hidden="true"
                  >
                    <Icon className="size-4" strokeWidth={2.25} />
                  </span>

                  <div className="min-w-0 flex-1 pt-1">
                    <div className="flex flex-col gap-0.5 sm:flex-row sm:items-baseline sm:gap-2">
                      <h3 className="text-sm leading-5 font-semibold">
                        Chặng {seq} · {ten}
                      </h3>
                      <span
                        className={cn(
                          'text-xs font-medium',
                          dangHienTai ? 'text-primary' : 'text-muted-foreground',
                        )}
                      >
                        {nhan}
                      </span>
                    </div>
                    {nguoi.length > 0 && (
                      <ul className="mt-1 space-y-1">
                        {nguoi.map((row) => (
                          <li key={row.id} className="text-sm leading-5 text-muted-foreground">
                            <span className="font-medium text-foreground">{row.assignee_name}</span>
                            {nguoi.length > 1 && (
                              <>
                                <span aria-hidden="true"> · </span>
                                {row.status_label}
                              </>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              )
            })}
          </ol>
        </CardContent>
      </Card>

      <ApprovalTrailCard instanceId={instance.id} />

      {dangXuLy && viecCuaToi && (
        <ApprovalActionDialog task={viecCuaToi} open onOpenChange={setDangXuLy} />
      )}
    </div>
  )
}
