import { useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { confirm } from '@/shared/ui/confirm-dialog'
import { toWorkHistoryPayload, uploadWorkHistoryFiles } from '../api/employee-work-history-api'
import type { EmployeeWorkHistoryFormValues } from '../schemas/employee-work-history-schema'
import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { planApplyPrompt, type ApplyPromptValues } from '../utils/employee-work-history-apply'
import { useSaveEmployeeWorkHistory } from './use-employee-work-history'

/** Nhãn hiển thị tối thiểu — khớp `LookupItem` của `components/lookup-select.tsx`
 *  nhưng không import chéo sang tầng component (hook chỉ cần hai trường này). */
interface LabelOption {
  id: number
  label: string
}

function labelFor(items: LabelOption[], id: number): string | undefined {
  return items.find((item) => item.id === id)?.label
}

interface UseEmployeeWorkHistoryFormSubmitArgs {
  employeeId: number
  employee: Employee
  /** `null`/`undefined` = đang TẠO dòng mới. */
  row?: EmployeeWorkHistory | null
  allRows: EmployeeWorkHistory[]
  extraDeptIds: number[]
  /** A9 (Q4) — `false` thì không tải tệp đã xếp hàng lên (M4, không có gì để tải vì vùng thả đã ẩn). */
  canOpenFiles: boolean
  today: string
  /** Dòng chính đang mở, sớm hơn dòng mới — quyết định có gửi `close_open_main` hay không. */
  openMainRow: EmployeeWorkHistory | null
  companyOptions: LabelOption[]
  departmentOptions: LabelOption[]
  positionOptions: LabelOption[]
  queuedFiles: File[]
  onOpenChange: (open: boolean) => void
}

/**
 * Điều phối LƯU + câu hỏi áp hồ sơ của hộp thêm/sửa «Quá trình công tác»
 * (tách khỏi `employee-work-history-form-dialog.tsx` để mỗi tệp dưới ~200
 * dòng, CLAUDE.md §"File Size Management"). Thôi việc (Q2) đi hộp xác nhận
 * RIÊNG (`EmployeeWorkHistoryResignConfirmDialog`, dựng ở nơi gọi); loại khác
 * đi `confirm()` chung với `confirmLabel`/`cancelLabel` riêng (M6).
 */
export function useEmployeeWorkHistoryFormSubmit({
  employeeId,
  employee,
  row,
  allRows,
  extraDeptIds,
  canOpenFiles,
  today,
  openMainRow,
  companyOptions,
  departmentOptions,
  positionOptions,
  queuedFiles,
  onOpenChange,
}: UseEmployeeWorkHistoryFormSubmitArgs) {
  const queryClient = useQueryClient()
  const saveMutation = useSaveEmployeeWorkHistory(employeeId)
  const submittingRef = useRef(false)
  const [pendingResign, setPendingResign] = useState<{
    values: EmployeeWorkHistoryFormValues
    resignDate: string
  } | null>(null)

  async function save(values: EmployeeWorkHistoryFormValues, applyToProfile: boolean) {
    const payload = toWorkHistoryPayload({
      ...values,
      close_open_main: Boolean(openMainRow) && values.close_open_main,
      apply_to_profile: applyToProfile,
    })
    const result = await saveMutation.mutateAsync({ id: row?.id, payload })
    if (!row && canOpenFiles && queuedFiles.length > 0) {
      void uploadWorkHistoryFiles(result.item.id, queuedFiles)
        .then(() => {
          //  M5 — cột «Tệp» của bảng đọc `employeeWorkHistory(id)`; tải tệp đi
          //  đường riêng (không qua hook) nên phải tự dọn cache ở đây, không
          //  thì `file_count` đứng im tới lần nạp sau.
          void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeWorkHistory(employeeId) })
        })
        .catch(() => {
          toast.error('Đã lưu dòng nhưng tải tệp QĐ lên thất bại — mở lại dòng để thử lại.')
        })
    }
    onOpenChange(false)
  }

  async function onSubmit(values: EmployeeWorkHistoryFormValues) {
    if (submittingRef.current) return

    const promptValues: ApplyPromptValues = {
      event_type: values.event_type,
      from_date: values.from_date,
      to_date: values.to_date,
      company_id: values.company_id,
      company_label: labelFor(companyOptions, values.company_id),
      department_id: values.department_id,
      department_label: labelFor(departmentOptions, values.department_id),
      position_id: values.position_id,
      position_label: labelFor(positionOptions, values.position_id),
    }
    //  Thôi việc (Q2) đi hộp xác nhận RIÊNG — KHÔNG mở `confirm()` chung.
    const prompt = planApplyPrompt(promptValues, employee, extraDeptIds, today, allRows, row?.id ?? 0)
    if (prompt?.kind === 'resign') {
      setPendingResign({ values, resignDate: prompt.resignDate })
      return
    }

    submittingRef.current = true
    try {
      const applyToProfile =
        prompt?.kind === 'profile'
          ? await confirm({
              title: 'Cập nhật hồ sơ hiện tại?',
              message: [
                ...prompt.changes.map((c) => `• ${c}`),
                '',
                //  M6 — Esc/đóng hộp KHÔNG có nút riêng để phân biệt với «Chỉ
                //  lưu dòng» (cùng `confirm()` chung cho mọi màn) nên phải NÓI
                //  RÕ hệ quả ngay trong câu, thay vì đổi hành vi Esc.
                'Đóng hộp này (hoặc nhấn Esc) sẽ CHỈ lưu dòng, không cập nhật hồ sơ.',
              ].join('\n'),
              confirmLabel: 'Lưu và cập nhật hồ sơ',
              cancelLabel: 'Chỉ lưu dòng',
            })
          : false
      await save(values, applyToProfile)
    } finally {
      submittingRef.current = false
    }
  }

  function handleResignConfirm(applyToProfile: boolean) {
    if (!pendingResign || submittingRef.current) return
    submittingRef.current = true
    save(pendingResign.values, applyToProfile).finally(() => {
      submittingRef.current = false
      setPendingResign(null)
    })
  }

  return { saveMutation, onSubmit, pendingResign, setPendingResign, handleResignConfirm }
}
