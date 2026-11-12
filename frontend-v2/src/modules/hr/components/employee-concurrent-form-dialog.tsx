import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Form } from '@/shared/ui/form'
import { toConcurrentPayload, uploadConcurrentFiles } from '../api/employee-concurrent-api'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments, useDepartmentsByCompanies } from '../hooks/use-departments'
import { useSaveEmployeeConcurrent } from '../hooks/use-employee-concurrents'
import { useJobPositions } from '../hooks/use-job-positions'
import {
  EMPTY_EMPLOYEE_CONCURRENT_FORM,
  employeeConcurrentSchema,
  type EmployeeConcurrentFormValues,
} from '../schemas/employee-concurrent-schema'
import type { Employee } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { buildConcurrentDepartmentOptions } from '../utils/concurrent-department-options'
import { EmployeeConcurrentFilesDialog } from './employee-concurrent-files-dialog'
import { EmployeeConcurrentFormFields } from './employee-concurrent-form-fields'
import { WORK_HISTORY_FILE_MAX_SIZE_MB } from './employee-work-history-files-dialog'
import { EmployeeWorkHistoryFileField } from './employee-work-history-form-dialog-file-field'

interface EmployeeConcurrentFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  employee: Employee
  /** `null` = thêm dòng mới. */
  row: EmployeeConcurrent | null
  canOpenFiles: boolean
}

function toFormValues(row: EmployeeConcurrent | null): EmployeeConcurrentFormValues {
  if (!row) return EMPTY_EMPLOYEE_CONCURRENT_FORM
  return {
    company_id: row.company_id,
    department_id: row.department_id,
    position_id: row.position_id,
    from_date: row.from_date ?? '',
    to_date: row.to_date ?? '',
    decision_no: row.decision_no,
    decision_date: row.decision_date ?? '',
    note: row.note,
    counts_scope: row.counts_scope,
  }
}

/**
 * Hộp thêm / sửa một dòng KIÊM NHIỆM (duoc-CR-755).
 *
 * ⚠️ Hộp nằm TRONG `<form>` của trang hồ sơ: `<form>` của hộp gọi `stopPropagation` trước `handleSubmit`, nên bấm Lưu
 * hay nhấn Enter trong ô của hộp KHÔNG submit form hồ sơ phía ngoài (bẫy 2 + bẫy 4 của biểu mẫu).
 * ⚠️ Chặn bấm đúp bằng `useRef` (đổi ngay trong tick); `disabled` chỉ để báo hiệu.
 * Ô Phòng ban lọc theo công ty đang chọn đúng luật L3 của backend — xem `buildConcurrentDepartmentOptions`.
 */
export function EmployeeConcurrentFormDialog({
  open,
  onOpenChange,
  employee,
  row,
  canOpenFiles,
}: EmployeeConcurrentFormDialogProps) {
  const { can } = usePermission()
  const queryClient = useQueryClient()
  const canReadDepartment = can('department', 'read')
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: can('company', 'read') })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true }, { enabled: canReadDepartment })
  const { data: positions } = useJobPositions(can('job_position', 'read'))
  const save = useSaveEmployeeConcurrent(employee.id)

  const form = useForm<EmployeeConcurrentFormValues>({
    resolver: zodResolver(employeeConcurrentSchema),
    defaultValues: EMPTY_EMPLOYEE_CONCURRENT_FORM,
  })
  const companyId = form.watch('company_id')
  const { data: servedPairs } = useDepartmentsByCompanies(canReadDepartment && companyId > 0 ? [companyId] : [])

  const submittingRef = useRef(false)
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [filesOpen, setFilesOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    form.reset(toFormValues(row))
    setQueuedFiles([])
  }, [open, row, form])

  const departmentItems = departments?.items ?? []
  const companyOptions = (companies?.items ?? []).map((c) => ({ id: c.id, label: c.name }))
  const departmentOptions = buildConcurrentDepartmentOptions(
    departmentItems,
    servedPairs ?? [],
    companyId,
    { companyId: employee.company_id, departmentId: employee.department_id },
    row?.company_id === companyId ? row.department_id : 0,
  )
  const positionOptions = (positions?.items ?? []).map((p) => ({ id: p.id, label: p.name }))

  //  Đổi công ty: phòng DÙNG CHUNG vẫn phục vụ công ty mới nên giữ; phòng riêng của công ty cũ thì dọn để người dùng
  //  không lưu một cặp mà backend chắc chắn trả 400.
  function handleCompanyChange(next: number) {
    form.setValue('company_id', next, { shouldValidate: form.formState.isSubmitted })
    const currentDept = form.getValues('department_id')
    const shared = departmentItems.some((d) => d.id === currentDept && d.company_id === 0)
    if (currentDept && !shared) form.setValue('department_id', 0)
  }

  function queueFiles(picked: File[]) {
    const limit = WORK_HISTORY_FILE_MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0) toast.error(`Vượt quá ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`)
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) setQueuedFiles((prev) => [...prev, ...ok])
  }

  async function onSubmit(values: EmployeeConcurrentFormValues) {
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      const result = await save.mutateAsync({ id: row?.id, payload: toConcurrentPayload(values) })
      if (!row && canOpenFiles && queuedFiles.length > 0) {
        void uploadConcurrentFiles(result.item.id, queuedFiles)
          .then(() => queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeConcurrents(employee.id) }))
          .catch(() => toast.error('Đã lưu dòng nhưng tải tệp QĐ lên thất bại — mở lại dòng để thử lại.'))
      }
      onOpenChange(false)
    } catch {
      //  Lỗi 400/403/409 đã có toast đúng câu backend (`httpClient`); giữ hộp mở để người dùng sửa.
    } finally {
      submittingRef.current = false
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={(next) => !save.isPending && onOpenChange(next)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{row ? 'Sửa kiêm nhiệm' : 'Thêm kiêm nhiệm'}</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.stopPropagation()
                void form.handleSubmit(onSubmit)(event)
              }}
            >
              <EmployeeConcurrentFormFields
                form={form}
                companies={companyOptions}
                departments={departmentOptions}
                positions={positionOptions}
                fallback={row ? { company: row.company_name, department: row.department_name, position: row.position_label } : undefined}
                onCompanyChange={handleCompanyChange}
              />
              <EmployeeWorkHistoryFileField
                editingRow={row}
                canOpenFiles={canOpenFiles}
                queuedFileCount={queuedFiles.length}
                onQueueFiles={queueFiles}
                onOpenFilesDialog={() => setFilesOpen(true)}
              />
              <DialogFooter>
                <Button type="button" variant="outline" disabled={save.isPending} onClick={() => onOpenChange(false)}>
                  Hủy
                </Button>
                <Button type="submit" disabled={save.isPending}>
                  {save.isPending && <Loader2 className="size-4 animate-spin" />}
                  Lưu
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {row && canOpenFiles && (
        <EmployeeConcurrentFilesDialog
          open={filesOpen}
          onOpenChange={setFilesOpen}
          concurrentId={row.id}
          employeeId={employee.id}
          editable
        />
      )}
    </>
  )
}
