import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PO_STATUS_LABELS, type PurchaseOrder } from '../types/purchase-document'
import { StatusBadge } from './document-status-badge'

/** Thẻ chỉ đọc sáu trường của đơn — khai đúng sáu trường để bài kiểm khỏi bịa cả một đơn. */
export type LinkedPurchaseOrder = Pick<
  PurchaseOrder,
  'id' | 'code' | 'supplier_name' | 'supplier_code' | 'order_date' | 'amount' | 'status'
>

/**
 * Một ĐƠN MUA HÀNG lập từ phiếu YCMH, ở khổ điện thoại — thay cho bảng 5 cột của thẻ
 * *Chứng từ liên quan*.
 *
 * ⚠️ **NCC lên dòng đầu**: một YCMH đẻ nhiều ĐMH chủ yếu vì CHIA THEO NCC, nên tên NCC
 * là thứ phân biệt các đơn; mã ĐMH tụt xuống dòng phụ và vẫn là liên kết sang đơn.
 * Tổng tiền in đủ chữ số, không rút gọn — người đọc đối chiếu với tổng của phiếu.
 */
export function LinkedPurchaseOrderCard({ order }: { order: LinkedPurchaseOrder }) {
  return (
    <div className="space-y-1.5 p-3">
      <p className="font-medium break-words text-foreground">
        {order.supplier_name || order.supplier_code || 'Chưa có NCC'}
      </p>

      <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <Link
          className="inline-flex items-center gap-1 font-medium text-sky-600 hover:underline dark:text-sky-400"
          to={appRoutes.procurement.purchaseOrderDetail(order.id)}
        >
          {order.code}
          <ExternalLink className="size-3.5" />
        </Link>
        {order.order_date && (
          <span>
            <span aria-hidden="true">· </span>
            {formatDate(order.order_date)}
          </span>
        )}
      </p>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <StatusBadge status={order.status} labels={PO_STATUS_LABELS} />
        <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
          {formatMoney(order.amount)} đ
        </span>
      </div>
    </div>
  )
}
