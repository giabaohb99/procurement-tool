import { CheckCircle2, RotateCcw } from 'lucide-react'
import { useRef } from 'react'

import { labelOf, WORK_TASK_OUTCOME } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { cn } from '@/shared/utils/cn'
import { useSetTaskOutcome } from '../hooks/use-task-types'
import type { WorkTask } from '../types/work'
import { WORK_TASK_OUTCOME_CODE } from '../types/work'

interface TaskOutcomeBoxProps {
  task: WorkTask
  listId: number
  canEdit: boolean
  /** Việc đã xong. Chưa xong (đang làm lại) thì chỉ hiện nhãn — máy chủ từ chối đánh giá việc chưa xong. */
  done: boolean
}

/**
 * Hộp "Đánh giá kết quả" — chỉ hiện khi việc ĐÃ XONG (duoc-CR-656).
 *
 * Người giao (hoặc quản lý dự án) chọn "Đạt" hay "Phải làm lại"; "Phải làm lại" MỞ LẠI việc nên hỏi xác nhận
 * trước. Quyền thật do máy chủ kiểm (403 kèm câu giải thích hiện qua toast); giao diện chỉ ẩn nút với người chỉ xem.
 * Chặn bấm đúp bằng `useRef` (đổi ngay trong tick), `disabled` chỉ để báo hiệu — luật bẫy biểu mẫu #4.
 */
export function TaskOutcomeBox({ task, listId, canEdit, done }: TaskOutcomeBoxProps) {
  const setOutcome = useSetTaskOutcome(listId)
  const busy = useRef(false)

  async function choose(outcome: number) {
    if (busy.current) return
    busy.current = true
    try {
      if (outcome === WORK_TASK_OUTCOME_CODE.REWORK) {
        const ok = await confirm({
          title: 'Yêu cầu làm lại',
          message: `Mở lại công việc "${task.title}" để làm lại? Công việc sẽ trở về trạng thái đang mở.`,
          confirmLabel: 'Làm lại',
        })
        if (!ok) return
      }
      await setOutcome.mutateAsync({ taskId: task.id, outcome })
    } catch {
      //  Toast lỗi đã do lớp gọi API hiện; không để lời hứa bị từ chối thành lỗi chưa bắt.
    } finally {
      busy.current = false
    }
  }

  const current = String(task.outcome)
  const label = labelOf(WORK_TASK_OUTCOME, current)

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border bg-muted/30 px-3 py-2" data-testid="task-outcome-box">
      <span className="text-sm text-muted-foreground">Đánh giá kết quả</span>
      {label && (
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-xs font-medium',
            task.outcome === WORK_TASK_OUTCOME_CODE.PASSED
              ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
              : 'bg-amber-500/15 text-amber-700 dark:text-amber-400',
          )}
        >
          {label}
        </span>
      )}
      {canEdit && done && (
        <div className="ml-auto flex gap-1.5">
          <Button
            type="button"
            size="sm"
            variant={task.outcome === WORK_TASK_OUTCOME_CODE.PASSED ? 'secondary' : 'outline'}
            className="h-7 gap-1.5"
            disabled={setOutcome.isPending}
            onClick={() => void choose(WORK_TASK_OUTCOME_CODE.PASSED)}
          >
            <CheckCircle2 className="size-3.5" />
            {labelOf(WORK_TASK_OUTCOME, String(WORK_TASK_OUTCOME_CODE.PASSED))}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="h-7 gap-1.5"
            disabled={setOutcome.isPending}
            onClick={() => void choose(WORK_TASK_OUTCOME_CODE.REWORK)}
          >
            <RotateCcw className="size-3.5" />
            {labelOf(WORK_TASK_OUTCOME, String(WORK_TASK_OUTCOME_CODE.REWORK))}
          </Button>
        </div>
      )}
    </div>
  )
}
