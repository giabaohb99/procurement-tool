import { Loader2, SlidersHorizontal } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useWarehouseOptions } from '../hooks/use-inventory-catalog'
import { useAdjustInventory, useInventoryLine } from '../hooks/use-inventory'
import type { InventoryItem } from '../types/inventory'
import { InventoryProductPicker } from './inventory-product-picker'

/** Số lượng và đơn giá giữ dạng CHUỖI khi đang gõ — số 0 ép sẵn thì phải xóa mới nhập được. */
interface AdjustForm {
  companyId: string
  warehouseCode: string
  productCode: string
  productName: string
  unit: string
  qty: string
  unitPrice: string
  note: string
}

const EMPTY_FORM: AdjustForm = {
  companyId: '',
  warehouseCode: '',
  productCode: '',
  productName: '',
  unit: '',
  qty: '',
  unitPrice: '',
  note: '',
}

interface InventoryAdjustDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Dòng tồn được chọn — có thì điền sẵn; `null` = lập điều chỉnh từ đầu. */
  preset: InventoryItem | null
}

/**
 * Điều chỉnh tồn kho bằng tay.
 *
 * Số nhập vào là CHÊNH LỆCH (+ tăng / − giảm), không phải tồn mới — backend cộng
 * thêm một dòng vào sổ phát sinh rồi tính lại số dư, nên mọi lần chỉnh đều còn
 * dấu vết. Không có đường nào "đặt thẳng tồn = N" và đó là chủ ý.
 */
export function InventoryAdjustDialog({
  open,
  onOpenChange,
  preset,
}: InventoryAdjustDialogProps) {
  const [form, setForm] = useState<AdjustForm>(EMPTY_FORM)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: warehouses } = useWarehouseOptions()
  const adjust = useAdjustInventory()

  // Mở hộp thoại (hoặc đổi dòng được chọn) -> dựng lại form. Gọi hook ra biến
  // riêng: `||` sẽ short-circuit làm hook thứ hai không chạy.
  const openChanged = useHasChanged(open)
  const presetChanged = useHasChanged(preset)
  if (openChanged || presetChanged) {
    setForm(
      preset
        ? {
            ...EMPTY_FORM,
            companyId: String(preset.company_id),
            warehouseCode: preset.warehouse_code,
            productCode: preset.product_code,
            productName: preset.product_name,
            unit: preset.unit,
          }
        : EMPTY_FORM,
    )
  }

  const companyId = Number(form.companyId) || 0
  const { data: currentLine } = useInventoryLine(
    companyId,
    form.warehouseCode,
    form.productCode,
  )
  const current = currentLine?.items[0]

  const qty = Number(form.qty) || 0
  const canSubmit =
    companyId > 0 && !!form.warehouseCode && !!form.productCode && qty !== 0

  async function submit() {
    if (!canSubmit) {
      toast.error('Chọn đủ công ty, kho, sản phẩm và nhập số lượng khác 0')
      return
    }
    await adjust.mutateAsync({
      company_id: companyId,
      warehouse_code: form.warehouseCode,
      product_code: form.productCode,
      product_name: form.productName,
      unit: form.unit,
      qty,
      // Bỏ trống thì gửi 0 để backend tự lấy đơn giá bình quân đang có.
      unit_price: Number(form.unitPrice) || 0,
      note: form.note,
    })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[96vw] overflow-y-auto sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>Điều chỉnh tồn kho</DialogTitle>
          <DialogDescription>
            Nhập phần CHÊNH LỆCH so với số đang có: <b>10</b> là nhập thêm 10,{' '}
            <b>-5</b> là giảm 5. Mỗi lần chỉnh là một dòng trong sổ phát sinh.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3">
          <div className="space-y-1.5">
            <Label>Công ty</Label>
            <Select
              value={form.companyId}
              onValueChange={(value) => setForm((state) => ({ ...state, companyId: value }))}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn công ty…" />
              </SelectTrigger>
              <SelectContent>
                {(companies?.items ?? []).map((company) => (
                  <SelectItem key={company.id} value={String(company.id)}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Kho</Label>
            <Select
              value={form.warehouseCode}
              onValueChange={(value) =>
                setForm((state) => ({ ...state, warehouseCode: value }))
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn kho…" />
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
            <Label>Sản phẩm</Label>
            <InventoryProductPicker
              code={form.productCode}
              name={form.productName}
              onPick={(product) =>
                setForm((state) => ({
                  ...state,
                  productCode: product.code,
                  productName: product.name,
                  // ĐVT lấy theo danh mục sản phẩm; danh mục để trống thì giữ ĐVT cũ.
                  unit: product.unit || state.unit,
                }))
              }
            />
          </div>

          {form.productCode && (
            <div className="rounded-lg border border-dashed bg-muted/40 px-3 py-2 text-sm">
              <p>
                <span className="text-muted-foreground">Đơn vị tính: </span>
                <b>{form.unit || '—'}</b>
              </p>
              <p>
                <span className="text-muted-foreground">Tồn hiện tại ở kho này: </span>
                <b className="tabular-nums">{formatQuantity(current?.qty ?? 0)}</b>
              </p>
              <p>
                <span className="text-muted-foreground">Đơn giá bình quân hiện tại: </span>
                <b className="tabular-nums">{formatUnitPrice(current?.avg_cost ?? 0)} đ</b>
              </p>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Số lượng (+ / −)</Label>
              <Input
                type="number"
                value={form.qty}
                placeholder="Ví dụ: 10 hoặc -5"
                onChange={(event) =>
                  setForm((state) => ({ ...state, qty: event.target.value }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label>Đơn giá điều chỉnh (đ)</Label>
              <Input
                type="number"
                step="0.0001"
                value={form.unitPrice}
                placeholder="Mặc định theo đơn giá bình quân"
                onChange={(event) =>
                  setForm((state) => ({ ...state, unitPrice: event.target.value }))
                }
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Lý do</Label>
            <Input
              value={form.note}
              placeholder="Kiểm kê, hàng hỏng, nhập tồn đầu kỳ…"
              onChange={(event) => setForm((state) => ({ ...state, note: event.target.value }))}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button disabled={!canSubmit || adjust.isPending} onClick={() => void submit()}>
            {adjust.isPending ? <Loader2 className="animate-spin" /> : <SlidersHorizontal />}
            Lưu điều chỉnh
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
