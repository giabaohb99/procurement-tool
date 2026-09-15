import { ArrowLeft } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { PurchaseRequestProcessCard } from '../components/purchase-request-process-card'
import { usePurchaseRequest } from '../hooks/use-purchase-request'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import { isDispatched } from '../types/purchase-request-detail'
import { isPrOptionStageOpen } from '../types/purchase-request-options'

/**
 * Màn XỬ LÝ PHƯƠNG ÁN của YCMH (bao-CR-310) — vỏ trang, nhân khuôn màn xử lý
 * khảo sát của YCBG (CR-222). Nghiệp vụ nằm trong `PurchaseRequestProcessCard`.
 *
 * KHÔNG gác quyền cứng ở đây: người yêu cầu (không có quyền ghi YCMH) vẫn phải
 * vào được để CHỐT phương án, còn ai ngoài phạm vi thì chính truy vấn chi tiết
 * phiếu trả lỗi. Phiếu đã đóng vẫn mở được để xem lại phương án — backend chỉ
 * chặn GHI theo giai đoạn, không chặn xem.
 */
export function PurchaseRequestProcessPage() {
  const { id } = useParams()
  const purchaseRequestId = Number(id) || 0
  const navigate = useNavigate()

  const { data, isLoading, isError } = usePurchaseRequest(purchaseRequestId)

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
        <Button
          variant="outline"
          onClick={() => navigate(appRoutes.procurement.purchaseRequests)}
        >
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về chi tiết yêu cầu mua hàng">
          <Link to={appRoutes.procurement.purchaseRequestDetail(data.id)}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          Xử lý phương án — {data.code || `#${data.id}`}
        </h1>
        <StatusBadge status={data.status} labels={PR_STATUS_LABELS} />
      </div>

      <p className="mb-4 text-sm text-muted-foreground">
        Người yêu cầu: <b>{data.requester || '—'}</b> · Bộ phận: <b>{data.department || '—'}</b> ·
        Ngày lập: <b>{formatDate(data.request_date) || '—'}</b>
      </p>

      {isDispatched(data.status) ? (
        <>
          {!isPrOptionStageOpen(data.status) && (
            <Card className="mb-4 py-4">
              <CardContent className="px-4 text-sm text-muted-foreground">
                Phiếu đang ở trạng thái{' '}
                <b>{PR_STATUS_LABELS[data.status] ?? data.status}</b> — chỉ xem lại được phương
                án, không gắn / sửa / chốt thêm.
              </CardContent>
            </Card>
          )}
          <PurchaseRequestProcessCard purchaseRequest={data} />
        </>
      ) : (
        <Card className="py-4">
          <CardContent className="px-4 text-sm text-muted-foreground">
            Phiếu đang ở trạng thái <b>{PR_STATUS_LABELS[data.status] ?? data.status}</b> — chỉ
            gắn phương án được sau khi thu mua đã tiếp nhận phiếu (điều phối xong).
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
