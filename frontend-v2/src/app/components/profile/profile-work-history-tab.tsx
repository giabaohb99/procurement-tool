import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { EmployeeWorkHistoryFilesDialog } from '@/modules/hr/components/employee-work-history-files-dialog'
import { EmployeeWorkHistoryMainSection } from '@/modules/hr/components/employee-work-history-main-section'
import { useMyWorkHistory } from '@/modules/hr/hooks/use-employee-work-history'
import type { EmployeeWorkHistory } from '@/modules/hr/types/employee-work-history'

/**
 * TAB CHÍNH «Quá trình công tác» của Trang cá nhân (đại ca chốt 03/10/2026 —
 * trước đó là tab con lồng trong thẻ cuối tab «Thông tin cá nhân», không ai
 * thấy). Dùng lại đúng `EmployeeWorkHistoryMainSection` của tab hồ sơ, CHỈ
 * ĐỌC: không truyền `actions`/`onAddClick`/`onCreateFromProfileClick` nên
 * không có nút Thêm/Sửa/Xóa/Áp, ở cả dạng Bảng lẫn Dòng thời gian.
 *
 * Đọc qua `GET /api/employees/me/work-history` (`useMyWorkHistory`) — KHÔNG
 * gọi `/{eid}/work-history`, người không có `employee.read` sẽ ăn 403 ngay
 * lúc mở Trang cá nhân. Tab «Quyết định bổ nhiệm»
 * (`profile-work-decisions-tab.tsx`) gọi CHUNG hook này — TanStack Query cache
 * theo khóa, nên chuyển qua lại không gọi lại API; `Tabs` của Radix cũng chỉ
 * mount một tab tại một thời điểm.
 *
 * Chỉ dựng khi tài khoản đã gắn hồ sơ nhân sự — gác ở nơi gọi
 * (`profile-page.tsx`, cùng luật với `ProfileLeaveCard`/`ProfileEmergencyContacts`).
 */
export function ProfileWorkHistoryTab() {
  const { user } = useAuth()
  const { data, isLoading, isError } = useMyWorkHistory()
  const [filesRow, setFilesRow] = useState<EmployeeWorkHistory | null>(null)
  const items = data?.items ?? []
  //  Tab này chỉ dựng khi tài khoản đã gắn hồ sơ (gác ở `profile-page.tsx`),
  //  nên `employee_id` luôn có; `?? 0` chỉ để khớp kiểu, không phải nhánh thật.
  const employeeId = user?.employee_id ?? 0

  return (
    <>
      <EmployeeWorkHistoryMainSection
        items={items}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Chưa có quá trình công tác nào được ghi. Phòng Nhân sự cập nhật mục này."
        canOpenFiles
        onOpenFiles={setFilesRow}
        storageKey="me.work-history"
      />

      {/*  Chỉ xem (`editable={false}`): không vùng thả, không nút gỡ tệp; nút
           xem/tải vẫn hiện vì chính chủ luôn mở được tệp của mình. */}
      <EmployeeWorkHistoryFilesDialog
        open={Boolean(filesRow)}
        onOpenChange={(next) => !next && setFilesRow(null)}
        historyId={filesRow?.id ?? 0}
        employeeId={employeeId}
        editable={false}
      />
    </>
  )
}
