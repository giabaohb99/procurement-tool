import { useState } from 'react'

import { useEmployeeWorkHistory } from '../hooks/use-employee-work-history'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryDecisionSection } from './employee-work-history-decision-section'
import { EmployeeWorkHistoryFilesDialog } from './employee-work-history-files-dialog'

interface EmployeeTabWorkDecisionsProps {
  employee: EmployeeDetail
  /**
   * Bấm nút gợi ý lúc rỗng (chỉ hiện khi `can_edit`) thì NHẢY sang tab «Quá
   * trình công tác» — nơi gọi (`employee-detail-page.tsx`) đổi `tab` qua
   * `useUrlParamState`.
   */
  onGoToWorkHistoryClick: () => void
}

/**
 * Tab «Quyết định bổ nhiệm» ở hồ sơ nhân sự — TÁCH từ tab gộp cũ «Quá trình
 * công tác & Quyết định» thành tab RIÊNG (đại ca chốt 03/10/2026, xem báo cáo
 * `fullstack-developer-261003-1110-tach-hai-tab.md`). CHỈ ĐỌC: không có nút
 * Thêm/Sửa/Xóa/Áp — ghi vẫn làm ở tab «Quá trình công tác»
 * (`employee-tab-work-history.tsx`).
 *
 * Dùng CHUNG khóa truy vấn `useEmployeeWorkHistory(employee.id)` với tab kia —
 * TanStack Query cache theo key (`staleTime` 30 giây, `core/api/query-client.ts`)
 * là đủ: chuyển tab qua lại trong 30 giây không gọi lại API, không cần nâng
 * dữ liệu lên component cha chỉ để chia sẻ.
 *
 * Hộp tệp vẫn `editable={canEdit}` — khu này chỉ cấm SỬA DÒNG lịch sử (số QĐ,
 * ngày…), không cấm quản lý tệp đính kèm của dòng đó; cùng luật với hộp tệp ở
 * tab «Quá trình công tác».
 */
export function EmployeeTabWorkDecisions({ employee, onGoToWorkHistoryClick }: EmployeeTabWorkDecisionsProps) {
  const { data, isLoading, isError } = useEmployeeWorkHistory(employee.id)
  const [filesRow, setFilesRow] = useState<EmployeeWorkHistory | null>(null)

  const items = data?.items ?? []
  const canEdit = data?.can_edit ?? false
  const canOpenFiles = data?.can_open_files ?? false

  return (
    <div className="flex flex-col gap-5">
      <EmployeeWorkHistoryDecisionSection
        items={items}
        isLoading={isLoading}
        isError={isError}
        canOpenFiles={canOpenFiles}
        onOpenFiles={setFilesRow}
        storageKey="hr.employee-work-history-decisions"
        onAddInWorkHistoryClick={canEdit ? onGoToWorkHistoryClick : undefined}
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
