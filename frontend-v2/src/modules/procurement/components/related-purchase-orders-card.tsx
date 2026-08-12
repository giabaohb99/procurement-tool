import { ShoppingCart } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatMoney } from '@/shared/utils/format-money'
import { useRelatedPurchaseOrders } from '../hooks/use-purchase-request-support'
import { PO_STATUS_LABELS } from '../types/purchase-document'
import { StatusBadge } from './document-status-badge'

export function RelatedPurchaseOrdersCard({ purchaseRequestCode }: { purchaseRequestCode: string }) {
  const [open, setOpen] = useState(false)
  const { data, isLoading, isError } = useRelatedPurchaseOrders(purchaseRequestCode)
  const orders = data?.items ?? []

  if (isError || (!isLoading && orders.length === 0)) return null

  return (
    <>
      {isLoading ? (
        <Skeleton className="h-9 w-40" />
      ) : (
        <Button variant="outline" onClick={() => setOpen(true)}>
          <ShoppingCart />
          ĐMH liên quan ({orders.length})
        </Button>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>Đơn mua hàng liên quan ({orders.length})</DialogTitle>
            <DialogDescription>
              Các đơn mua hàng được tạo từ phiếu {purchaseRequestCode}.
            </DialogDescription>
          </DialogHeader>
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-muted">
                <TableRow>
                  <TableHead>Mã ĐMH</TableHead>
                  <TableHead>Nhà cung cấp</TableHead>
                  <TableHead className="text-right">Tổng tiền</TableHead>
                  <TableHead>Trạng thái</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">{order.code}</TableCell>
                    <TableCell>{order.supplier_name || order.supplier_code || 'Chưa có NCC'}</TableCell>
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
        </DialogContent>
      </Dialog>
    </>
  )
}
