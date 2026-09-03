import { CalendarX2, Check, FileText, Send, Undo2, X, type LucideIcon } from 'lucide-react'

import {
  ApprovalTrailCard,
  type TrailExtraEvent,
} from '@/modules/approval/components/approval-trail-card'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'
import { decisionNoteOf } from '../utils/leave-decision-note'

interface LeaveApprovalTimelineProps {
  request: LeaveRequest
}

interface TimelineStep {
  key: string
  icon: LucideIcon
  title: string
  time?: string | null
  /** Câu giải thích — với ba kết cục xấu thì đây chính là LÝ DO người duyệt ghi. */
  detail?: string
  tone: 'done' | 'current' | 'bad' | 'todo'
}

const TONE_CLASS: Record<TimelineStep['tone'], string> = {
  done: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40',
  current: 'border-sky-200 bg-sky-50 text-sky-700 dark:bg-sky-950/40',
  bad: 'border-destructive/30 bg-destructive/5 text-destructive',
  todo: 'border-border bg-background text-muted-foreground',
}

/**
 * LUỒNG DUYỆT của tờ đơn, dạng dòng thời gian.
 *
 * Hai đường, tùy môi trường có khai luồng nhiều bước hay không:
 *
 * 1. **Có luồng** (`approval_instance_id > 0`) → dựng thẳng `ApprovalTrailCard`
 *    của phân hệ Phê duyệt. Nó đọc dấu vết THẬT (ai ký chặng nào, ủy quyền cho
 *    ai, ý kiến gì) và cùng một câu chữ với bản in phê duyệt. Chép lại một bản
 *    riêng cho Nghỉ phép là sớm muộn hai chỗ nói khác nhau.
 * 2. **Duyệt thẳng** (chưa khai luồng) → không có dấu vết nào để đọc, nên dựng
 *    ba mốc từ chính tờ đơn: lập → gửi duyệt → kết quả.
 *
 * Cả hai đường đều phải nói ra **LÝ DO** khi đơn không được duyệt, và nói ra
 * **ngay trong dòng thời gian** — không phải bằng một dải cảnh báo nằm ngoài.
 * Bộ máy duyệt chỉ ghi việc của nó ("đã rút trình duyệt"), nó không biết gì về
 * `decision_note` của tờ đơn; tách ra hai khối thì người đọc thấy hai câu chuyện
 * rời nhau, mà chuyện quan trọng nhất — vì sao đơn hỏng — lại là cái nằm ngoài.
 */
export function LeaveApprovalTimeline({ request }: LeaveApprovalTimelineProps) {
  if (request.approval_instance_id > 0) {
    const outcome = badOutcomeEvent(request)
    return (
      <ApprovalTrailCard
        instanceId={request.approval_instance_id}
        extraEvents={outcome ? [outcome] : undefined}
      />
    )
  }

  return <PlainTimelineCard request={request} />
}

/**
 * Ba kết cục không-duyệt: ĐỘNG TỪ của người chốt, câu dự phòng khi không biết ai
 * chốt, và biểu tượng.
 *
 * ⚠️ **Ba kết cục này KHÁC NHAU, không được gộp câu chữ.** «Từ chối» là người
 * duyệt bác đơn, «Trả về» là bảo đi sửa rồi nộp lại, còn «Đã hủy» là chính người
 * nộp đổi ý rút đơn. Đọc cả ba thành một câu thì người xem mất luôn khả năng
 * phân biệt đơn mình tự rút với đơn bị sếp bác — mà hai chuyện đó dẫn tới hai
 * hành động hoàn toàn khác.
 *
 * ⚠️ Biểu tượng phải là hình KHÔNG TRÒN: mốc nào cũng nằm trong một vòng tròn
 * viền sẵn, nên nhét `Ban` (vòng tròn gạch chéo) vào là hai vòng tròn lồng nhau,
 * đọc ra thành một cái mốc bị vỡ.
 */
const BAD_OUTCOMES: Record<number, { verb: string; fallbackTitle: string; icon: LucideIcon }> = {
  [LEAVE_STATUS.REJECTED]: {
    verb: 'đã từ chối yêu cầu',
    fallbackTitle: 'Yêu cầu bị từ chối',
    icon: X,
  },
  [LEAVE_STATUS.RETURNED]: {
    verb: 'đã trả yêu cầu về',
    fallbackTitle: 'Yêu cầu bị trả về để chỉnh sửa',
    icon: Undo2,
  },
  [LEAVE_STATUS.CANCELLED]: {
    verb: 'đã hủy yêu cầu',
    fallbackTitle: 'Yêu cầu đã bị hủy',
    icon: CalendarX2,
  },
}

/**
 * Tiêu đề + câu giải thích của một mốc kết cục xấu.
 *
 * Tiêu đề đi ĐÚNG khuôn các mốc khác của dòng thời gian — **tên người + động
 * từ** ("Nguyễn An đã từ chối đơn") — chứ không phải một câu vô chủ ("Đơn bị từ
 * chối"). Xen một dòng vô chủ vào giữa những dòng có chủ ngữ thì mốc quan trọng
 * nhất lại là mốc duy nhất không nói ai chịu trách nhiệm, người nộp mở ra vẫn
 * phải đi hỏi. `decided_by_name` chỉ có ở đường lấy MỘT đơn nên vẫn phải chịu
 * được khi nó rỗng — lúc đó mới rơi về câu vô chủ.
 */
function badOutcomeParts(
  request: LeaveRequest,
): { icon: LucideIcon; title: string; detail: string } | null {
  const outcome = BAD_OUTCOMES[request.status]
  if (!outcome) return null

  const actor = request.decided_by_name?.trim()
  const note = decisionNoteOf(request)
  return {
    icon: outcome.icon,
    title: actor ? `${actor} ${outcome.verb}` : outcome.fallbackTitle,
    detail: note ? `Lý do: ${note}` : 'Không ai ghi lý do.',
  }
}

/**
 * Mốc «vì sao đơn hỏng» để chèn lên đầu dấu vết của bộ máy duyệt.
 *
 * ⚠️ **Chỉ chèn cho ĐƠN BỊ HỦY, không chèn cho Từ chối / Trả về.**
 *
 * Từ chối và trả về là hành động CỦA CHÍNH bộ máy: nó đã ghi sẵn một mốc "đã từ
 * chối" mang đủ người quyết, thời điểm, chặng và lý do (cả hai đường đều bắt
 * buộc nhập lý do). Chèn thêm mốc của đơn ở đó là in cùng một câu hai lần liền
 * nhau — thấy rõ khi lý do dài: hai khối chữ y hệt chồng lên nhau chiếm gấp đôi
 * chỗ, và người đọc phải dò xem hai mốc đó có khác gì nhau không.
 *
 * Hủy thì ngược lại: bộ máy chỉ biết phiên duyệt vừa bị **rút** ("đã rút trình
 * duyệt") — nó không biết tờ đơn bên dưới đã hủy hẳn, cũng không thấy
 * `decision_note`. Thiếu mốc này thì dòng thời gian dừng ở "đã rút", còn câu
 * quan trọng nhất — đơn hủy rồi, vì lý do gì — không nằm ở đâu cả.
 */
function badOutcomeEvent(request: LeaveRequest): TrailExtraEvent | null {
  if (request.status !== LEAVE_STATUS.CANCELLED) return null

  const parts = badOutcomeParts(request)
  if (!parts) return null

  return {
    icon: parts.icon,
    iconClassName: TONE_CLASS.bad,
    title: parts.title,
    detail: parts.detail,
    time: request.decided_at,
    emphasizeBad: true,
  }
}

/** Dòng thời gian tự dựng — dùng khi môi trường chưa khai luồng nhiều bước. */
function PlainTimelineCard({ request }: LeaveApprovalTimelineProps) {
  const steps = buildSteps(request)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Luồng duyệt</CardTitle>
        <p className="text-sm text-muted-foreground">
          Đơn này duyệt thẳng, không qua luồng nhiều bước.
        </p>
      </CardHeader>

      <CardContent>
        <ol className="space-y-0">
          {steps.map((step, index) => (
            <li key={step.key} className="flex gap-3">
              {/* Cột mốc + vạch nối. Vạch nằm ở cột riêng chứ không vẽ bằng viền
                  trái của nội dung — nội dung cao thấp khác nhau thì vạch mới
                  chạy đủ từ mốc này xuống mốc kia. */}
              <div className="flex flex-col items-center">
                <span
                  className={cn(
                    'grid size-8 shrink-0 place-items-center rounded-full border',
                    TONE_CLASS[step.tone],
                  )}
                >
                  <step.icon className="size-4" />
                </span>
                {index < steps.length - 1 && <span className="w-px flex-1 bg-border" />}
              </div>

              <div className={cn('min-w-0 flex-1', index < steps.length - 1 && 'pb-5')}>
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span
                    className={cn(
                      'text-sm font-medium',
                      step.tone === 'todo' && 'text-muted-foreground',
                      step.tone === 'bad' && 'text-destructive',
                    )}
                  >
                    {step.title}
                  </span>
                  {step.time && (
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {formatDateTime(step.time)}
                    </span>
                  )}
                </div>
                {step.detail && (
                  //  `break-words`: lý do là chữ người dùng gõ tự do, có thể là
                  //  một chuỗi 500 ký tự không dấu cách — không bẻ thì nó đẩy
                  //  ngang cả thẻ và sinh thanh cuộn cho toàn trang.
                  <p
                    className={cn(
                      'mt-1 text-sm break-words',
                      step.tone === 'bad' ? 'text-destructive' : 'text-muted-foreground',
                    )}
                  >
                    {step.detail}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}

/** Ba mốc của đường duyệt thẳng. Mốc cuối đổi mặt theo trạng thái. */
function buildSteps(request: LeaveRequest): TimelineStep[] {
  const submitted = Boolean(request.submitted_at)

  const steps: TimelineStep[] = [
    {
      key: 'draft',
      icon: FileText,
      title: 'Lập đơn',
      detail: `Số đơn ${request.code}`,
      tone: 'done',
    },
    {
      key: 'submit',
      icon: Send,
      title: submitted ? 'Đã gửi duyệt' : 'Chưa gửi duyệt',
      time: request.submitted_at,
      detail: submitted ? undefined : 'Bấm «Gửi duyệt» khi đã nhập đủ.',
      tone: submitted ? 'done' : 'todo',
    },
  ]

  //  Lý do đi kèm ĐÚNG cái mốc sinh ra nó, không tách thành dải cảnh báo riêng.
  const badOutcome = badOutcomeParts(request)
  if (badOutcome) {
    steps.push({
      key: 'result',
      icon: badOutcome.icon,
      title: badOutcome.title,
      time: request.decided_at,
      detail: badOutcome.detail,
      tone: 'bad',
    })
  } else if (request.status === LEAVE_STATUS.APPROVED) {
    const approver = request.decided_by_name?.trim()
    const note = request.decision_note?.trim()
    steps.push({
      key: 'result',
      icon: Check,
      //  Cùng khuôn với ba kết cục xấu: nêu tên người chốt ngay ở tiêu đề.
      title: approver ? `${approver} đã duyệt yêu cầu` : 'Yêu cầu đã được duyệt',
      time: request.decided_at,
      detail: note || undefined,
      tone: 'done',
    })
  } else {
    steps.push({
      key: 'result',
      icon: Check,
      title: submitted ? 'Đang chờ duyệt' : 'Chờ kết quả duyệt',
      tone: submitted ? 'current' : 'todo',
    })
  }

  return steps
}
