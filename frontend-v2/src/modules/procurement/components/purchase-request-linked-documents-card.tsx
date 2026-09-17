import { ExternalLink, Link2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { useRelatedPurchaseOrders } from '../hooks/use-purchase-request-support'
import { PO_STATUS_LABELS, SR_STATUS_LABELS } from '../types/purchase-document'
import type { PurchaseRequestDetail } from '../types/purchase-request-detail'
import { StatusBadge } from './document-status-badge'

/**
 * bao-CR-422 — thẻ "Chứng từ liên quan" trên phiếu YCMH.
 *
 * Trước thẻ này, hai chiều liên kết của phiếu đều khó thấy: đường về YCBG chỉ là một
 * dòng chữ lẫn trong thẻ Thông tin chung và chỉ bày ĐƯỢC MỘT phiếu nguồn, còn danh
 * sách đơn mua hàng thì nấp sau một nút ở thanh lệnh — mà nút ấy TỰ ẨN khi chưa có
 * đơn nào, nên người dùng không có cách nào biết là nó tồn tại. Gom cả hai về một
 * thẻ đứng yên một chỗ: có thì bày ra, chưa có thì nói rõ là chưa có.
 *
 * Danh sách YCBG đi kèm sẵn trong phiếu (`survey_requests`), không tốn thêm lượt gọi.
 * Danh sách ĐMH phải hỏi riêng vì phiếu không mang theo, và chỉ hỏi khi người xem có
 * quyền đọc đơn mua hàng — người yêu cầu thường không có quyền đó, gọi vào chỉ ăn 403.
 */
/** Thẻ chỉ đọc hai trường của phiếu — khai đúng hai trường đó để dựng test khỏi phải
 *  bịa ra cả một phiếu đầy đủ. */
type LinkedDocumentsSource = Pick<PurchaseRequestDetail, 'code' | 'survey_requests'>

export function PurchaseRequestLinkedDocumentsCard({ data }: { data: LinkedDocumentsSource }) {
  const { can } = usePermission()
  const canReadSurveyRequest = can('survey_request', 'read')
  const canReadPurchaseOrder = can('purchase_order', 'read')

  const surveyRequests = data.survey_requests ?? []
  const {
    data: orderPage,
    isLoading: ordersLoading,
    isError: ordersError,
  } = useRelatedPurchaseOrders(canReadPurchaseOrder ? data.code : '')
  const orders = orderPage?.items ?? []

  return (
    <Card className="gap-4 py-4">
      {/* Cùng khuôn với các thẻ khác trên trang — xem ghi chú ở thẻ Thông tin chung. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <Link2 className="size-4" />
          Chứng từ liên quan
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 px-4">
        <section className="space-y-2">
          <h3 className="text-sm font-medium">Yêu cầu báo giá nguồn ({surveyRequests.length})</h3>
          {surveyRequests.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              Phiếu này lập tay, không sinh ra từ yêu cầu báo giá nào.
            </p>
          ) : (
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader className="bg-muted">
                  <TableRow>
                    <TableHead>Mã YCBG</TableHead>
                    <TableHead>Ngày yêu cầu</TableHead>
                    <TableHead>Người yêu cầu</TableHead>
                    <TableHead>Trạng thái</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {surveyRequests.map((surveyRequest) => (
                    <TableRow key={surveyRequest.id}>
                      <TableCell className="font-medium">
                        {/* Không có quyền đọc YCBG thì bày mã dạng chữ: bấm vào chỉ ăn 403. */}
                        {canReadSurveyRequest ? (
                          <Link
                            className="text-primary inline-flex items-center gap-1 hover:underline"
                            to={appRoutes.procurement.surveyRequestDetail(surveyRequest.id)}
                          >
                            {surveyRequest.code}
                            <ExternalLink className="size-3.5" />
                          </Link>
                        ) : (
                          surveyRequest.code
                        )}
                      </TableCell>
                      <TableCell>{formatDate(surveyRequest.request_date) || '—'}</TableCell>
                      <TableCell>{surveyRequest.requester || '—'}</TableCell>
                      <TableCell>
                        <StatusBadge status={surveyRequest.status} labels={SR_STATUS_LABELS} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>

        {canReadPurchaseOrder && (
          <section className="space-y-2">
            <h3 className="text-sm font-medium">Đơn mua hàng đã lập ({orders.length})</h3>
            {ordersLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : ordersError ? (
              <p className="text-muted-foreground text-sm">
                Chưa đọc được danh sách đơn mua hàng, thử tải lại trang.
              </p>
            ) : orders.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                Chưa có đơn mua hàng nào được lập từ phiếu này.
              </p>
            ) : (
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader className="bg-muted">
                    <TableRow>
                      <TableHead>Mã ĐMH</TableHead>
                      <TableHead>Ngày đặt</TableHead>
                      <TableHead>Nhà cung cấp</TableHead>
                      <TableHead className="text-right">Tổng tiền</TableHead>
                      <TableHead>Trạng thái</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => (
                      <TableRow key={order.id}>
                        <TableCell className="font-medium">
                          <Link
                            className="text-primary inline-flex items-center gap-1 hover:underline"
                            to={appRoutes.procurement.purchaseOrderDetail(order.id)}
                          >
                            {order.code}
                            <ExternalLink className="size-3.5" />
                          </Link>
                        </TableCell>
                        <TableCell>{formatDate(order.order_date) || '—'}</TableCell>
                        <TableCell>
                          {order.supplier_name || order.supplier_code || 'Chưa có NCC'}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatMoney(order.amount)} đ
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={order.status} labels={PO_STATUS_LABELS} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </section>
        )}
      </CardContent>
    </Card>
  )
}
