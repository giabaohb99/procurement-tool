import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { useDeleteEmployeeWorkHistory, useEmployeeWorkHistory } from '../hooks/use-employee-work-history'
import { useEmployeeWorkHistoryEditorDialog } from '../hooks/use-employee-work-history-editor-dialog'
import { useBusyIds, useEmployeeWorkHistoryRowApply } from '../hooks/use-employee-work-history-row-apply'
import { useEmployeeDepartments } from '../hooks/use-employees'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryFilesDialog } from './employee-work-history-files-dialog'
import { EmployeeWorkHistoryFormDialog } from './employee-work-history-form-dialog'
import { EmployeeWorkHistoryMainSection } from './employee-work-history-main-section'
import { EmployeeWorkHistoryResignConfirmDialog } from './employee-work-history-resign-confirm-dialog'

interface EmployeeTabWorkHistoryProps {
  employee: EmployeeDetail
}

/** Khớp `WorkEventType.HIRE` — loại điền sẵn của nút «Tạo dòng đầu từ hồ sơ». */
const HIRE_TYPE = 1

/**
 * Tab «Quá trình công tác» ở hồ sơ nhân sự — TÁCH từ tab gộp cũ «Quá trình
 * công tác & Quyết định» thành tab RIÊNG (đại ca chốt 03/10/2026, xem báo cáo
 * `fullstack-developer-261003-1110-tach-hai-tab.md`): MỌI dòng,
 * Thêm/Áp/Sửa/Xóa như cũ, tự chuyển Bảng | Dòng thời gian (lưu vào URL `whView`).
 *
 * Khu «Quyết định bổ nhiệm» (chỉ dòng có số QĐ, chỉ đọc) nay là TAB RIÊNG —
 * `employee-tab-work-decisions.tsx` — dùng CHUNG khóa truy vấn
 * `useEmployeeWorkHistory(employee.id)` với component này; TanStack Query
 * cache theo key là đủ (`staleTime` 30 giây ở `query-client.ts`), không cần
 * nâng dữ liệu lên component cha chỉ để tránh gọi API hai lần.
 *
 * Được sửa / được mở tệp lấy từ cờ BACKEND trả (`can_edit`, `can_open_files`,
 * A9) — không tự ghép `can()` + so `employee_id`. Câu hỏi trước khi áp vào hồ
 * sơ (H1) nằm ở `use-employee-work-history-row-apply.ts`.
 */
export function EmployeeTabWorkHistory({ employee }: EmployeeTabWorkHistoryProps) {
  const { user } = useAuth()
  const { data, isLoading, isError } = useEmployeeWorkHistory(employee.id)
  const { data: departments } = useEmployeeDepartments(employee.id)
  const deleteMutation = useDeleteEmployeeWorkHistory(employee.id)
  const deleting = useBusyIds()

  const [filesRow, setFilesRow] = useState<EmployeeWorkHistory | null>(null)
  //  Điều phối hộp thêm/sửa NÂNG lên chỗ chung — tab «Quyết định bổ nhiệm»
  //  (`employee-tab-work-decisions.tsx`) dùng CHUNG hook này cho nút
  //  «+ Thêm quyết định», không chép logic chuyển trạng thái ra bản thứ hai.
  const editor = useEmployeeWorkHistoryEditorDialog()

  const items = data?.items ?? []
  const canEdit = data?.can_edit ?? false
  const canOpenFiles = data?.can_open_files ?? false
  const extraDeptIds = departments?.extra_department_ids ?? []
  //  Chỉ đúng "hồ sơ của chính bạn" khi id người đang đăng nhập khớp hồ sơ
  //  đang xem — `canEdit=false` còn xảy ra khi người xem chỉ thiếu quyền sửa
  //  hồ sơ CỦA NGƯỜI KHÁC, lúc đó câu "của chính bạn" là sai (Low FE).
  const isOwnProfile = Boolean(user?.employee_id) && user?.employee_id === employee.id

  const rowApply = useEmployeeWorkHistoryRowApply(employee.id, employee, extraDeptIds, items)

  const actions = canEdit
    ? {
        onEdit: editor.openEdit,
        onApply: rowApply.onApply,
        onDelete: (row: EmployeeWorkHistory) =>
          deleting.run(row.id, (done) => deleteMutation.mutate(row.id, { onSettled: done })),
        isApplying: rowApply.isApplying,
        isDeleting: (row: EmployeeWorkHistory) => deleting.ids.has(row.id),
      }
    : undefined

  return (
    <div className="flex flex-col gap-5">
      {!isLoading && !isError && !canEdit && isOwnProfile && (
        <p className="text-sm text-muted-foreground">
          Quá trình công tác của chính bạn do người khác cập nhật.
        </p>
      )}

      <EmployeeWorkHistoryMainSection
        items={items}
        isLoading={isLoading}
        isError={isError}
        errorMessage="Không tải được quá trình công tác."
        emptyMessage="Chưa có dòng quá trình công tác nào."
        canOpenFiles={canOpenFiles}
        onOpenFiles={setFilesRow}
        actions={actions}
        storageKey="hr.employee-work-history"
        onAddClick={canEdit ? () => editor.openCreate() : undefined}
        onCreateFromProfileClick={
          canEdit
            ? () =>
                editor.openCreate({
                  event_type: HIRE_TYPE,
                  from_date: employee.hire_date ?? '',
                  company_id: employee.company_id,
                  department_id: employee.department_id,
                  position_id: employee.position_id ?? 0,
                })
            : undefined
        }
      />

      <EmployeeWorkHistoryFormDialog
        open={editor.open}
        onOpenChange={editor.onOpenChange}
        employeeId={employee.id}
        employee={employee}
        row={editor.editRow}
        allRows={items}
        extraDeptIds={extraDeptIds}
        canOpenFiles={canOpenFiles}
        seed={editor.seed}
        requireDecisionNo={editor.requireDecisionNo}
        createTitle={editor.createTitle}
      />

      <EmployeeWorkHistoryFilesDialog
        open={Boolean(filesRow)}
        onOpenChange={(next) => !next && setFilesRow(null)}
        historyId={filesRow?.id ?? 0}
        employeeId={employee.id}
        editable={canEdit}
      />

      {rowApply.resignApply && (
        <EmployeeWorkHistoryResignConfirmDialog
          open
          onOpenChange={(next) => !next && rowApply.closeResignApply()}
          resignDate={rowApply.resignApply.resignDate}
          pending={rowApply.isApplying(rowApply.resignApply.row)}
          cancelLabel="Hủy"
          confirmLabel="Chuyển sang nghỉ việc"
          onCancel={rowApply.closeResignApply}
          onConfirm={rowApply.confirmResignApply}
        />
      )}
    </div>
  )
}
