import { Loader2, RotateCcw } from 'lucide-react'
import { useRef, useState, type ReactNode } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { useResetPrOptionZero, useUpdatePrOptionDetails } from '../hooks/use-purchase-request-options'
import type { PurchaseRequestOption } from '../types/purchase-request-options'
import { PR_OPTION_SOURCE_ORIGINAL } from '../types/purchase-request-options'
import {
  NO_SUPPLIER_CODE,
  buildOptionDetailsPayload,
  optionToDetailsForm,
  type OptionDetailsForm,
} from '../utils/purchase-request-option-details'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

interface PurchaseRequestOptionEditDialogProps {
  purchaseRequestId: number
  itemId: number
  option: PurchaseRequestOption
  suppliers: { code: string; name: string }[]
  onClose: () => void
}

/**
 * bao-CR-583 (đại ca chốt 03/10/2026) — sửa thông tin PHƯƠNG ÁN 0 và phương án NHẬP TAY, dùng
 * chung cho màn xử lý (NSTM) và màn chọn (thu mua). «Phương án 0 xem như phương án nhập tay và
 * chỉnh sửa lại được.»
 *
 * Phương án 0 sinh từ chính dòng yêu cầu nên thường thiếu mã VTBB, NCC, giá thật; riêng nó có
 * nút «Khôi phục ban đầu» đưa về đúng như dòng yêu cầu lúc sinh (bỏ NCC, xóa mọi ô đã sửa).
 * Phương án đang được chọn mà đổi mã thì mã của DÒNG đổi theo — lập đơn đọc mã ở dòng
 * (bao-CR-568). Phương án lấy từ khảo sát KHÔNG đi hộp này (chỉ sửa giá).
 */
export function PurchaseRequestOptionEditDialog({
  purchaseRequestId,
  itemId,
  option,
  suppliers,
  onClose,
}: PurchaseRequestOptionEditDialogProps) {
  const [form, setForm] = useState<OptionDetailsForm>(() => optionToDetailsForm(option))
  const updateMutation = useUpdatePrOptionDetails(purchaseRequestId)
  const resetMutation = useResetPrOptionZero(purchaseRequestId)
  //  `disabled={isPending}` chỉ đúng ở lượt render sau — bấm đúp vẫn lọt hai request.
  const busyRef = useRef(false)
  const pending = updateMutation.isPending || resetMutation.isPending
  const isOptionZero = option.source === PR_OPTION_SOURCE_ORIGINAL
  const label = option.display_label || `Phương án ${option.public_id}`

  const patch = (changes: Partial<OptionDetailsForm>) => setForm((current) => ({ ...current, ...changes }))
  const settle = { onSettled: () => (busyRef.current = false), onSuccess: onClose }

  const submit = () => {
    if (busyRef.current) return
    const { payload, error } = buildOptionDetailsPayload(option, form)
    if (error) {
      toast.error(error)
      return
    }
    if (Object.keys(payload).length === 0) {
      toast.error('Chưa có thay đổi nào để lưu')
      return
    }
    busyRef.current = true
    updateMutation.mutate({ itemId, optionId: option.id, payload }, settle)
  }

  const reset = async () => {
    if (busyRef.current) return
    const ok = await confirm({
      title: 'Khôi phục Phương án 0',
      message:
        'Phương án 0 sẽ về đúng như dòng yêu cầu: tên hàng, ĐVT, giá đề xuất, VAT, mã hàng của dòng; ' +
        'bỏ nhà cung cấp và xóa mọi ô đã sửa. Mã VTBB đã gắn cho dòng vẫn giữ.',
      confirmLabel: 'Khôi phục',
    })
    if (!ok || busyRef.current) return
    busyRef.current = true
    resetMutation.mutate({ itemId, optionId: option.id }, settle)
  }

  const supplierOptions = [
    { value: NO_SUPPLIER_CODE, label: '— Không chọn —' },
    ...suppliers.map((supplier) => ({
      value: supplier.code,
      label: `${supplier.code} — ${supplier.name}`,
    })),
  ]

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Sửa {label}</DialogTitle>
          <DialogDescription>
            {isOptionZero
              ? 'Phương án 0 là mua đúng theo dòng yêu cầu. Bổ sung mã VTBB, nhà cung cấp, giá và điều kiện giao; cần thì bấm «Khôi phục ban đầu» để quay về như dòng yêu cầu.'
              : 'Phương án nhập tay: sửa được mọi thông tin, nhà cung cấp không được bỏ trống.'}
          </DialogDescription>
        </DialogHeader>

        {/* `min-w-0`: lưới của DialogContent giãn theo chữ dài nhất (bao-CR-575). */}
        <div className="grid min-w-0 gap-3 sm:grid-cols-2">
          <Field label="Mã VTBB" wide>
            <PurchaseRequestProductPicker
              code={form.productCode}
              name={form.productName}
              onPick={(product) =>
                patch(
                  product
                    ? { productCode: product.code, productName: product.name, quoteUnit: product.unit || form.quoteUnit }
                    : { productCode: '' },
                )
              }
            />
          </Field>
          <Field label="Tên hàng" wide>
            <Input value={form.productName} onChange={(event) => patch({ productName: event.target.value })} />
          </Field>
          <Field label="Nhà cung cấp" wide>
            <div className="min-w-0 space-y-1.5">
              <SearchSelect
                className="w-full"
                value={form.supplierCode}
                onChange={(value) =>
                  patch(value !== NO_SUPPLIER_CODE ? { supplierCode: value, supplierName: '' } : { supplierCode: value })
                }
                placeholder="Chọn NCC trong danh mục"
                searchPlaceholder="Tìm NCC theo mã / tên…"
                options={supplierOptions}
              />
              <Input
                value={form.supplierName}
                placeholder="Hoặc gõ tên NCC ngoài danh mục"
                onChange={(event) =>
                  patch(
                    event.target.value.trim()
                      ? { supplierName: event.target.value, supplierCode: NO_SUPPLIER_CODE }
                      : { supplierName: event.target.value },
                  )
                }
              />
            </div>
          </Field>
          <Field label="Đơn giá (đ)">
            <NumberInput value={form.price} onChange={(price) => patch({ price })} label="Đơn giá" />
          </Field>
          <Field label="ĐVT báo giá">
            <Input value={form.quoteUnit} onChange={(event) => patch({ quoteUnit: event.target.value })} />
          </Field>
          <Field label="VAT (%)">
            <NumberInput value={form.vat} onChange={(vat) => patch({ vat })} label="VAT" />
          </Field>
          <Field label="MOQ">
            <NumberInput value={form.moq} onChange={(moq) => patch({ moq })} label="MOQ" />
          </Field>
          <Field label="Khoảng SL áp giá">
            <Input value={form.volumeRange} onChange={(event) => patch({ volumeRange: event.target.value })} />
          </Field>
          <Field label="Xuất xứ">
            <Input value={form.origin} onChange={(event) => patch({ origin: event.target.value })} />
          </Field>
          <Field label="Thời gian giao">
            <Input value={form.deliveryTime} onChange={(event) => patch({ deliveryTime: event.target.value })} />
          </Field>
          <Field label="Địa điểm giao">
            <Input value={form.deliveryPlace} onChange={(event) => patch({ deliveryPlace: event.target.value })} />
          </Field>
          <Field label="Phí vận chuyển (đ)">
            <NumberInput
              value={form.shippingCost}
              onChange={(shippingCost) => patch({ shippingCost })}
              label="Phí vận chuyển"
            />
          </Field>
          <label className="flex cursor-pointer items-center gap-2 self-end pb-2 text-sm font-medium">
            <Checkbox
              checked={form.sampleReady}
              onCheckedChange={(checked) => patch({ sampleReady: checked === true })}
              aria-label="Có mẫu"
            />
            Có mẫu
          </label>
          <Field label="Ghi chú cho người yêu cầu" wide>
            <Textarea rows={2} value={form.note} onChange={(event) => patch({ note: event.target.value })} />
          </Field>
        </div>

        <DialogFooter className={cn('gap-2', isOptionZero && 'sm:justify-between')}>
          {isOptionZero && (
            <Button type="button" variant="outline" disabled={pending} onClick={() => void reset()}>
              <RotateCcw />
              Khôi phục ban đầu
            </Button>
          )}
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Hủy
            </Button>
            <Button type="button" disabled={pending} onClick={submit}>
              {updateMutation.isPending && <Loader2 className="animate-spin" />}
              Lưu
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Field({ label, wide = false, children }: { label: string; wide?: boolean; children: ReactNode }) {
  return (
    <div className={cn('min-w-0 space-y-1.5', wide && 'sm:col-span-2')}>
      <span className="text-sm font-medium">{label}</span>
      {children}
    </div>
  )
}

function NumberInput({
  value,
  onChange,
  label,
}: {
  value: string
  onChange: (value: string) => void
  label: string
}) {
  return (
    <Input
      type="number"
      min={0}
      inputMode="decimal"
      aria-label={label}
      className="text-right tabular-nums"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  )
}
