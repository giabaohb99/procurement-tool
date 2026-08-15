import { Plus } from 'lucide-react'

import type { Supplier } from '@/modules/production/types/supplier'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import {
  usePurchaseRequestUnits,
  usePurchaseRequestWarehouses,
} from '../hooks/use-purchase-request-support'
import { ProgressStatusBadge } from './document-status-badge'
import { PurchaseOrderDeliveriesTable } from './purchase-order-deliveries-table'
import {
  isLineLocked,
  isLineReceived,
  PRODUCT_LOCK_HINT,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

interface PurchaseOrderLineDialogProps {
  item: PurchaseOrderItem | null
  lineNumber: number
  open: boolean
  /** Sửa được nội dung dòng (đơn chưa chốt + có quyền ghi). */
  editable: boolean
  /** Nhập được tiến độ giao (đơn đã duyệt trở đi). */
  deliveryEditable: boolean
  /** Gắn tệp cho lần giao — mở cả khi đơn đã hoàn thành. */
  attachEditable: boolean
  purchaseOrderId: number
  carriers: Supplier[]
  onChange: (item: PurchaseOrderItem) => void
  onOpenChange: (open: boolean) => void
  /** Lưu cả đơn — lần giao chỉ được ghi nhận khi lưu đơn (giống v1). */
  onSave: () => void
}

/**
 * Chi tiết một dòng ĐMH: các trường không đủ chỗ trên bảng chính (tên hóa đơn,
 * thông số, thành phẩm, kho, ngày chứng từ…) và bảng GIAO HÀNG NHIỀU LẦN.
 *
 * Dialog chỉ sửa state nháp; ghi xuống server khi bấm "Lưu đơn" — backend nhận
 * cả header + dòng + lần giao trong một lần `PATCH`.
 */
export function PurchaseOrderLineDialog({
  item,
  lineNumber,
  open,
  editable,
  deliveryEditable,
  attachEditable,
  purchaseOrderId,
  carriers,
  onChange,
  onOpenChange,
  onSave,
}: PurchaseOrderLineDialogProps) {
  const { data: units } = usePurchaseRequestUnits(open)
  const { data: warehouses } = usePurchaseRequestWarehouses(open)

  if (!item) return null

  const locked = isLineLocked(item)
  const received = isLineReceived(item)
  const fieldEditable = editable && !locked
  const canEditDeliveries = deliveryEditable && !locked
  const remaining = (item.qty_order || 0) - (item.qty_received || 0)

  const patch = (changes: Partial<PurchaseOrderItem>) => onChange({ ...item, ...changes })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* `max-w-*!`: `DialogContent` của shadcn có sẵn `max-w-[calc(100%-2rem)]`
          và `sm:max-w-lg` — không đánh important thì hộp thoại bị bóp lại theo
          luật gốc, bảng lần giao 22 cột không còn chỗ. */}
      <DialogContent className="max-h-[92vh] w-[96vw] max-w-[1200px]! overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Dòng {lineNumber}: {item.product_name || item.product_code || 'Chưa chọn sản phẩm'}
          </DialogTitle>
          <DialogDescription>
            SL đặt {formatQuantity(item.qty_order)} · Đã nhận{' '}
            {formatQuantity(item.qty_received ?? 0)} · Còn lại {formatQuantity(remaining)}
          </DialogDescription>
        </DialogHeader>

        <section className="grid min-w-0 gap-x-4 gap-y-3 md:grid-cols-2">
          <Field label="Mã hàng">{item.product_code || '—'}</Field>

          <div className="space-y-1.5">
            <Label>Phân loại</Label>
            <Input
              value={item.item_group || ''}
              disabled={!fieldEditable}
              onChange={(event) => patch({ item_group: event.target.value })}
            />
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label title={received ? PRODUCT_LOCK_HINT : undefined}>Tên hàng</Label>
            <Textarea
              rows={2}
              value={item.product_name || ''}
              disabled={!fieldEditable || received}
              onChange={(event) => patch({ product_name: event.target.value })}
            />
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label>Tên trên hóa đơn</Label>
            <Textarea
              rows={2}
              value={item.invoice_name || ''}
              placeholder="Bỏ trống thì hệ thống lấy theo danh mục sản phẩm"
              disabled={!fieldEditable}
              onChange={(event) => patch({ invoice_name: event.target.value })}
            />
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label>Xuất xứ / TSKT / chất liệu</Label>
            <Textarea
              rows={2}
              value={item.spec || ''}
              disabled={!fieldEditable}
              onChange={(event) => patch({ spec: event.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Mã HH (thành phẩm)</Label>
            <Input
              value={item.fg_code || ''}
              placeholder="Tự gắn khi chọn sản phẩm"
              disabled={!fieldEditable}
              onChange={(event) => patch({ fg_code: event.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Tên HH (thành phẩm)</Label>
            <Input
              value={item.fg_name || ''}
              placeholder="Tự gắn khi chọn sản phẩm"
              disabled={!fieldEditable}
              onChange={(event) => patch({ fg_name: event.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label title="Có ngày này thì dòng chuyển sang 'Đã gửi ĐMH cho KT'">
              Ngày giao chứng từ cho KT
            </Label>
            <DatePicker
              value={item.document_delivery_date || ''}
              disabled={!fieldEditable}
              onChange={(value) => patch({ document_delivery_date: value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Ngày yêu cầu có hàng</Label>
            <DatePicker
              value={item.required_date || ''}
              disabled={!fieldEditable}
              onChange={(value) => patch({ required_date: value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>ĐVT</Label>
            <Select
              value={item.unit || undefined}
              disabled={!fieldEditable || received}
              onValueChange={(value) => patch({ unit: value })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn ĐVT" />
              </SelectTrigger>
              <SelectContent>
                {(units?.items ?? []).map((unit) => (
                  <SelectItem key={unit.id} value={unit.name}>
                    {unit.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Kho nhận mặc định</Label>
            <Select
              value={item.warehouse_code || undefined}
              disabled={!fieldEditable}
              onValueChange={(value) => patch({ warehouse_code: value })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn kho" />
              </SelectTrigger>
              <SelectContent>
                {(warehouses?.items ?? []).map((warehouse) => (
                  <SelectItem key={warehouse.id} value={warehouse.code}>
                    {warehouse.code} — {warehouse.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Tùy chọn dòng</Label>
            <label className="flex min-h-9 cursor-pointer items-center gap-2 text-sm">
              <Checkbox
                checked={item.supplier_ready}
                disabled={!fieldEditable}
                onCheckedChange={(checked) => patch({ supplier_ready: checked === true })}
              />
              NCC có sẵn hàng
            </label>
          </div>

          <div className="space-y-1.5">
            <Label>Trạng thái tiến độ</Label>
            <div className="flex min-h-9 items-center gap-2">
              <ProgressStatusBadge status={item.progress_status ?? 'Chưa đặt hàng'} />
              {item.pause_reason && (
                <span className="text-xs text-muted-foreground">Lý do: {item.pause_reason}</span>
              )}
            </div>
          </div>

          <Field label="Tổng tiền đặt hàng">
            {formatMoney(
              item.order_total ??
                (item.qty_order || 0) * (item.price || 0) * (1 + (item.vat || 0) / 100),
            )}{' '}
            đ
          </Field>
          <Field label="Tiền hàng đã nhận">{formatMoney(item.goods_total ?? 0)} đ</Field>
          <Field label="Đã trả">{formatMoney(item.paid_total ?? 0)} đ</Field>
          <Field label="Còn lại">{formatMoney(item.remaining_total ?? 0)} đ</Field>

          <div className="space-y-1.5 md:col-span-2">
            <Label>Ghi chú</Label>
            <Input
              value={item.note || ''}
              disabled={!fieldEditable}
              onChange={(event) => patch({ note: event.target.value })}
            />
          </div>
        </section>

        <section className="min-w-0 space-y-3 border-t pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-navy dark:text-foreground">
              Giao hàng (nhiều lần)
            </h3>
            {canEditDeliveries && (
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  patch({
                    deliveries: [
                      ...(item.deliveries ?? []),
                      createEmptyDelivery(item, (item.deliveries?.length ?? 0) + 1),
                    ],
                  })
                }
              >
                <Plus />
                Thêm lần giao
              </Button>
            )}
          </div>

          {purchaseOrderId <= 0 && (
            <p className="text-sm text-muted-foreground">
              Lưu đơn (Tạo) trước rồi mới thêm được lần giao.
            </p>
          )}
          {purchaseOrderId > 0 && !deliveryEditable && (
            <p className="text-sm text-muted-foreground">
              Chỉ thêm/sửa lần giao khi đơn đã được duyệt.
            </p>
          )}
          {locked && (
            <p className="text-sm text-muted-foreground">
              Dòng đã {item.progress_status === 'Hủy đơn' ? 'hủy' : 'hoàn thành'} — không sửa được
              lần giao.
            </p>
          )}

          <PurchaseOrderDeliveriesTable
            item={item}
            editable={canEditDeliveries && purchaseOrderId > 0}
            carriers={carriers}
            attachEditable={attachEditable && !locked}
            purchaseOrderId={purchaseOrderId}
            onChange={(deliveries) => patch({ deliveries })}
          />
        </section>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          {(editable || canEditDeliveries) && (
            <Button
              onClick={() => {
                onOpenChange(false)
                onSave()
              }}
            >
              Lưu đơn
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Lần giao mới: kế thừa kho nhận và ĐVT của dòng để đỡ phải chọn lại. */
function createEmptyDelivery(item: PurchaseOrderItem, deliveryNo: number) {
  return {
    delivery_no: deliveryNo,
    warehouse_code: item.warehouse_code || '',
    carrier_code: '',
    carrier_name: '',
    ship_qty: 0,
    ship_unit: item.unit || '',
    received_qty: 0,
    promised_date: '',
    expected_date: '',
    received_date: '',
    std_days: 0,
    invoice_no: '',
    invoice_date: '',
    shipping_unit_price: 0,
    shipping_amount: 0,
    qc_result: '',
    extra_request: '',
    progress_note: '',
  }
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">{label}</Label>
      <div className="flex min-h-9 items-center rounded-lg border bg-muted/35 px-3 py-2 text-sm font-medium tabular-nums">
        {children}
      </div>
    </div>
  )
}
