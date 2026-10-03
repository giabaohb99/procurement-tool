import { useRef, useState } from 'react'

import { confirm } from '@/shared/ui/confirm-dialog'
import { toDateInputValue } from '@/shared/utils/format-date'
import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { planApplyPrompt, workHistoryRowToApplyValues } from '../utils/employee-work-history-apply'
import { useApplyEmployeeWorkHistory } from './use-employee-work-history'

/** Chặn bấm đúp theo từng id — `useRef` đổi NGAY trong tick, `disabled` chỉ báo hiệu. */
export function useBusyIds() {
  const ref = useRef<Set<number>>(new Set())
  const [ids, setIds] = useState<Set<number>>(new Set())
  function run(id: number, fn: (onSettled: () => void) => void) {
    if (ref.current.has(id)) return
    ref.current.add(id)
    setIds(new Set(ref.current))
    fn(() => {
      ref.current.delete(id)
      setIds(new Set(ref.current))
    })
  }
  return { ids, run }
}

/**
 * H1 (code review 03/10/2026) — nút ▶ «Áp vào hồ sơ» của TỪNG DÒNG phải HỎI
 * trước khi gọi `/apply`, dùng LẠI đúng một luật `planApplyPrompt` của hộp Lưu
 * (M6) — không chép luật ra bản thứ hai. Thôi việc → hộp riêng (khóa TK); loại
 * khác → `confirm()` chung, liệt kê thay đổi cũ → mới (đã có sẵn trên dòng,
 * không cần tra danh mục). Tách khỏi `employee-tab-work-history.tsx` để tệp
 * đó giữ dưới ~200 dòng (CLAUDE.md §"File Size Management").
 */
export function useEmployeeWorkHistoryRowApply(
  employeeId: number,
  employee: Employee,
  extraDeptIds: number[],
  items: EmployeeWorkHistory[],
) {
  const applyMutation = useApplyEmployeeWorkHistory(employeeId)
  const applying = useBusyIds()
  const [resignApply, setResignApply] = useState<{ row: EmployeeWorkHistory; resignDate: string } | null>(null)

  function runApply(row: EmployeeWorkHistory) {
    applying.run(row.id, (done) => applyMutation.mutate(row.id, { onSettled: done }))
  }

  function onApply(row: EmployeeWorkHistory) {
    const today = toDateInputValue(new Date())
    const prompt = planApplyPrompt(workHistoryRowToApplyValues(row), employee, extraDeptIds, today, items, row.id)

    if (prompt?.kind === 'resign') {
      setResignApply({ row, resignDate: prompt.resignDate })
      return
    }

    const message =
      prompt?.kind === 'profile'
        ? prompt.changes.map((c) => `• ${c}`).join('\n')
        : 'Dòng này sẽ được áp vào hồ sơ.'
    void confirm({
      title: 'Áp dòng này vào hồ sơ?',
      message,
      confirmLabel: 'Áp vào hồ sơ',
      cancelLabel: 'Hủy',
    }).then((ok) => {
      if (ok) runApply(row)
    })
  }

  function closeResignApply() {
    setResignApply(null)
  }

  function confirmResignApply() {
    if (!resignApply) return
    runApply(resignApply.row)
    setResignApply(null)
  }

  return {
    isApplying: (row: EmployeeWorkHistory) => applying.ids.has(row.id),
    onApply,
    resignApply,
    closeResignApply,
    confirmResignApply,
  }
}
