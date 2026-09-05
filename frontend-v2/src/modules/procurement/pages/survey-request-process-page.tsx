import { ArrowLeft, Printer, ShoppingCart } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { SurveyRequestProcessCard } from '../components/survey-request-process-card'
import { useCreatePurchaseOrdersFromSurvey, useSurveyRequest } from '../hooks/use-survey-request'
import { useSurveyRequestProcess } from '../hooks/use-survey-request-process'
import { SR_STATUS_LABELS } from '../types/purchase-document'
import { LINE_STATUS_CONFIRMED } from '../types/survey-request-detail'
import { isSurveyRequestProcessable } from '../types/survey-request-process'

/** P6-3 (bao-CR-281): từ trạng thái này trở đi mới tạo thẳng ĐMH được (khớp gác backend). */
const CREATE_PO_STATUSES = ['processing', 'survey_done', 'pr_created', 'done']

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
  // bao-CR-290: khung xử lý là nơi DUY NHẤT biết dòng nào người đang xem được phân
  // phối (`can_process` do backend tính, gồm cả NSTM phụ của phân loại). Chi tiết
  // phiếu không mang cờ đó, nên nút "Tạo đơn mua hàng" phải đếm từ đây.
  const processQuery = useSurveyRequestProcess(surveyRequestId, can('survey_request', 'process'))
  const createPurchaseOrders = useCreatePurchaseOrdersFromSurvey(surveyRequestId)
  const [confirmCreatePos, setConfirmCreatePos] = useState(false)

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

  /**
   * Số dòng đã chốt phương án MÀ người đang xem được phân phối — nguồn của nút
   * "Tạo đơn mua hàng". bao-CR-290: trước đây đếm mọi dòng đã chốt, nên NSTM này
   * lên đơn được cho dòng của NSTM khác (backend nay cũng chặn).
   */
  const confirmedCount = (processQuery.data?.lines ?? []).filter(
    (line) => line.can_process && line.line_status === LINE_STATUS_CONFIRMED,
  ).length

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

        <div className="min-w-4 flex-1" />
        {/* P6-9 (bao-CR-287): bộ bản in tách theo NCC cho thu mua — backend gác
            `supplier.read` nên nút cũng ẩn theo, người yêu cầu không thấy bản này. */}
        {can('supplier', 'read') && (
          <Button variant="outline" asChild>
            <Link
              to={appRoutes.procurement.surveyRequestPurchasingPrint(data.id)}
              target="_blank"
              rel="noreferrer"
            >
              <Printer />
              In theo NCC
            </Link>
          </Button>
        )}
        {/* P6-3 (bao-CR-281): tạo THẲNG đơn mua hàng từ các dòng người YC đã chốt
            phương án — bỏ bước YCMH trung gian. Chỉ hiện với người tạo được ĐMH.
            P6-8 (bao-CR-286): cờ luồng gộp TẮT thì ẩn luôn — backend cũng chặn 400.
            bao-CR-290: ẩn hẳn khi không có dòng đã chốt NÀO thuộc phần mình phụ
            trách — nút này là việc của NSTM được phân phối, không phải của mọi
            người có quyền tạo ĐMH. */}
        {data.merged_flow_enabled &&
          CREATE_PO_STATUSES.includes(data.status) &&
          can('purchase_order', 'create') &&
          confirmedCount > 0 && (
          <Button
            disabled={createPurchaseOrders.isPending}
            onClick={() => setConfirmCreatePos(true)}
          >
            <ShoppingCart />
            Tạo đơn mua hàng ({confirmedCount} dòng đã chốt)
          </Button>
        )}
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

      <AlertDialog open={confirmCreatePos} onOpenChange={setConfirmCreatePos}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Tạo đơn mua hàng?</AlertDialogTitle>
            <AlertDialogDescription>
              Tạo thẳng đơn mua hàng (nháp) từ {confirmedCount} dòng đã chốt phương án, gom theo
              nhà cung cấp — không qua bước Yêu cầu mua hàng. Giá, VAT, thời gian giao lấy từ
              phương án đã chốt.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                void createPurchaseOrders.mutateAsync()
                setConfirmCreatePos(false)
              }}
            >
              Đồng ý
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageContainer>
  )
}
