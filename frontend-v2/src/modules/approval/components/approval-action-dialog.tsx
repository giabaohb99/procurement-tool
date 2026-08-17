import { Check, CornerUpLeft, MessageSquare, UserCheck, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { ENTITY_LABELS, entityLink } from '../helpers/entity-link'
import { useApprovalAction, type ApprovalActionKind } from '../hooks/use-approvals'
import type { MyTask } from '../types/approval'

interface ApprovalActionDialogProps {
  task: MyTask
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Ba việc BẮT BUỘC nêu lý do — backend chặn, giao diện nói trước cho đỡ mất công. */
const CAN_LY_DO: ApprovalActionKind[] = ['reject', 'return', 'withdraw']

const NHAN: Record<ApprovalActionKind, string> = {
  approve: 'Duyệt',
  reject: 'Từ chối',
  return: 'Trả lại',
  withdraw: 'Rút lại',
  comment: 'Ghi ý kiến',
}

/**
 * Bấm duyệt / từ chối / trả lại ngay trên hộp việc, không phải mở từng phiếu.
 *
 * **Từ chối** khác **trả lại**, và hộp thoại phải nói ra: từ chối là phiếu chết
 * hẳn, phải làm phiếu mới; trả lại là phiếu còn sống, người nộp sửa rồi gửi
 * lại. Gộp hai nút làm một là người duyệt bấm nhầm và người nộp mất cả phiếu.
 */
export function ApprovalActionDialog({ task, open, onOpenChange }: ApprovalActionDialogProps) {
  const [kind, setKind] = useState<ApprovalActionKind>('approve')
  const [text, setText] = useState('')
  const action = useApprovalAction(task.instance_id)

  const canLyDo = CAN_LY_DO.includes(kind)
  const thieuLyDo = canLyDo && !text.trim()

  function handleSubmit() {
    action.mutate(
      { kind, text: text.trim() },
      {
        onSuccess: () => {
          onOpenChange(false)
          setText('')
          setKind('approve')
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{task.entity_title || 'Phiếu chờ duyệt'}</DialogTitle>
          <DialogDescription>
            {ENTITY_LABELS[task.entity] ?? task.entity} ·{' '}
            <Link
              to={entityLink(task.entity, task.entity_id)}
              className="font-mono hover:underline"
            >
              {task.entity_code || `#${task.entity_id}`}
            </Link>{' '}
            · {task.node_name || `Bước ${task.node_seq}`}
          </DialogDescription>
        </DialogHeader>

        {/*  Bấm THAY người khác là việc khác hẳn bấm cho mình — nói ra trước khi
             họ bấm, vì nhật ký sẽ ghi cả hai tên và bản in sẽ đọc ra câu đó. */}
        {task.on_behalf_of_name && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <UserCheck className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Bạn đang xử lý <b>thay {task.on_behalf_of_name}</b> theo ủy quyền. Nhật ký
              sẽ ghi cả hai tên.
            </span>
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          <ChonViec kind="approve" dang={kind} onChon={setKind} icon={Check} />
          <ChonViec kind="return" dang={kind} onChon={setKind} icon={CornerUpLeft} />
          <ChonViec kind="reject" dang={kind} onChon={setKind} icon={X} destructive />
          <ChonViec kind="comment" dang={kind} onChon={setKind} icon={MessageSquare} />
        </div>

        <p className="text-sm text-muted-foreground">
          {kind === 'reject' && 'Phiếu dừng hẳn — người nộp phải làm phiếu mới.'}
          {kind === 'return' && 'Phiếu còn sống — người nộp sửa rồi gửi duyệt lại.'}
          {kind === 'approve' && 'Phiếu chuyển sang bước kế tiếp.'}
          {kind === 'comment' && 'Chỉ ghi ý kiến, không đổi trạng thái phiếu.'}
        </p>

        <div className="space-y-2">
          <Label htmlFor="approval-comment">
            {canLyDo ? 'Lý do' : 'Ý kiến'}
            {canLyDo && <span className="text-destructive"> *</span>}
          </Label>
          <Textarea
            id="approval-comment"
            rows={3}
            placeholder={
              canLyDo
                ? 'Nêu rõ cần sửa gì — thiếu câu này thì lần gửi sau y hệt lần trước.'
                : 'Không bắt buộc.'
            }
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          <Button
            type="button"
            variant={kind === 'reject' ? 'destructive' : 'default'}
            disabled={thieuLyDo || action.isPending}
            onClick={handleSubmit}
          >
            {NHAN[kind]}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface ChonViecProps {
  kind: ApprovalActionKind
  dang: ApprovalActionKind
  onChon: (kind: ApprovalActionKind) => void
  icon: React.ComponentType<{ className?: string }>
  destructive?: boolean
}

function ChonViec({ kind, dang, onChon, icon: Icon, destructive }: ChonViecProps) {
  const chon = kind === dang
  return (
    <Button
      type="button"
      size="sm"
      variant={chon ? (destructive ? 'destructive' : 'default') : 'outline'}
      className={cn(!chon && destructive && 'text-destructive')}
      onClick={() => onChon(kind)}
    >
      <Icon className="size-4" />
      {NHAN[kind]}
    </Button>
  )
}
