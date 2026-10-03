import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { toDateInputValue } from '@/shared/utils/format-date'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useEmployeeWorkHistoryFormSubmit } from '../hooks/use-employee-work-history-form-submit'
import { useJobPositions } from '../hooks/use-job-positions'
import {
  EMPTY_EMPLOYEE_WORK_HISTORY_FORM,
  employeeWorkHistorySchema,
  type EmployeeWorkHistoryFormValues,
} from '../schemas/employee-work-history-schema'
import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { MAIN_TRACK } from '../utils/employee-work-history-apply'
import { buildEmployeeWorkHistoryDefaultValues } from '../utils/employee-work-history-form-defaults'
import {
  EmployeeWorkHistoryFilesDialog,
  WORK_HISTORY_FILE_MAX_SIZE_MB,
} from './employee-work-history-files-dialog'
import { EmployeeWorkHistoryFormDialogFields } from './employee-work-history-form-dialog-fields'
import { EmployeeWorkHistoryResignConfirmDialog } from './employee-work-history-resign-confirm-dialog'
import type { LookupItem } from './lookup-select'

interface EmployeeWorkHistoryFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  employeeId: number
  employee: Employee
  /** `null`/`undefined` = đang TẠO dòng mới. */
  row?: EmployeeWorkHistory | null
  /** Toàn bộ dòng đã có của hồ sơ — tìm dòng chính đang mở cho tick "Đóng dòng"
   *  VÀ cho `planApplyPrompt` nhận biết nhập bù lịch sử cũ (M6). */
  allRows: EmployeeWorkHistory[]
  /** Phòng kiêm nhiệm hiện tại — cho `planApplyPrompt` xét loại Kiêm nhiệm. */
  extraDeptIds: number[]
  /** A9 (Q4) — `false` thì ẨN vùng thả tệp (tạo mới) VÀ nút «Quản lý tệp» (sửa),
   *  không gọi API đính kèm (M4). */
  canOpenFiles: boolean
  /** Điền sẵn khi mở từ nút «Tạo dòng đầu từ hồ sơ». */
  seed?: Partial<EmployeeWorkHistoryFormValues>
}

/**
 * Hộp thêm/sửa một dòng «Quá trình công tác» — dựng ô nhập + hộp con, giao LƯU
 * + câu hỏi áp hồ sơ cho `useEmployeeWorkHistoryFormSubmit` (tách ra để mỗi
 * tệp dưới ~200 dòng, CLAUDE.md §"File Size Management").
 *
 * ⚠️ BẪY 1: hộp này nằm TRONG `<form>` của trang hồ sơ. `stopPropagation` ở
 * `<form onSubmit>` của tệp -fields xử cả bẫy 1 (bấm Lưu) lẫn bẫy 4 (Enter).
 */
export function EmployeeWorkHistoryFormDialog({
  open,
  onOpenChange,
  employeeId,
  employee,
  row,
  allRows,
  extraDeptIds,
  canOpenFiles,
  seed,
}: EmployeeWorkHistoryFormDialogProps) {
  const { can } = usePermission()
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: can('company', 'read') })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  const { data: positions } = useJobPositions(can('job_position', 'read'))

  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [filesDialogOpen, setFilesDialogOpen] = useState(false)

  const form = useForm<EmployeeWorkHistoryFormValues>({
    resolver: zodResolver(employeeWorkHistorySchema),
    defaultValues: EMPTY_EMPLOYEE_WORK_HISTORY_FORM,
  })

  useEffect(() => {
    if (!open) return
    form.reset(buildEmployeeWorkHistoryDefaultValues(employee, row, seed))
    setQueuedFiles([])
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ reset lúc MỞ/đổi dòng, không theo mọi đổi của `employee`/`seed`.
  }, [open, row])

  //  Chặn tại chỗ cho khỏi chờ tải hết một tệp quá cỡ rồi mới ăn 413 lúc tạo
  //  xong dòng (khuôn `leave-attachments-card.tsx::handleFiles`).
  function handleQueueFiles(picked: File[]) {
    const limit = WORK_HISTORY_FILE_MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0) {
      toast.error(`Vượt quá ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`)
    }
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) setQueuedFiles((prev) => [...prev, ...ok])
  }

  const eventType = form.watch('event_type')
  const fromDate = form.watch('from_date')
  const companyId = form.watch('company_id')
  const today = toDateInputValue(new Date())

  //  Dòng chính đang mở (khác dòng đang sửa) sớm hơn dòng mới → mời đóng lại.
  const openMainRow = useMemo(() => {
    if (row || !MAIN_TRACK.has(eventType) || !fromDate) return null
    return (
      allRows.find((r) => MAIN_TRACK.has(r.event_type) && !r.to_date && r.from_date < fromDate) ??
      null
    )
  }, [row, allRows, eventType, fromDate])

  const companyOptions: LookupItem[] = (companies?.items ?? []).map((c) => ({ id: c.id, label: c.name }))
  const departmentOptions: LookupItem[] = (departments?.items ?? [])
    .filter((d) => !companyId || !d.company_id || d.company_id === companyId)
    .map((d) => ({ id: d.id, label: d.name }))
  const positionOptions: LookupItem[] = (positions?.items ?? []).map((p) => ({ id: p.id, label: p.name }))

  const { saveMutation, onSubmit, pendingResign, setPendingResign, handleResignConfirm } =
    useEmployeeWorkHistoryFormSubmit({
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
    })

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{row ? 'Sửa quá trình công tác' : 'Thêm quá trình công tác'}</DialogTitle>
          </DialogHeader>

          <EmployeeWorkHistoryFormDialogFields
            form={form}
            onSubmit={onSubmit}
            companies={companyOptions}
            departments={departmentOptions}
            positions={positionOptions}
            openMainRow={openMainRow}
            eventType={eventType}
            fromDate={fromDate}
            today={today}
            editingRow={row ?? null}
            canOpenFiles={canOpenFiles}
            queuedFileCount={queuedFiles.length}
            onQueueFiles={handleQueueFiles}
            onOpenFilesDialog={() => setFilesDialogOpen(true)}
            footer={
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                  Hủy
                </Button>
                <Button type="submit" disabled={saveMutation.isPending}>
                  {saveMutation.isPending && <Loader2 className="size-4 animate-spin" />}
                  Lưu
                </Button>
              </DialogFooter>
            }
          />
        </DialogContent>
      </Dialog>

      {row && canOpenFiles && (
        <EmployeeWorkHistoryFilesDialog
          open={filesDialogOpen}
          onOpenChange={setFilesDialogOpen}
          historyId={row.id}
          employeeId={employeeId}
          editable
        />
      )}

      {pendingResign && (
        <EmployeeWorkHistoryResignConfirmDialog
          open
          onOpenChange={(next) => !next && setPendingResign(null)}
          resignDate={pendingResign.resignDate}
          pending={saveMutation.isPending}
          onConfirm={handleResignConfirm}
        />
      )}
    </>
  )
}
