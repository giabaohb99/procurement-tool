import { ArrowLeft } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { SurveyRequestProcessCard } from '../components/survey-request-process-card'
import { useSurveyRequest } from '../hooks/use-survey-request'
import { SR_STATUS_LABELS } from '../types/purchase-document'
import { isSurveyRequestProcessable } from '../types/survey-request-process'

/**
 * Màn XỬ LÝ KHẢO SÁT riêng cho NSTM — dựng lại theo yêu cầu 29/08: bản v2 từng
 * gộp khu xử lý vào trang chi tiết YCBG (QĐ `doc/erp/12` mục 2.7), nhưng khách
 * muốn giữ thói quen bản v1 là một trang riêng. Toàn bộ nghiệp vụ nằm trong
 * `SurveyRequestProcessCard` dùng chung; trang này chỉ là vỏ: đầu phiếu + quyền.
 */
export function SurveyRequestProcessPage() {
  const { id } = useParams()
  const surveyRequestId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()

  const { data, isLoading, isError } = useSurveyRequest(surveyRequestId)

  if (!can('survey_request', 'process')) {
    return (
      <ErrorState
        title="Không có quyền xử lý khảo sát"
        description="Màn này dành cho nhân sự thu mua được gán quyền xử lý Yêu cầu báo giá."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.surveyRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        title="Không mở được phiếu"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.surveyRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về chi tiết yêu cầu báo giá">
          <Link to={appRoutes.procurement.surveyRequestDetail(data.id)}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          Xử lý khảo sát — {data.code || `#${data.id}`}
        </h1>
        <StatusBadge status={data.status} labels={SR_STATUS_LABELS} />
      </div>

      <p className="mb-4 text-sm text-muted-foreground">
        Người yêu cầu: <b>{data.requester || '—'}</b> · Bộ phận: <b>{data.department || '—'}</b> ·
        Ngày yêu cầu: <b>{formatDate(data.request_date) || '—'}</b>
      </p>

      {isSurveyRequestProcessable(data.status) ? (
        <SurveyRequestProcessCard surveyRequestId={data.id} status={data.status} />
      ) : (
        <Card className="py-4">
          <CardContent className="px-4 text-sm text-muted-foreground">
            Phiếu đang ở trạng thái{' '}
            <b>{SR_STATUS_LABELS[data.status] ?? data.status}</b> — chỉ xử lý khảo sát được khi
            phiếu <b>Đang xử lý</b> hoặc <b>Đã khảo sát</b>.
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
