import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { EmployeeWorkHistoryDecisionSection } from '@/modules/hr/components/employee-work-history-decision-section'
import { EmployeeWorkHistoryFilesDialog } from '@/modules/hr/components/employee-work-history-files-dialog'
import { useMyWorkHistory } from '@/modules/hr/hooks/use-employee-work-history'
import type { EmployeeWorkHistory } from '@/modules/hr/types/employee-work-history'

/**
 * TAB CHÍNH «Quyết định bổ nhiệm» của Trang cá nhân (đại ca chốt 03/10/2026 —
 * trước đó là tab con lồng trong thẻ cuối tab «Thông tin cá nhân», không ai
 * thấy). Dùng lại đúng `EmployeeWorkHistoryDecisionSection` của tab hồ sơ, CHỈ
 * ĐỌC ở cả hai nơi (không nhận `onAddInWorkHistoryClick` — tab này của Trang
 * cá nhân không có chỗ nào để nhảy sang vì «Quá trình công tác» ở đây cũng
 * chỉ đọc).
 *
 * Gọi CHUNG `useMyWorkHistory` với `profile-work-history-tab.tsx` — khu này
 * tự lọc dòng có `decision_no`, KHÔNG gọi API riêng.
 *
 * Chỉ dựng khi tài khoản đã gắn hồ sơ nhân sự — gác ở nơi gọi
 * (`profile-page.tsx`, cùng luật với `ProfileLeaveCard`/`ProfileEmergencyContacts`).
 */
export function ProfileWorkDecisionsTab() {
  const { user } = useAuth()
  const { data, isLoading, isError } = useMyWorkHistory()
  const [filesRow, setFilesRow] = useState<EmployeeWorkHistory | null>(null)
  const items = data?.items ?? []
  //  Tab này chỉ dựng khi tài khoản đã gắn hồ sơ (gác ở `profile-page.tsx`),
  //  nên `employee_id` luôn có; `?? 0` chỉ để khớp kiểu, không phải nhánh thật.
  const employeeId = user?.employee_id ?? 0

  return (
    <>
      <EmployeeWorkHistoryDecisionSection
        items={items}
        isLoading={isLoading}
        isError={isError}
        canOpenFiles
        onOpenFiles={setFilesRow}
        storageKey="me.work-history-decisions"
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
