import { useState } from 'react'

import { useEmployeeWorkHistory } from '../hooks/use-employee-work-history'
import { useEmployeeWorkHistoryEditorDialog } from '../hooks/use-employee-work-history-editor-dialog'
import { useEmployeeDepartments } from '../hooks/use-employees'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { APPOINT_TYPE } from '../utils/employee-work-history-apply'
import { EmployeeWorkHistoryDecisionSection } from './employee-work-history-decision-section'
import { EmployeeWorkHistoryFilesDialog } from './employee-work-history-files-dialog'
import { EmployeeWorkHistoryFormDialog } from './employee-work-history-form-dialog'

interface EmployeeTabWorkDecisionsProps {
  employee: EmployeeDetail
}

/**
 * Tab «Quyết định bổ nhiệm» ở hồ sơ nhân sự — TÁCH từ tab gộp cũ «Quá trình
 * công tác & Quyết định» thành tab RIÊNG (đại ca chốt 03/10/2026, xem báo cáo
 * `fullstack-developer-261003-1110-tach-hai-tab.md`). KHÔNG có nút Sửa/Xóa/Áp
 * (ghi vẫn làm ở tab «Quá trình công tác»), nhưng CÓ nút «+ Thêm quyết định»
 * (mục 3 — mở ĐÚNG hộp thêm/sửa dùng chung, loại mặc định Bổ nhiệm, Số QĐ bắt
 * buộc) — dùng CHUNG `useEmployeeWorkHistoryEditorDialog` với tab kia qua
 * `openCreate`, không chép logic điều phối hộp ra bản thứ hai.
 *
 * Dùng CHUNG khóa truy vấn `useEmployeeWorkHistory(employee.id)` với tab kia —
 * TanStack Query cache theo key (`staleTime` 30 giây, `core/api/query-client.ts`)
 * là đủ: chuyển tab qua lại trong 30 giây không gọi lại API, không cần nâng
 * dữ liệu lên component cha chỉ để chia sẻ. Lưu dòng mới từ hộp này cũng
 * `invalidateQueries` đúng khóa đó nên dòng xuất hiện ở CẢ HAI tab.
 *
 * Hộp tệp vẫn `editable={canEdit}` — khu này chỉ cấm SỬA DÒNG lịch sử (số QĐ,
 * ngày…), không cấm quản lý tệp đính kèm của dòng đó; cùng luật với hộp tệp ở
 * tab «Quá trình công tác».
 */
export function EmployeeTabWorkDecisions({ employee }: EmployeeTabWorkDecisionsProps) {
  const { data, isLoading, isError } = useEmployeeWorkHistory(employee.id)
  const { data: departments } = useEmployeeDepartments(employee.id)
  const [filesRow, setFilesRow] = useState<EmployeeWorkHistory | null>(null)
  const editor = useEmployeeWorkHistoryEditorDialog()

  const items = data?.items ?? []
  const canEdit = data?.can_edit ?? false
  const canOpenFiles = data?.can_open_files ?? false
  const extraDeptIds = departments?.extra_department_ids ?? []

  function openAddDecision() {
    editor.openCreate({ event_type: APPOINT_TYPE }, { requireDecisionNo: true, createTitle: 'Thêm quyết định bổ nhiệm' })
  }

  return (
    <div className="flex flex-col gap-5">
      <EmployeeWorkHistoryDecisionSection
        items={items}
        isLoading={isLoading}
        isError={isError}
        canOpenFiles={canOpenFiles}
        onOpenFiles={setFilesRow}
        storageKey="hr.employee-work-history-decisions"
        onAddClick={canEdit ? openAddDecision : undefined}
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
    </div>
  )
}
