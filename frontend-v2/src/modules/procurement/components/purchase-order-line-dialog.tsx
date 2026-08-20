import type { Supplier } from '@/modules/production/types/supplier'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { CopyButton } from '@/shared/ui/copy-button'
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
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
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
  PO_FIELDS_EDITABLE_AFTER_APPROVE,
  PRODUCT_LOCK_HINT,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

interface PurchaseOrderLineDialogProps {
  item: PurchaseOrderItem | null
  lineNumber: number
  open: boolean
  /** Sửa được nội dung dòng (đơn chưa chốt + có quyền ghi). */
  editable: boolean
  /**
   * Đơn ĐÃ DUYỆT + có quyền ghi (CR-108). Chỉ mở đúng các ô phát sinh sau khi
   * duyệt; phần nội dung đã được ký thì vẫn khóa.
   */
  afterApproveEditable: boolean
  /** Nhập được tiến độ giao (đơn đã duyệt trở đi). */
  deliveryEditable: boolean
  /** Gắn tệp cho lần giao — mở cả khi đơn đã hoàn thành. */
  attachEditable: boolean
  purchaseOrderId: number
  carriers: Supplier[]
  /** Phiếu giao chọn trước khi lưu, khóa theo chỉ số lần giao của dòng này. */
  pendingFiles: Record<number, File[]>
  onChange: (item: PurchaseOrderItem) => void
  onPendingFilesChange: (deliveryIndex: number, files: File[]) => void
  onDeliveryRemoved: (deliveryIndex: number) => void
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
  afterApproveEditable,
  deliveryEditable,
  attachEditable,
  purchaseOrderId,
  carriers,
  pendingFiles,
  onChange,
  onPendingFilesChange,
  onDeliveryRemoved,
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
  /**
   * Ô còn mở khi đơn ĐÃ DUYỆT (CR-108). Gộp với `fieldEditable` chứ không thay thế:
   * lúc đơn còn Nháp thì mấy ô này vẫn sửa như cũ.
   */
  const lateEditable = fieldEditable || (afterApproveEditable && !locked)
  const remaining = (item.qty_order || 0) - (item.qty_received || 0)

  const patch = (changes: Partial<PurchaseOrderItem>) => onChange({ ...item, ...changes })

  /**
   * Chỉ xem thì hiện "MÃ — Tên kho" cho đúng thứ đang thấy lúc mở ô chọn. Kho cũ
   * bị gỡ khỏi danh mục thì vẫn hiện mã trần, đừng nuốt mất dữ liệu của đơn cũ.
   */
  function warehouseLabel(code?: string) {
    if (!code) return ''
    const warehouse = (warehouses?.items ?? []).find((option) => option.code === code)
    return warehouse ? `${warehouse.code} — ${warehouse.name}` : code
  }

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

        {afterApproveEditable && !locked && (
          <p className="rounded-md border border-info/30 bg-info/8 px-3 py-2 text-sm text-muted-foreground">
            Đơn đã duyệt — chỉ còn sửa được: {PO_FIELDS_EDITABLE_AFTER_APPROVE}. Muốn đổi phần
            khác thì bấm <b>Hủy duyệt</b> ở đầu trang để đơn về Nháp, sửa xong gửi duyệt lại.
          </p>
        )}

        <section className="grid min-w-0 gap-x-4 gap-y-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="text-muted-foreground">
              Mã hàng
              <RequiredMark />
            </Label>
            {/* Chỉ xem nhưng phải lấy ra được để tra cứu — chép bằng nút cho chắc. */}
            <div className="flex min-w-0 items-center gap-1">
              <ReadOnlyValue className="min-w-0 flex-1">{item.product_code}</ReadOnlyValue>
              <CopyButton value={item.product_code} label="mã hàng" className="size-8" />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>
              Phân loại
              <RequiredMark />
            </Label>
            {fieldEditable ? (
              <Input
                value={item.item_group || ''}
                onChange={(event) => patch({ item_group: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{item.item_group}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label title={received ? PRODUCT_LOCK_HINT : undefined}>
              Tên hàng
              <RequiredMark />
            </Label>
            {fieldEditable && !received ? (
              <Textarea
                rows={2}
                value={item.product_name || ''}
                onChange={(event) => patch({ product_name: event.target.value })}
              />
            ) : (
              <ReadOnlyValue multiline>{item.product_name}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label>
              Tên trên hóa đơn
              {/* Bắt buộc, nhưng backend suy sẵn từ danh mục sản phẩm khi trả dữ
                  liệu về — nói rõ để người lập không tưởng phải gõ tay mọi dòng. */}
              <RequiredMark hint="Bắt buộc trước khi gửi duyệt — bỏ trống thì lấy theo danh mục sản phẩm; sản phẩm chưa khai thì phải gõ tay" />
            </Label>
            {lateEditable ? (
              <Textarea
                rows={2}
                value={item.invoice_name || ''}
                placeholder="Bỏ trống thì hệ thống lấy theo danh mục sản phẩm"
                onChange={(event) => patch({ invoice_name: event.target.value })}
              />
            ) : (
              <ReadOnlyValue multiline>{item.invoice_name}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label>Xuất xứ / TSKT / chất liệu</Label>
            {fieldEditable ? (
              <Textarea
                rows={2}
                value={item.spec || ''}
                onChange={(event) => patch({ spec: event.target.value })}
              />
            ) : (
              <ReadOnlyValue multiline>{item.spec}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Mã HH (thành phẩm)</Label>
            {fieldEditable ? (
              <Input
                value={item.fg_code || ''}
                placeholder="Tự gắn khi chọn sản phẩm"
                onChange={(event) => patch({ fg_code: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{item.fg_code}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Tên HH (thành phẩm)</Label>
            {fieldEditable ? (
              <Input
                value={item.fg_name || ''}
                placeholder="Tự gắn khi chọn sản phẩm"
                onChange={(event) => patch({ fg_name: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{item.fg_name}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label title="Có ngày này thì dòng chuyển sang 'Đã gửi ĐMH cho KT'">
              Ngày giao chứng từ cho KT
            </Label>
            {lateEditable ? (
              <DatePicker
                value={item.document_delivery_date || ''}
                onChange={(value) => patch({ document_delivery_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(item.document_delivery_date)}
              </ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>
              Ngày yêu cầu có hàng
              <RequiredMark />
            </Label>
            {fieldEditable ? (
              <DatePicker
                value={item.required_date || ''}
                onChange={(value) => patch({ required_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(item.required_date)}
              </ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>
              Ngày dự kiến có hàng
              {/* Hệ thống tự tính khi lưu (theo dòng YCMH nguồn, không có thì
                  theo thời gian chuẩn của phân loại). Dòng thêm tay hoặc phân
                  loại chưa khai thời gian chuẩn thì ô ở lại rỗng, phải gõ tay. */}
              <RequiredMark hint="Bắt buộc trước khi gửi duyệt — bỏ trống thì hệ thống tự tính theo phân loại; không tính được thì phải chọn tay" />
            </Label>
            {lateEditable ? (
              <DatePicker
                value={item.expected_date || ''}
                onChange={(value) => patch({ expected_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(item.expected_date)}
              </ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>
              SL yêu cầu
              <RequiredMark />
            </Label>
            {fieldEditable ? (
              <Input
                type="number"
                min={0}
                step="0.001"
                value={item.qty_request || ''}
                onChange={(event) => patch({ qty_request: Number(event.target.value) })}
              />
            ) : (
              // Chỉ xem thì hiện số đã ngăn cách hàng nghìn — ô nhập bắt buộc để
              // số trần (2000), đọc lướt qua rất dễ nhầm bậc.
              <ReadOnlyValue className="tabular-nums">
                {formatQuantity(item.qty_request)}
              </ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>
              ĐVT
              <RequiredMark />
            </Label>
            {fieldEditable && !received ? (
              <Select value={item.unit || undefined} onValueChange={(value) => patch({ unit: value })}>
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
            ) : (
              <ReadOnlyValue>{item.unit}</ReadOnlyValue>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>
              Kho nhận mặc định
              <RequiredMark />
            </Label>
            {lateEditable ? (
              <Select
                value={item.warehouse_code || undefined}
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
            ) : (
              <ReadOnlyValue>{warehouseLabel(item.warehouse_code)}</ReadOnlyValue>
            )}
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
            {lateEditable ? (
              <Input
                value={item.note || ''}
                onChange={(event) => patch({ note: event.target.value })}
              />
            ) : (
              <ReadOnlyValue multiline>{item.note}</ReadOnlyValue>
            )}
          </div>
        </section>

        <section className="min-w-0 space-y-3 border-t pt-4">
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
            pendingFiles={pendingFiles}
            onChange={(deliveries) => patch({ deliveries })}
            onPendingFilesChange={onPendingFilesChange}
            onDeliveryRemoved={onDeliveryRemoved}
            onAdd={
              canEditDeliveries && purchaseOrderId > 0
                ? () =>
                    patch({
                      deliveries: [
                        ...(item.deliveries ?? []),
                        createEmptyDelivery(item, (item.deliveries?.length ?? 0) + 1),
                      ],
                    })
                : undefined
            }
          />
        </section>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          {(editable || canEditDeliveries || lateEditable) && (
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

function Field({
  label,
  required,
  children,
}: {
  label: string
  /**
   * Ô bắt buộc theo cổng CR-095. Nhãn ở đây là chữ mờ nhưng dấu sao vẫn đỏ —
   * `RequiredMark` tự mang màu riêng nên không bị `text-muted-foreground` nuốt.
   */
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">
        {label}
        {required && <RequiredMark />}
      </Label>
      <ReadOnlyValue className="tabular-nums">{children}</ReadOnlyValue>
    </div>
  )
}
