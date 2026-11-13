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
import {
  toConcurrentCreatePayload,
  toConcurrentUpdatePayload,
  uploadConcurrentFiles,
} from '../api/employee-concurrent-api'
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
import { CONCURRENT_KIND_COMPANY, type EmployeeConcurrent } from '../types/employee-concurrent'
import { buildConcurrentCompanyOptions } from '../utils/concurrent-company-options'
import { buildConcurrentDepartmentOptions } from '../utils/concurrent-department-options'
import { EmployeeConcurrentFileField } from './employee-concurrent-file-field'
import { EmployeeConcurrentFilesDialog } from './employee-concurrent-files-dialog'
import { EmployeeConcurrentFormFields } from './employee-concurrent-form-fields'
import { WORK_HISTORY_FILE_MAX_SIZE_MB } from './employee-work-history-files-dialog'

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
    kind: row.kind,
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
 * Hộp thêm / sửa một dòng KIÊM NHIỆM (duoc-CR-755; hai loại dòng ở duoc-CR-756).
 *
 * Chọn **Loại** trước: *Phòng ban* — ô phòng CHỈ liệt kê phòng phục vụ công ty HIỆN TẠI của hồ sơ (phòng riêng, phòng
 * dùng chung, phòng nối qua `tab_department_company`), không có ô công ty (máy chủ điền công ty chính); *Công ty* — ô
 * công ty trừ công ty hiện tại, không có ô phòng. Sửa dòng thì Loại chỉ đọc. Đổi loại dọn ô của loại kia.
 *
 * ⚠️ Hộp nằm TRONG `<form>` của trang hồ sơ: `<form>` của hộp gọi `stopPropagation` trước `handleSubmit`, nên bấm Lưu
 * hay nhấn Enter trong ô của hộp KHÔNG submit form hồ sơ phía ngoài (bẫy 2 + bẫy 4 của biểu mẫu).
 * ⚠️ Chặn bấm đúp bằng `useRef` (đổi ngay trong tick); `disabled` chỉ để báo hiệu.
 * Ô Phòng ban lọc đúng luật L3 của backend — xem `buildConcurrentDepartmentOptions`.
 * Bố cục: thân hộp cuộn riêng (`max-h` theo màn hình), chân Hủy / Lưu dính đáy — một khung cuộn duy nhất vì hộp không
 * bao giờ cao hơn màn hình nên lớp phủ của `DialogContent` không còn gì để cuộn.
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
  const { data: companies } = useCompanies(
    { page_size: 200, is_active: true },
    { enabled: can('company', 'read') },
  )
  const { data: departments } = useDepartments(
    { page_size: 500, is_active: true },
    { enabled: canReadDepartment },
  )
  const { data: positions } = useJobPositions(can('job_position', 'read'))
  const save = useSaveEmployeeConcurrent(employee.id)

  const form = useForm<EmployeeConcurrentFormValues>({
    resolver: zodResolver(employeeConcurrentSchema),
    defaultValues: EMPTY_EMPLOYEE_CONCURRENT_FORM,
  })
  const primaryCompanyId = employee.company_id
  const { data: servedPairs } = useDepartmentsByCompanies(
    canReadDepartment && primaryCompanyId > 0 ? [primaryCompanyId] : [],
  )

  const submittingRef = useRef(false)
  const [queuedFiles, setQueuedFiles] = useState<File[]>([])
  const [filesOpen, setFilesOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    form.reset(toFormValues(row))
  }, [open, row, form])

  //  Tệp xếp hàng dọn lúc ĐÓNG hộp (mọi đường đóng đều qua đây) chứ không trong effect lúc mở — đặt state trong effect
  //  là một lượt vẽ thừa (luật `react-hooks/set-state-in-effect`).
  function close() {
    setQueuedFiles([])
    onOpenChange(false)
  }

  const departmentItems = departments?.items ?? []
  const companyItems = companies?.items ?? []
  const companyOptions = buildConcurrentCompanyOptions(
    companyItems,
    primaryCompanyId,
    row?.kind === CONCURRENT_KIND_COMPANY ? row.company_id : 0,
  )
  const departmentOptions = buildConcurrentDepartmentOptions(
    departmentItems,
    servedPairs ?? [],
    primaryCompanyId,
    { companyId: primaryCompanyId, departmentId: employee.department_id },
    row && row.kind !== CONCURRENT_KIND_COMPANY ? row.department_id : 0,
  )
  const primaryCompanyName =
    employee.company_name || companyItems.find((c) => c.id === primaryCompanyId)?.name || ''
  const positionOptions = (positions?.items ?? []).map((p) => ({ id: p.id, label: p.name }))

  //  Đổi loại: dọn ô nơi kiêm nhiệm của loại kia — không thì thân gửi đi vẫn đúng (chỉ ô của loại đang chọn được gửi)
  //  nhưng quay lại loại cũ sẽ thấy một giá trị người dùng tưởng đã bỏ.
  function handleKindChange(next: number) {
    form.setValue('kind', next)
    form.setValue('company_id', 0)
    form.setValue('department_id', 0)
    form.clearErrors(['company_id', 'department_id'])
  }

  function queueFiles(picked: File[]) {
    const limit = WORK_HISTORY_FILE_MAX_SIZE_MB * 1024 * 1024
    const tooBig = picked.filter((f) => f.size > limit)
    if (tooBig.length > 0)
      toast.error(
        `Vượt quá ${WORK_HISTORY_FILE_MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`,
      )
    const ok = picked.filter((f) => f.size <= limit)
    if (ok.length > 0) setQueuedFiles((prev) => [...prev, ...ok])
  }

  async function onSubmit(values: EmployeeConcurrentFormValues) {
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      const result = row
        ? await save.mutateAsync({ id: row.id, payload: toConcurrentUpdatePayload(values) })
        : await save.mutateAsync({ payload: toConcurrentCreatePayload(values) })
      if (!row && canOpenFiles && queuedFiles.length > 0) {
        void uploadConcurrentFiles(result.item.id, queuedFiles)
          .then(() =>
            queryClient.invalidateQueries({
              queryKey: queryKeys.hr.employeeConcurrents(employee.id),
            }),
          )
          .catch(() =>
            toast.error('Đã lưu dòng nhưng tải tệp QĐ lên thất bại — mở lại dòng để thử lại.'),
          )
      }
      close()
    } catch {
      //  Lỗi 400/403/409 đã có toast đúng câu backend (`httpClient`); giữ hộp mở để người dùng sửa.
    } finally {
      submittingRef.current = false
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={(next) => !save.isPending && (next ? onOpenChange(true) : close())}>
        <DialogContent className="flex max-h-[calc(100dvh-2rem)] flex-col gap-0 p-0 sm:max-w-2xl">
          <DialogHeader className="border-b px-6 pt-5 pb-4">
            <DialogTitle>{row ? 'Sửa kiêm nhiệm' : 'Thêm kiêm nhiệm'}</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form
              className="flex min-h-0 flex-1 flex-col"
              onSubmit={(event) => {
                event.stopPropagation()
                void form.handleSubmit(onSubmit)(event)
              }}
            >
              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-6 py-4">
                <EmployeeConcurrentFormFields
                  form={form}
                  kindLocked={Boolean(row)}
                  primaryCompanyName={primaryCompanyName}
                  companies={companyOptions}
                  departments={departmentOptions}
                  positions={positionOptions}
                  fallback={
                    row
                      ? {
                          company: row.company_name,
                          department: row.department_name,
                          position: row.position_label,
                        }
                      : undefined
                  }
                  onKindChange={handleKindChange}
                  fileField={
                    <EmployeeConcurrentFileField
                      editingRow={row}
                      canOpenFiles={canOpenFiles}
                      queuedFiles={queuedFiles}
                      onQueueFiles={queueFiles}
                      onRemoveQueued={(index) =>
                        setQueuedFiles((prev) => prev.filter((_, i) => i !== index))
                      }
                      onOpenFilesDialog={() => setFilesOpen(true)}
                    />
                  }
                />
              </div>
              <DialogFooter className="border-t px-6 py-3">
                <Button
                  type="button"
                  variant="outline"
                  disabled={save.isPending}
                  onClick={close}
                >
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
