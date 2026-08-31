import { Plus, Trash2 } from 'lucide-react'
import { useMemo } from 'react'

import type { Supplier } from '@/modules/production/types/supplier'
import { LinesTable } from '@/shared/data-table/lines-table'
import type { LinesTableColumn } from '@/shared/data-table/types'
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

const TABLE_STORAGE_KEY = 'purchase-order-deliveries'

interface PurchaseOrderDeliveriesTableProps {
  item: PurchaseOrderItem
  /** Đơn đã duyệt + có quyền ghi thì mới nhập được tiến độ giao. */
  editable: boolean
  /** Đơn vị vận chuyển (`supplier_type = 'transport'`). */
  carriers: Supplier[]
  /** Cho gắn/xóa tệp của lần giao — mở cả khi đơn đã hoàn thành. */
  attachEditable: boolean
  purchaseOrderId: number
  /** Tệp chọn trước khi lần giao được lưu, khóa theo chỉ số lần giao. */
  pendingFiles: Record<number, File[]>
  onChange: (deliveries: PurchaseOrderDelivery[]) => void
  onPendingFilesChange: (deliveryIndex: number, files: File[]) => void
  /** Xóa lần giao làm lệch chỉ số các lần sau — trang phải dời giỏ tệp theo. */
  onDeliveryRemoved?: (deliveryIndex: number) => void
  /** Nút "Thêm lần giao" nằm trên thanh công cụ của bảng. */
  onAdd?: () => void
}

/**
 * Bảng các LẦN GIAO của một dòng hàng: nhận hàng nhiều đợt, mỗi đợt có số hóa
 * đơn, cước vận chuyển và công nợ riêng.
 *
 * Dùng chung khung `LinesTable` với bảng dòng hàng YCMH/YCBG/ĐMH: ẩn/hiện, ghim,
 * kéo giãn, đổi thứ tự cột. 24 cột nhồi vào hộp thoại thì chật, nên bảng mở sẵn
 * ở chế độ RÚT GỌN; cần đủ cột thì bấm "Bảng đầy đủ".
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
  pendingFiles,
  onChange,
  onPendingFilesChange,
  onDeliveryRemoved,
  onAdd,
}: PurchaseOrderDeliveriesTableProps) {
  const { data: warehouses } = usePurchaseRequestWarehouses()
  const deliveries = item.deliveries ?? []

  const columns = useMemo<LinesTableColumn[]>(() => [
    {
      key: 'delivery_no',
      header: 'Lần',
      width: 70,
      minWidth: 50,
      hideable: false,
      defaultPinned: true,
      align: 'center',
    },
    { key: 'warehouse', header: 'Kho nhận', width: 140, minWidth: 90 },
    { key: 'carrier', header: 'Đơn vị vận chuyển', width: 190, minWidth: 120 },
    { key: 'ship_qty', header: 'SL gửi', width: 100, minWidth: 60, align: 'right' },
    {
      key: 'ship_unit',
      header: 'ĐVT VC',
      width: 110,
      minWidth: 70,
      compactHidden: true,
    },
    { key: 'received_qty', header: 'SL nhận', width: 110, minWidth: 60, align: 'right' },
    {
      key: 'received_amount',
      header: 'Thành tiền (nhận)',
      width: 150,
      minWidth: 90,
      align: 'right',
    },
    {
      key: 'invoice_no',
      header: 'Số hóa đơn',
      width: 150,
      minWidth: 90,
      compactHidden: true,
    },
    {
      key: 'invoice_date',
      header: 'Ngày hóa đơn',
      width: 150,
      minWidth: 100,
      compactHidden: true,
    },
    {
      key: 'paid',
      header: 'Đã trả',
      width: 130,
      minWidth: 80,
      align: 'right',
      compactHidden: true,
    },
    {
      key: 'remaining',
      header: 'Còn lại',
      width: 130,
      minWidth: 80,
      align: 'right',
      compactHidden: true,
    },
    { key: 'promised_date', header: 'Cam kết giao', width: 150, minWidth: 100 },
    { key: 'received_date', header: 'Ngày nhận', width: 150, minWidth: 100 },
    {
      //  Đây là SỐ NGÀY quy định và người dùng nhập được — trước gắn nhãn "Ngày
      //  QĐ" nên bị đọc nhầm là cột ngày.
      key: 'std_days',
      header: 'Số ngày QĐ',
      width: 100,
      minWidth: 70,
      align: 'right',
      compactHidden: true,
    },
    {
      key: 'regulated_date',
      header: 'Ngày QĐ',
      width: 130,
      minWidth: 100,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'diff_promise',
      header: 'Trễ CK',
      width: 110,
      minWidth: 60,
      align: 'center',
      compactHidden: true,
    },
    {
      key: 'diff_regulated',
      header: 'Trễ QĐ',
      width: 110,
      minWidth: 60,
      align: 'center',
      compactHidden: true,
    },
    {
      //  Lệch giữa ngày quy định và NGÀY KINH DOANH YÊU CẦU CÓ HÀNG của dòng —
      //  khác `diff_regulated` (lệch với ngày nhận thật).
      key: 'diff_required',
      header: 'Trễ QĐ-KD',
      width: 110,
      minWidth: 70,
      align: 'center',
      compactHidden: true,
    },
    { key: 'status', header: 'Trạng thái giao', width: 130, minWidth: 90, align: 'center' },
    {
      key: 'shipping_unit_price',
      header: 'Đơn giá VC',
      width: 140,
      minWidth: 80,
      align: 'right',
      compactHidden: true,
    },
    {
      key: 'shipping_amount',
      header: 'Thành tiền VC',
      width: 140,
      minWidth: 80,
      align: 'right',
      compactHidden: true,
    },
    {
      key: 'extra_request',
      header: 'Yêu cầu khác',
      width: 170,
      minWidth: 110,
      compactHidden: true,
    },
    { key: 'files', header: 'Phiếu giao', width: 180, minWidth: 120 },
    {
      key: 'action',
      header: 'Thao tác',
      width: 80,
      minWidth: 60,
      hideable: false,
      align: 'center',
    },
  ], [])

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

  function remove(index: number) {
    onChange(deliveries.filter((_, current) => current !== index))
    onDeliveryRemoved?.(index)
  }

  function renderCell(key: string, delivery: PurchaseOrderDelivery, index: number) {
    switch (key) {
      case 'delivery_no':
        return (
          <NumberCell
            value={delivery.delivery_no}
            editable={editable}
            onChange={(value) => patch(index, { delivery_no: value })}
          />
        )

      case 'warehouse':
        return editable ? (
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
        )

      case 'carrier':
        return editable ? (
          <Select
            value={
              delivery.carrier_code || (delivery.carrier_name ? SELF_CARRIER : undefined)
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
        )

      case 'ship_qty':
        return (
          <NumberCell
            value={delivery.ship_qty}
            editable={editable}
            onChange={(value) => patch(index, { ship_qty: value })}
          />
        )

      case 'ship_unit':
        return editable ? (
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
        )

      case 'received_qty':
        return (
          <NumberCell
            value={delivery.received_qty}
            editable={editable}
            onChange={(value) => patch(index, { received_qty: value })}
          />
        )

      case 'received_amount':
        return (
          <span className="font-semibold tabular-nums">
            {formatMoney(
              (delivery.received_qty || 0) * (item.price || 0) * (1 + (item.vat || 0) / 100),
            )}{' '}
            đ
          </span>
        )

      case 'invoice_no':
        return editable ? (
          <Input
            value={delivery.invoice_no || ''}
            placeholder="Số HĐ đợt này"
            onChange={(event) => {
              const value = event.target.value
              patch(index, {
                invoice_no: value,
                // Có số hóa đơn mà chưa có ngày thì lấy hôm nay — kế toán gần
                // như luôn nhập hai ô này cùng lúc.
                ...(value && !delivery.invoice_date
                  ? { invoice_date: new Date().toISOString().slice(0, 10) }
                  : {}),
              })
            }}
          />
        ) : (
          delivery.invoice_no || '—'
        )

      case 'invoice_date':
        return (
          <DateCell
            value={delivery.invoice_date}
            editable={editable}
            onChange={(value) => patch(index, { invoice_date: value })}
          />
        )

      case 'paid':
        return (
          <span className="font-medium tabular-nums text-success">
            {delivery.id ? `${formatMoney(delivery.paid ?? 0)} đ` : '—'}
          </span>
        )

      case 'remaining':
        return (
          <span
            className={cn(
              'font-medium tabular-nums',
              (delivery.remaining ?? 0) > 0 ? 'text-destructive' : 'text-muted-foreground',
            )}
          >
            {delivery.id ? `${formatMoney(delivery.remaining ?? 0)} đ` : '—'}
          </span>
        )

      case 'promised_date':
        return (
          <DateCell
            value={delivery.promised_date}
            editable={editable}
            onChange={(value) => patch(index, { promised_date: value })}
          />
        )

      case 'received_date':
        return (
          <DateCell
            value={delivery.received_date}
            editable={editable}
            onChange={(value) => patch(index, { received_date: value })}
          />
        )

      case 'std_days':
        return (
          <NumberCell
            value={delivery.std_days}
            editable={editable}
            onChange={(value) => patch(index, { std_days: value })}
          />
        )

      case 'regulated_date':
        return (
          <span className="whitespace-nowrap text-muted-foreground">
            {formatDate(delivery.regulated_date ?? '') || '—'}
          </span>
        )

      case 'diff_promise':
        return <LateCell value={delivery.received_date ? delivery.diff_promise : undefined} />

      case 'diff_regulated':
        return <LateCell value={delivery.received_date ? delivery.diff_regulated : undefined} />

      //  Mốc so ở đây là ngày kinh doanh YÊU CẦU có hàng của dòng, không phải
      //  ngày nhận — chưa có ngày yêu cầu thì không có gì để so.
      case 'diff_required':
        return <LateCell value={item.required_date ? delivery.diff_required : undefined} />

      case 'status':
        return delivery.status ? (
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
        )

      case 'shipping_unit_price':
        return (
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
        )

      case 'shipping_amount':
        return (
          <NumberCell
            value={delivery.shipping_amount}
            editable={editable}
            onChange={(value) => patch(index, { shipping_amount: value })}
          />
        )

      case 'extra_request':
        return editable ? (
          <Input
            value={delivery.extra_request || ''}
            onChange={(event) => patch(index, { extra_request: event.target.value })}
          />
        ) : (
          delivery.extra_request || '—'
        )

      case 'files':
        return (
          <PurchaseOrderDeliveryFiles
            deliveryId={delivery.id}
            purchaseOrderId={purchaseOrderId}
            editable={attachEditable}
            pendingFiles={pendingFiles[index] ?? []}
            onPendingFilesChange={(files) => onPendingFilesChange(index, files)}
          />
        )

      case 'action':
        return (
          editable && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-destructive hover:text-destructive"
              title="Xóa lần giao"
              onClick={() => remove(index)}
            >
              <Trash2 />
            </Button>
          )
        )

      default:
        return null
    }
  }

  return (
    <LinesTable
      columns={columns}
      rows={deliveries}
      storageKey={TABLE_STORAGE_KEY}
      rowKey={(delivery, index) => delivery.id ?? `new-${index}`}
      renderCell={renderCell}
      defaultCompact
      title={`Giao hàng nhiều lần (${deliveries.length} lần)`}
      emptyMessage="Chưa có lần giao nào."
      cellClassName={(key) => (key === 'files' ? 'whitespace-normal' : undefined)}
      actions={
        onAdd && (
          <Button type="button" variant="outline" size="sm" onClick={onAdd}>
            <Plus />
            Thêm lần giao
          </Button>
        )
      }
    />
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
      className="w-full px-2 text-right tabular-nums"
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
  if (value === undefined || value === null)
    return <span className="text-muted-foreground">—</span>
  return (
    <span className={cn('tabular-nums', value < 0 && 'font-semibold text-destructive')}>
      {value}
    </span>
  )
}
