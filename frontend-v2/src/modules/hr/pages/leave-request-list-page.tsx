import { Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { UnifiedLeaveRequestTable } from '../components/unified-leave-request-table'

/**
 * ĐƠN NGHỈ PHÉP — Bảng duy nhất gom toàn bộ đơn trong phạm vi, việc cần duyệt
 * và lịch sử đã duyệt, kèm bộ lọc nhanh theo phạm vi và ưu tiên Chờ duyệt lên đầu.
 */
export function LeaveRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Đơn nghỉ phép"
        description={
          <span className="max-md:hidden">
            Nộp đơn, duyệt đơn của người khác và theo dõi số ngày phép còn lại.
          </span>
        }
        actions={
          can('leave_request', 'create') ? (
            <Button
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.leaveRequestNew)}
            >
              <Plus className="size-4" />
              Nộp đơn nghỉ phép
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
        <UnifiedLeaveRequestTable />
      </Card>
    </PageContainer>
  )
}
