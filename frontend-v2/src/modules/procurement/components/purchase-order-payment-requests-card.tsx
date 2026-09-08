import { ReceiptText } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
// Mượn hook + badge của phân hệ Tài chính (cùng tiền lệ với payment-dialog):
// khi cụm YCTT dời hẳn về v2 thì cân nhắc nâng lên shared.
import { PaymentRequestStatusBadge } from '@/modules/finance/components/payment-request-status-badge'
import { usePaymentRequests } from '@/modules/finance/hooks/use-payment-requests'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
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

/**
 * Khối "Yêu cầu thanh toán của đơn này" trên chi tiết ĐMH — trả lời đúng câu
 * người dùng hỏi sau khi bấm tạo YCTT: "phiếu vừa tạo nằm đâu, giờ làm gì tiếp?".
 *
 * Lọc bằng `po_code_exact` (khớp ĐÚNG mã đơn) chứ không dùng `po_code` — filter
 * cũ chạy LIKE nên PO-TREO-1 sẽ vơ nhầm cả phiếu của PO-TREO-10.
 * Không có phiếu nào / thiếu quyền đọc YCTT thì khối tự ẩn, không chiếm chỗ.
 */
export function PurchaseOrderPaymentRequestsCard({ poCode }: { poCode: string }) {
  const { can } = usePermission()
  const canRead = can('payment_request', 'read')
  const { data } = usePaymentRequests(
    { po_code_exact: poCode, page_size: 100 },
    { enabled: canRead && !!poCode },
  )
  const items = data?.items ?? []

  if (!canRead || !poCode || items.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <ReceiptText className="size-4 text-muted-foreground" />
          Yêu cầu thanh toán của đơn này
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Mã phiếu</TableHead>
              <TableHead>Ngày đề nghị</TableHead>
              <TableHead className="text-right">Số tiền</TableHead>
              <TableHead>Trạng thái</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((req) => (
              <TableRow key={req.id}>
                <TableCell>
                  <Link
                    className="font-medium text-primary hover:underline"
                    to={appRoutes.finance.paymentRequestDetail(req.id)}
                  >
                    {req.code}
                  </Link>
                  {req.prepay === 1 && (
                    <Badge variant="outline" className="ml-2 text-xs">
                      Trả trước
                    </Badge>
                  )}
                </TableCell>
                <TableCell>{formatDate(req.request_date)}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(req.total)} đ
                </TableCell>
                <TableCell>
                  <PaymentRequestStatusBadge status={req.status} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <p className="mt-2 text-xs text-muted-foreground">
          Phiếu Nháp cần vào chi tiết để Gửi duyệt; sau khi Duyệt và Ghi nhận đã chi thì công nợ
          của đơn mới được trừ.
        </p>
      </CardContent>
    </Card>
  )
}
