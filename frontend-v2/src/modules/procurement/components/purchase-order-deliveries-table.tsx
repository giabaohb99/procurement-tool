import { Trash2 } from 'lucide-react'

import type { Supplier } from '@/modules/production/types/supplier'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import { usePurchaseRequestWarehouses } from '../hooks/use-purchase-request-support'
import { PurchaseOrderDeliveryFiles } from './purchase-order-delivery-files'
import type {
  PurchaseOrderDelivery,
  PurchaseOrderItem,
} from '../types/purchase-order-detail'

/** Đơn vị tính của cước vận chuyển — cố định theo nghiệp vụ, không lấy từ danh mục ĐVT. */
const SHIP_UNITS = ['Kiện', 'Chuyến', 'm2', 'tấn'] as const

/** Giá trị giả cho lựa chọn "NCC tự vận chuyển" (không có mã trong danh mục). */
const SELF_CARRIER = '__self__'

interface PurchaseOrderDeliveriesTableProps {
  item: PurchaseOrderItem
  /** Đơn đã duyệt + có quyền ghi thì mới nhập được tiến độ giao. */
  editable: boolean
  /** Đơn vị vận chuyển (`supplier_type = 'transport'`). */
  carriers: Supplier[]
  /** Cho gắn/xóa tệp của lần giao — mở cả khi đơn đã hoàn thành. */
  attachEditable: boolean
  purchaseOrderId: number
  onChange: (deliveries: PurchaseOrderDelivery[]) => void
}

/**
 * Bảng các LẦN GIAO của một dòng hàng: nhận hàng nhiều đợt, mỗi đợt có số hóa
 * đơn, cước vận chuyển và công nợ riêng.
 *
 * Các cột ngày lệch (Ngày QĐ, Trễ CK/QĐ) và công nợ (Đã trả / Còn lại) do
 * BACKEND tính — hiện chỉ đọc, sửa tay ở đây sẽ lệch với sổ công nợ.
 */
export function PurchaseOrderDeliveriesTable({
  item,
  editable,
  carriers,
  attachEditable,
  purchaseOrderId,
  onChange,
}: PurchaseOrderDeliveriesTableProps) {
  const { data: warehouses } = usePurchaseRequestWarehouses()
  const deliveries = item.deliveries ?? []

  const patch = (index: number, changes: Partial<PurchaseOrderDelivery>) =>
    onChange(
      deliveries.map((delivery, current) =>
        current === index ? { ...delivery, ...changes } : delivery,
      ),
    )

  function pickCarrier(index: number, value: string) {
    if (value === SELF_CARRIER) {
      patch(index, { carrier_code: '', carrier_name: 'NCC tự vận chuyển' })
      return
    }
    const carrier = carriers.find((option) => option.code === value)
    patch(index, { carrier_code: value, carrier_name: carrier?.name ?? '' })
  }

  return (
    // `min-w-0`: bảng rộng 2400px nằm trong hộp thoại — thiếu nó thì mục lưới cha
    // nở theo nội dung (min-width: auto) và kéo phình cả hộp thoại thay vì cuộn.
    <div className="w-full min-w-0 overflow-x-auto rounded-lg border">
      <Table className="w-[2400px] table-fixed">
        <TableHeader className="bg-muted">
          <TableRow>
            <TableHead className="w-[70px]">Lần</TableHead>
            <TableHead className="w-[140px]">Kho nhận</TableHead>
            <TableHead className="w-[190px]">Đơn vị vận chuyển</TableHead>
            <TableHead className="w-[100px] text-right">SL gửi</TableHead>
            <TableHead className="w-[110px]">ĐVT VC</TableHead>
            <TableHead className="w-[110px] text-right">SL nhận</TableHead>
            <TableHead className="w-[150px] text-right">Thành tiền (nhận)</TableHead>
            <TableHead className="w-[150px]">Số hóa đơn</TableHead>
            <TableHead className="w-[150px]">Ngày hóa đơn</TableHead>
            <TableHead className="w-[130px] text-right">Đã trả</TableHead>
            <TableHead className="w-[130px] text-right">Còn lại</TableHead>
            <TableHead className="w-[150px]">Cam kết giao</TableHead>
            <TableHead className="w-[150px]">Ngày nhận</TableHead>
            <TableHead className="w-[90px] text-right">Ngày QĐ</TableHead>
            <TableHead className="w-[110px] text-center">Trễ CK</TableHead>
            <TableHead className="w-[110px] text-center">Trễ QĐ</TableHead>
            <TableHead className="w-[130px] text-center">Trạng thái giao</TableHead>
            <TableHead className="w-[140px] text-right">Đơn giá VC</TableHead>
            <TableHead className="w-[140px] text-right">Thành tiền VC</TableHead>
            <TableHead className="w-[170px]">Yêu cầu khác</TableHead>
            <TableHead className="w-[180px]">Phiếu giao</TableHead>
            <TableHead className="w-[70px]" />
          </TableRow>
        </TableHeader>

        <TableBody>
          {deliveries.length === 0 && (
            <TableRow>
              <TableCell colSpan={22} className="h-20 text-center text-muted-foreground">
                Chưa có lần giao nào.
              </TableCell>
            </TableRow>
          )}

          {deliveries.map((delivery, index) => {
            const receivedAmount =
              (delivery.received_qty || 0) * (item.price || 0) * (1 + (item.vat || 0) / 100)

            return (
              <TableRow key={delivery.id ?? `new-${index}`}>
                <TableCell>
                  <NumberCell
                    value={delivery.delivery_no}
                    editable={editable}
                    onChange={(value) => patch(index, { delivery_no: value })}
                  />
                </TableCell>

                <TableCell>
                  {editable ? (
                    <Select
                      value={delivery.warehouse_code || undefined}
                      onValueChange={(value) => patch(index, { warehouse_code: value })}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="—" />
                      </SelectTrigger>
                      <SelectContent>
                        {(warehouses?.items ?? []).map((warehouse) => (
                          <SelectItem key={warehouse.id} value={warehouse.code}>
                            {warehouse.code} — {warehouse.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    delivery.warehouse_code || '—'
                  )}
                </TableCell>

                <TableCell>
                  {editable ? (
                    <Select
                      value={
                        delivery.carrier_code ||
                        (delivery.carrier_name ? SELF_CARRIER : undefined)
                      }
                      onValueChange={(value) => pickCarrier(index, value)}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Chọn đơn vị VC" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={SELF_CARRIER}>NCC tự vận chuyển</SelectItem>
                        {carriers.map((carrier) => (
                          <SelectItem key={carrier.id} value={carrier.code}>
                            {carrier.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    delivery.carrier_name || '—'
                  )}
                </TableCell>

                <TableCell className="text-right">
                  <NumberCell
                    value={delivery.ship_qty}
                    editable={editable}
                    onChange={(value) => patch(index, { ship_qty: value })}
                  />
                </TableCell>

                <TableCell>
                  {editable ? (
                    <Select
                      value={delivery.ship_unit || undefined}
                      onValueChange={(value) => patch(index, { ship_unit: value })}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="—" />
                      </SelectTrigger>
                      <SelectContent>
                        {SHIP_UNITS.map((unit) => (
                          <SelectItem key={unit} value={unit}>
                            {unit}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    delivery.ship_unit || '—'
                  )}
                </TableCell>

                <TableCell className="text-right">
                  <NumberCell
                    value={delivery.received_qty}
                    editable={editable}
                    onChange={(value) => patch(index, { received_qty: value })}
                  />
                </TableCell>

                <TableCell className="text-right font-semibold tabular-nums">
                  {formatMoney(receivedAmount)} đ
                </TableCell>

                <TableCell>
                  {editable ? (
                    <Input
                      value={delivery.invoice_no || ''}
                      placeholder="Số HĐ đợt này"
                      onChange={(event) => {
                        const value = event.target.value
                        patch(index, {
                          invoice_no: value,
                          // Có số hóa đơn mà chưa có ngày thì lấy hôm nay — kế
                          // toán gần như luôn nhập hai ô này cùng lúc.
                          ...(value && !delivery.invoice_date
                            ? { invoice_date: new Date().toISOString().slice(0, 10) }
                            : {}),
                        })
                      }}
                    />
                  ) : (
                    delivery.invoice_no || '—'
                  )}
                </TableCell>

                <TableCell>
                  <DateCell
                    value={delivery.invoice_date}
                    editable={editable}
                    onChange={(value) => patch(index, { invoice_date: value })}
                  />
                </TableCell>

                <TableCell className="text-right font-medium tabular-nums text-success">
                  {delivery.id ? `${formatMoney(delivery.paid ?? 0)} đ` : '—'}
                </TableCell>

                <TableCell
                  className={cn(
                    'text-right font-medium tabular-nums',
                    (delivery.remaining ?? 0) > 0 ? 'text-destructive' : 'text-muted-foreground',
                  )}
                >
                  {delivery.id ? `${formatMoney(delivery.remaining ?? 0)} đ` : '—'}
                </TableCell>

                <TableCell>
                  <DateCell
                    value={delivery.promised_date}
                    editable={editable}
                    onChange={(value) => patch(index, { promised_date: value })}
                  />
                </TableCell>

                <TableCell>
                  <DateCell
                    value={delivery.received_date}
                    editable={editable}
                    onChange={(value) => patch(index, { received_date: value })}
                  />
                </TableCell>

                <TableCell className="text-right">
                  <NumberCell
                    value={delivery.std_days}
                    editable={editable}
                    onChange={(value) => patch(index, { std_days: value })}
                  />
                </TableCell>

                <TableCell className="text-center">
                  <LateCell value={delivery.received_date ? delivery.diff_promise : undefined} />
                </TableCell>
                <TableCell className="text-center">
                  <LateCell value={delivery.received_date ? delivery.diff_regulated : undefined} />
                </TableCell>

                <TableCell className="text-center">
                  {delivery.status ? (
                    <Badge
                      variant="secondary"
                      className={cn(
                        'border-0',
                        delivery.status === 'Đã nhận'
                          ? 'bg-success/10 text-success'
                          : delivery.status === 'Lỗi'
                            ? 'bg-destructive/10 text-destructive'
                            : 'bg-warning/10 text-warning',
                      )}
                    >
                      {delivery.status}
                    </Badge>
                  ) : (
                    '—'
                  )}
                </TableCell>

                <TableCell className="text-right">
                  <NumberCell
                    value={delivery.shipping_unit_price}
                    editable={editable}
                    // Cước = đơn giá × SL gửi; vẫn cho sửa tay ô thành tiền bên cạnh.
                    onChange={(value) =>
                      patch(index, {
                        shipping_unit_price: value,
                        shipping_amount: value * (delivery.ship_qty || 0),
                      })
                    }
                  />
                </TableCell>

                <TableCell className="text-right">
                  <NumberCell
                    value={delivery.shipping_amount}
                    editable={editable}
                    onChange={(value) => patch(index, { shipping_amount: value })}
                  />
                </TableCell>

                <TableCell>
                  {editable ? (
                    <Input
                      value={delivery.extra_request || ''}
                      onChange={(event) => patch(index, { extra_request: event.target.value })}
                    />
                  ) : (
                    delivery.extra_request || '—'
                  )}
                </TableCell>

                <TableCell className="whitespace-normal">
                  <PurchaseOrderDeliveryFiles
                    deliveryId={delivery.id}
                    purchaseOrderId={purchaseOrderId}
                    editable={attachEditable}
                  />
                </TableCell>

                <TableCell className="text-center">
                  {editable && (
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-destructive"
                      title="Xóa lần giao"
                      onClick={() =>
                        onChange(deliveries.filter((_, current) => current !== index))
                      }
                    >
                      <Trash2 />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

function NumberCell({
  value,
  editable,
  onChange,
}: {
  value: number
  editable: boolean
  onChange: (value: number) => void
}) {
  if (!editable) return <span className="tabular-nums">{formatQuantity(value || 0)}</span>

  return (
    <Input
      type="number"
      className="w-full px-2 text-right tabular-nums [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
      value={value ?? 0}
      onChange={(event) => onChange(Number(event.target.value) || 0)}
    />
  )
}

function DateCell({
  value,
  editable,
  onChange,
}: {
  value: string
  editable: boolean
  onChange: (value: string) => void
}) {
  if (!editable) return <span>{formatDate(value) || '—'}</span>

  return <DatePicker size="sm" value={value || ''} placeholder="—" onChange={onChange} />
}

/** Số ngày trễ: âm = trễ hạn nên tô đỏ, còn lại để trung tính. */
function LateCell({ value }: { value?: number }) {
  if (value === undefined || value === null) return <span className="text-muted-foreground">—</span>
  return (
    <span className={cn('tabular-nums', value < 0 && 'font-semibold text-destructive')}>
      {value}
    </span>
  )
}
