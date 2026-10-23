import { ArrowLeft, Hash, Info, TriangleAlert, UserRound } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard } from '@/shared/ui/record-identity-card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { ChangeRequestDecisionActions } from '../components/change-request-decision-actions'
import { ChangeRequestDiffTable } from '../components/change-request-diff-table'
import { ChangeRequestFamiliesDiff } from '../components/change-request-families-diff'
import { ChangeRequestSummaryCard } from '../components/change-request-summary-card'
import { EmployeeChangeRequestStatusBadge } from '../components/employee-change-request-status-badge'
import { CHANGE_REQUEST_GROUP_LABELS } from '../config/employee-profile-fields'
import { useChangeRequest } from '../hooks/use-employee-change-requests'
import type { ChangeRequestGroup, EmployeeChangeRequest } from '../types/employee-change-request'
import { CHANGE_REQUEST_STATUS } from '../utils/employee-change-request-status'
import { describeWhyCannotDecide } from '../utils/employee-change-request-review'

const GROUPS: readonly ChangeRequestGroup[] = ['personal', 'bank', 'documents']

/**
 * Chi tiết MỘT đề nghị sửa hồ sơ (duoc-CR-676) — phòng Nhân sự đối chiếu rồi Duyệt / Từ chối.
 *
 * Bảng so sánh theo từng nhóm: Trường · Lúc gửi · Hiện tại · Đề nghị. Duyệt là GHI ĐÈ cột «Đề
 * nghị» lên hồ sơ, nên dòng nào hồ sơ đã bị sửa sau lúc gửi thì tô lên cho người duyệt thấy.
 *
 * Hai nút chỉ hiện khi backend báo `can_decide`; đang chờ mà không bấm được thì nói lý do (tự
 * duyệt đề nghị của mình · thiếu quyền nhạy cảm) thay vì để trống chỗ nút.
 */
export function ProfileChangeRequestDetailPage() {
  const { id } = useParams()
  const requestId = Number(id) || 0
  const navigate = useNavigate()
  const { data: request, isLoading, isError } = useChangeRequest(requestId)

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-24 w-full" />
        <Skeleton className="h-80 w-full" />
      </PageContainer>
    )
  }

  if (isError || !request) {
    return (
      <ErrorState
        title="Không tìm thấy đề nghị"
        description="Đề nghị không tồn tại, hoặc hồ sơ nằm ngoài phạm vi bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.hr.profileChangeRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return <ChangeRequestDetailView request={request} />
}

/** Phần thân khi đã có dữ liệu — tách ra để test không phải dựng router + query chi tiết. */
export function ChangeRequestDetailView({ request }: { request: EmployeeChangeRequest }) {
  const { user } = useAuth()
  const { can } = usePermission()
  const [decisionError, setDecisionError] = useState('')

  const showActions = request.status === CHANGE_REQUEST_STATUS.PENDING && request.can_decide
  const blockedReason = describeWhyCannotDecide(request, {
    employeeId: user?.employee_id ?? 0,
    canReadSensitive: can('employee_sensitive', 'read'),
  })
  const groups = GROUPS.map((group) => ({
    group,
    items: request.items.filter((item) => item.group === group),
  })).filter((entry) => entry.items.length > 0)

  return (
    <PageContainer>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={appRoutes.hr.profileChangeRequests}>
            <ArrowLeft />
            Duyệt sửa hồ sơ
          </Link>
        </Button>
        {showActions && (
          <ChangeRequestDecisionActions request={request} onDecisionError={setDecisionError} />
        )}
      </div>

      {decisionError && (
        <p
          role="alert"
          className="mb-5 flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm"
        >
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
          <span>
            <span className="font-medium text-destructive">Chưa xử lý được: </span>
            {decisionError}
          </span>
        </p>
      )}

      <RecordIdentityCard
        title={request.employee_name || 'Nhân sự'}
        chips={[
          { icon: Hash, text: request.employee_code, tone: 'code' },
          { icon: UserRound, text: `Gửi bởi ${request.created_by_name || request.employee_name}` },
        ]}
        chipsSuffix={<EmployeeChangeRequestStatusBadge status={request.status} />}
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link to={appRoutes.hr.employeeDetail(request.employee_id)}>Mở hồ sơ nhân sự</Link>
          </Button>
        }
      />

      {blockedReason && (
        <p
          role="note"
          className="mb-5 flex items-start gap-2 rounded-md border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground"
        >
          <Info className="mt-0.5 size-4 shrink-0" />
          {blockedReason}
        </p>
      )}

      <ChangeRequestSummaryCard request={request} />

      <div className="flex flex-col gap-5">
        {groups.map(({ group, items }) => (
          <Card key={group} className="gap-3 p-5">
            <SectionHeading>{CHANGE_REQUEST_GROUP_LABELS[group]}</SectionHeading>
            <ChangeRequestDiffTable items={items} />
          </Card>
        ))}
        {request.families && (
          <Card className="gap-3 p-5">
            <SectionHeading>{CHANGE_REQUEST_GROUP_LABELS.families}</SectionHeading>
            <ChangeRequestFamiliesDiff families={request.families} />
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
