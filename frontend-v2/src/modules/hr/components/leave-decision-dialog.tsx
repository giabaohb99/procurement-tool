import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
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
import { formatDate } from '@/shared/utils/format-date'
import type { ApprovalDecision } from '../hooks/use-leave'
import type { LeaveInboxRow } from '../types/leave'

interface LeaveDecisionDialogProps {
  row: LeaveInboxRow | null
  decision: ApprovalDecision
  isPending: boolean
  onClose: () => void
  onConfirm: (reason: string) => void
}

interface DecisionFace {
  title: string
  /** Câu nhắc người bấm đang làm gì — đọc trước khi ký, không phải sau. */
  hint: string
  confirmLabel: string
  /** Từ chối và trả về BẮT BUỘC lý do; duyệt thì không. */
  reasonRequired: boolean
  reasonLabel: string
  reasonPlaceholder: string
  variant: 'default' | 'destructive'
}

/**
 * ⚠️ **Từ chối và trả về BẮT BUỘC lý do, duyệt thì không.** Backend cũng chặn
 * (`action_service._require_reason`), nhưng chặn ở đây mới đúng chỗ: để backend
 * chặn thì người dùng gõ xong, bấm, rồi mới ăn một câu lỗi đỏ — còn ở đây nút
 * mờ sẵn và họ biết ngay phải nhập gì.
 *
 * Duyệt KHÔNG bắt lý do vì bắt thì người ta gõ "ok" hai mươi lần một buổi sáng,
 * và ô ý kiến mất sạch giá trị cho những lần thật sự có gì để nói.
 */
const FACES: Record<ApprovalDecision, DecisionFace> = {
  approve: {
    title: 'Duyệt đơn nghỉ phép',
    hint: 'Duyệt xong, chữ ký của bạn vào dấu vết và phiếu đi tiếp chặng sau (nếu còn).',
    confirmLabel: 'Duyệt',
    reasonRequired: false,
    reasonLabel: 'Ý kiến (không bắt buộc)',
    reasonPlaceholder: 'Ví dụ: Đồng ý, nhớ bàn giao trước khi nghỉ.',
    variant: 'default',
  },
  return: {
    title: 'Trả đơn về cho người nộp',
    hint: 'Người nộp sửa lại rồi gửi duyệt lần nữa. Đơn KHÔNG bị đóng.',
    confirmLabel: 'Trả về',
    reasonRequired: true,
    reasonLabel: 'Cần sửa gì',
    reasonPlaceholder: 'Ví dụ: Thiếu người bàn giao, bổ sung rồi gửi lại.',
    variant: 'default',
  },
  reject: {
    title: 'Từ chối đơn nghỉ phép',
    hint: 'Đơn đóng hẳn, người nộp KHÔNG sửa lại được. Muốn nghỉ nữa thì phải lập đơn khác.',
    confirmLabel: 'Từ chối',
    reasonRequired: true,
    reasonLabel: 'Lý do từ chối',
    reasonPlaceholder: 'Ví dụ: Trùng lịch nghỉ của cả phòng, dời sang tuần sau.',
    variant: 'destructive',
  },
}

/**
 * HỘP XÁC NHẬN cho ba quyết định duyệt, mở ngay từ dòng danh sách (CR-260).
 *
 * ⚠️ Hộp này TÓM TẮT tờ đơn chứ không chỉ hỏi "có chắc không". Duyệt ngay trên
 * dòng nhanh thật, nhưng nhanh mà ký nhầm ngày nghỉ của người khác thì hỏng
 * hơn là chậm — nên bốn thông tin quyết định (ai nghỉ · loại nghỉ · khoảng ngày
 * · số ngày) phải nằm ngay trước mắt lúc bấm nút.
 */
export function LeaveDecisionDialog({
  row,
  decision,
  isPending,
  onClose,
  onConfirm,
}: LeaveDecisionDialogProps) {
  const [reason, setReason] = useState('')
  const face = FACES[decision]

  //  Dọn ô lý do mỗi lần mở hộp cho một tờ đơn khác hoặc một quyết định khác.
  //  Giữ lại thì lý do từ chối của đơn trước dính sang đơn sau — và nó sẽ được
  //  ghi thẳng vào dấu vết phê duyệt.
  //
  //  Gán trong lúc RENDER chứ không trong `useEffect`: effect chạy sau khi đã
  //  commit nên người dùng thấy một khung hình còn chữ cũ rồi mới thấy ô trống.
  //  Xem `shared/hooks/use-has-changed.ts`.
  if (useHasChanged(`${row?.id ?? 0}:${decision}`)) {
    setReason('')
  }

  const canConfirm = !isPending && (!face.reasonRequired || reason.trim().length > 0)

  return (
    <Dialog open={row !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{face.title}</DialogTitle>
          <DialogDescription>{face.hint}</DialogDescription>
        </DialogHeader>

        {row && (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-md border bg-muted/20 px-4 py-3 text-sm">
            <Field label="Số đơn" value={row.code} />
            <Field label="Người nghỉ" value={row.employee_name || `#${row.employee_id}`} />
            <Field label="Loại nghỉ" value={row.leave_type_name || '—'} />
            <Field label="Số ngày" value={`${row.total_days} ngày`} />
            <Field
              label="Thời gian nghỉ"
              value={`${formatDate(row.from_date)} → ${formatDate(row.to_date)}`}
              wide
            />
            {row.reason && <Field label="Lý do nghỉ" value={row.reason} wide />}
            {/*  ⚠️ Bàn giao LUÔN hiện, kể cả khi trống — và câu lúc trống phải
                 nói thẳng ra. *Thiếu người bàn giao* là lý do trả đơn phổ biến
                 nhất, nên nó chính là thứ quyết định người ta bấm Duyệt hay Trả
                 về. Giấu nó đi khi rỗng thì cả cái hộp này mất đúng lý do tồn
                 tại: để họ quyết mà không phải mở tờ đơn ra. */}
            <Field
              label="Bàn giao công việc"
              value={
                row.handovers?.length
                  ? row.handovers
                      .map((h) =>
                        h.content
                          ? `${h.employee_name || `#${h.employee_id}`}: ${h.content}`
                          : h.employee_name || `#${h.employee_id}`,
                      )
                      .join(' · ')
                  : 'Chưa khai người nhận bàn giao'
              }
              wide
            />
          </dl>
        )}

        <div className="space-y-2">
          <Label htmlFor="leave-decision-reason">{face.reasonLabel}</Label>
          <Textarea
            id="leave-decision-reason"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder={face.reasonPlaceholder}
          />
          {face.reasonRequired && (
            <p className="text-xs text-muted-foreground">
              Người nộp chỉ đọc được câu này. Không ghi thì họ không biết phải sửa gì.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isPending}>
            Đóng
          </Button>
          <Button
            type="button"
            variant={face.variant}
            disabled={!canConfirm}
            onClick={() => onConfirm(reason.trim())}
          >
            {face.confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Field({ label, value, wide = false }: { label: string; value: string; wide?: boolean }) {
  return (
    <div className={wide ? 'col-span-2 min-w-0' : 'min-w-0'}>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      {/*  `break-words`: lý do nghỉ là chữ tự do, có thể là chuỗi dài không dấu
           cách — không bẻ thì nó nong hộp thoại rộng ra khỏi màn hình. */}
      <dd className="mt-0.5 font-medium break-words">{value}</dd>
    </div>
  )
}
