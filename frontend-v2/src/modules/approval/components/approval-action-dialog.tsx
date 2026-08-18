import {
  AlertTriangle,
  Check,
  Clock,
  CornerUpLeft,
  ExternalLink,
  MessageSquare,
  UserCheck,
  X,
} from 'lucide-react'
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
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
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

/** Nhãn trên NÚT XÁC NHẬN — câu mệnh lệnh, khác nhãn trên thẻ chọn. */
const NHAN_XAC_NHAN: Record<ApprovalActionKind, string> = {
  approve: 'Duyệt phiếu',
  reject: 'Từ chối phiếu',
  return: 'Trả lại người nộp',
  withdraw: 'Rút phiếu',
  comment: 'Gửi ý kiến',
}

const VIEC = [
  {
    kind: 'approve' as const,
    icon: Check,
    ten: 'Duyệt',
    hau_qua: 'Phiếu chuyển sang bước kế tiếp.',
  },
  {
    kind: 'return' as const,
    icon: CornerUpLeft,
    ten: 'Trả lại',
    hau_qua: 'Phiếu còn sống — người nộp sửa rồi gửi lại.',
  },
  {
    kind: 'reject' as const,
    icon: X,
    ten: 'Từ chối',
    hau_qua: 'Phiếu dừng hẳn — phải làm phiếu mới.',
    nang: true,
  },
  {
    kind: 'comment' as const,
    icon: MessageSquare,
    ten: 'Ghi ý kiến',
    hau_qua: 'Không đổi trạng thái phiếu.',
  },
]

/**
 * Bấm duyệt / từ chối / trả lại ngay trên hộp việc, không phải mở từng phiếu.
 *
 * **Từ chối** khác **trả lại**, và hộp thoại phải nói ra: từ chối là phiếu chết
 * hẳn, phải làm phiếu mới; trả lại là phiếu còn sống, người nộp sửa rồi gửi
 * lại. Gộp hai nút làm một là người duyệt bấm nhầm và người nộp mất cả phiếu.
 *
 * Vì thế bốn việc bày thành **thẻ chọn**, mỗi thẻ tự mang câu hậu quả của nó,
 * chứ không phải bốn cái nút. Bản cũ dùng nút: thẻ «Duyệt» đang chọn trông y hệt
 * nút «Duyệt» ở chân hộp thoại, nên một hộp thoại có hai nút xanh cùng tên và
 * người dùng không biết cái nào mới thật sự ký. Nút xác nhận nay chỉ có một, và
 * nhãn của nó đổi theo việc đang chọn.
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
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="pr-6">{task.entity_title || 'Phiếu chờ duyệt'}</DialogTitle>
          <DialogDescription>
            {ENTITY_LABELS[task.entity] ?? task.entity} ·{' '}
            {task.node_name || `Bước ${task.node_seq}`}
          </DialogDescription>
        </DialogHeader>

        {/*  Bối cảnh phiếu gom một hàng: người duyệt cần biết ai trình và hạn khi
             nào TRƯỚC khi ký, và cần một đường mở thẳng sang chứng từ để đọc. */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-md border bg-muted/40 px-3 py-2 text-sm">
          <Link
            to={entityLink(task.entity, task.entity_id)}
            className="flex items-center gap-1.5 font-medium text-primary hover:underline"
          >
            <ExternalLink className="size-3.5" />
            {task.entity_code || `#${task.entity_id}`}
          </Link>
          {task.started_by_name && (
            <span className="text-muted-foreground">{task.started_by_name} trình</span>
          )}
          {task.due_at && (
            <span
              className={cn(
                'flex items-center gap-1.5',
                task.is_overdue ? 'font-medium text-destructive' : 'text-muted-foreground',
              )}
            >
              <Clock className="size-3.5" />
              {task.is_overdue ? 'Quá hạn ' : 'Hạn '}
              {formatDate(task.due_at)}
            </span>
          )}
        </div>

        {/*  Bấm THAY người khác là việc khác hẳn bấm cho mình — nói ra trước khi
             họ bấm, vì nhật ký sẽ ghi cả hai tên và bản in sẽ đọc ra câu đó. */}
        {task.on_behalf_of_name && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <UserCheck className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Bạn đang xử lý <b>thay {task.on_behalf_of_name}</b> theo ủy quyền. Nhật ký sẽ
              ghi cả hai tên.
            </span>
          </p>
        )}

        <RadioGroup
          value={kind}
          onValueChange={(giatri) => setKind(giatri as ApprovalActionKind)}
          //  `items-stretch` đè mặc định `items-center` của RadioGroup: trong
          //  lưới, căn giữa làm hai thẻ cùng hàng cao thấp lệch nhau khi một thẻ
          //  có câu hậu quả dài hơn.
          className="grid items-stretch gap-2 sm:grid-cols-2"
        >
          {VIEC.map((viec) => (
            <ChonViec key={viec.kind} {...viec} dang={kind} />
          ))}
        </RadioGroup>

        <div className="space-y-2">
          <Label htmlFor="approval-comment">
            {canLyDo ? 'Lý do' : 'Ý kiến'}
            {canLyDo ? (
              <span className="text-destructive"> *</span>
            ) : (
              <span className="font-normal text-muted-foreground"> — không bắt buộc</span>
            )}
          </Label>
          <Textarea
            id="approval-comment"
            rows={3}
            aria-invalid={thieuLyDo || undefined}
            placeholder={
              canLyDo
                ? 'Nêu rõ cần sửa gì — thiếu câu này thì lần gửi sau y hệt lần trước.'
                : 'Điều bạn muốn người đọc dấu vết sau này biết.'
            }
            value={text}
            onChange={(event) => setText(event.target.value)}
          />
          {thieuLyDo && (
            <p className="flex items-center gap-1.5 text-sm text-destructive">
              <AlertTriangle className="size-3.5" />
              Phải nêu lý do thì người nộp mới biết sửa gì.
            </p>
          )}
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
            {NHAN_XAC_NHAN[kind]}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface ChonViecProps {
  kind: ApprovalActionKind
  dang: ApprovalActionKind
  icon: React.ComponentType<{ className?: string }>
  ten: string
  hau_qua: string
  /** Việc phá phiếu — viền đỏ lúc chọn, để không bấm nhầm mà không hay. */
  nang?: boolean
}

function ChonViec({ kind, dang, icon: Icon, ten, hau_qua, nang }: ChonViecProps) {
  const chon = kind === dang
  return (
    <label
      className={cn(
        'flex cursor-pointer items-start gap-2.5 rounded-md border p-3 text-sm transition-colors',
        chon && nang && 'border-destructive bg-destructive/5',
        chon && !nang && 'border-primary bg-accent/40',
        !chon && 'hover:bg-muted/50',
      )}
    >
      {/*  Chấm chọn của việc phá phiếu cũng phải đỏ. Primitive ghim cứng
           `bg-primary` cho chấm nên đổi màu từ đây, thay vì sửa tệp shadcn dùng
           chung cho cả app.
           ⚠️ Phải là `[&>span>span]` chứ KHÔNG phải `[&_span]`: cây của Radix là
           button > Indicator(span) > chấm(span), nên `[&_span]` tô luôn cả lớp
           Indicator — nó không có kích thước riêng nên phình ra kín cả ô vuông,
           thành một hình tròn đỏ đặc thay vì cái chấm. */}
      <RadioGroupItem
        value={kind}
        className={cn(
          'mt-0.5',
          nang && 'data-[state=checked]:border-destructive [&>span>span]:bg-destructive',
        )}
      />
      <span className="min-w-0 flex-1">
        <span className={cn('flex items-center gap-2 font-medium', nang && 'text-destructive')}>
          <Icon className="size-4" />
          {ten}
        </span>
        <span className="mt-0.5 block text-muted-foreground">{hau_qua}</span>
      </span>
    </label>
  )
}
