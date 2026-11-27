/**
 * duoc-CR-784 — hộp thoại "+ Báo giá mới" / sửa báo giá NCC (bám `#mQuote` của bản mẫu).
 *
 * Viết riêng thay vì dùng form dựng sẵn của `shared/crud` vì ô đơn giá phải nhập kiểu vi-VN
 * (`NumberInput`, 4 số lẻ) và cần mở sẵn mã từ dòng Bảng giá (`defaultCode`). Vẫn khớp khuôn
 * `CrudFormDialogProps` để gắn làm `FormDialog` của danh sách Báo giá.
 *
 * Báo giá có `valid_from` ở tương lai VẪN tính ngay là giá mới (Q2, chốt 20/11) — để xem trước tác động.
 */
import { Loader2 } from 'lucide-react'
import { useMemo, useState } from 'react'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { useCrudDelete, useCrudSave, type CrudFormDialogProps } from '@/shared/crud'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
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
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { toDateInputValue } from '@/shared/utils/format-date'

import { PACKAGING_QUOTE_API } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingQuote } from '../types/packaging-cost-types'

interface PackagingQuoteDialogProps extends Partial<CrudFormDialogProps<PackagingQuote>> {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Mở từ một dòng Bảng giá — mã điền sẵn và khóa lại. */
  defaultCode?: string
}

interface QuoteDraft {
  product_code: string
  supplier_code: string
  price: number
  vat: number
  valid_from: string
  note: string
}

function buildDraft(item: PackagingQuote | null | undefined, defaultCode?: string): QuoteDraft {
  return {
    product_code: item?.product_code ?? defaultCode ?? '',
    supplier_code: item?.supplier_code ?? '',
    price: Number(item?.price ?? 0),
    vat: Number(item?.vat ?? 0),
    valid_from: item?.valid_from ?? toDateInputValue(new Date()),
    note: item?.note ?? '',
  }
}

/** Câu chặn đầu tiên của bản nháp; `null` = gửi được. Backend vẫn kiểm lại mã có trong danh mục. */
function validateQuoteDraft(draft: QuoteDraft): string | null {
  if (!draft.product_code.trim()) return 'Nhập mã vật tư bao bì.'
  if (!(draft.price > 0)) return 'Nhập đơn giá báo giá (lớn hơn 0).'
  if (!draft.valid_from) return 'Chọn ngày hiệu lực.'
  return null
}

export function PackagingQuoteDialog({
  open,
  onOpenChange,
  item,
  defaultCode,
}: PackagingQuoteDialogProps) {
  //  Mở lại hộp là dựng lại bản nháp — component cha gắn `key` theo lần mở nên state không dính lần trước.
  const [draft, setDraft] = useState<QuoteDraft>(() => buildDraft(item, defaultCode))
  const [error, setError] = useState<string | null>(null)
  const save = useCrudSave<PackagingQuote>(PACKAGING_QUOTE_API, 'Báo giá', [packagingCostKeys.all])
  const remove = useCrudDelete(PACKAGING_QUOTE_API, 'Báo giá', [packagingCostKeys.all])
  //  `disabled={isPending}` không chặn được bấm đúp — `useRef` trong hook này mới chặn (duoc-CR-317).
  const once = useSingleFlight()
  const pending = save.isPending || remove.isPending
  //  Mã NCC chọn từ danh mục NCC (cùng cách ô NCC ở màn ĐMH). Thiếu quyền đọc danh mục thì lùi về ô gõ tay
  //  để vẫn nhập được — đừng gọi API cho backend trả 403.
  const { can } = usePermission()
  const canPickSupplier = can('supplier', 'read')
  const { data: suppliersData } = useSuppliers(
    { page_size: 1000, is_active: true },
    { enabled: canPickSupplier },
  )
  const supplierOptions = useMemo(
    () =>
      (suppliersData?.items ?? []).map((supplier) => ({
        value: supplier.code,
        label: `${supplier.code} · ${supplier.name}`,
      })),
    [suppliersData],
  )
  const codeLocked = Boolean(item || defaultCode)

  const patch = (next: Partial<QuoteDraft>) => setDraft((prev) => ({ ...prev, ...next }))

  const submit = () =>
    once(async () => {
      const problem = validateQuoteDraft(draft)
      setError(problem)
      if (problem) return
      await save.mutateAsync({
        id: item?.id,
        values: {
          ...draft,
          product_code: draft.product_code.trim().toUpperCase(),
          //  Mã chọn từ danh mục giữ nguyên chữ hoa/thường của danh mục; chỉ ô gõ tay mới tự viết hoa.
          supplier_code: canPickSupplier
            ? draft.supplier_code.trim()
            : draft.supplier_code.trim().toUpperCase(),
          note: draft.note.trim(),
        },
      })
      onOpenChange(false)
    })

  return (
    <Dialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <DialogContent
        className="sm:max-w-lg"
        //  Mở từ dòng Bảng giá thì mã đã có — đưa con trỏ thẳng vào ô đơn giá.
        onOpenAutoFocus={(event) => {
          if (!codeLocked) return
          event.preventDefault()
          document.getElementById('quote-price')?.focus()
        }}
      >
        <DialogHeader>
          <DialogTitle>{item ? `Sửa báo giá ${item.product_code}` : 'Báo giá mới'}</DialogTitle>
          <DialogDescription>
            Giá VNĐ chưa VAT theo đơn vị tính của danh mục. Báo giá mới nhất của một mã là giá mới ở
            màn Tác động.
          </DialogDescription>
        </DialogHeader>

        <form
          className="grid gap-3 sm:grid-cols-2"
          onSubmit={(event) => {
            event.preventDefault()
            void submit()
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="quote-code">
              Mã VTBB <RequiredMark />
            </Label>
            {codeLocked ? (
              //  Ô chỉ xem dùng `ReadOnlyValue` (bôi đen / copy được), không `Input readOnly` trông như ô nhập.
              <ReadOnlyValue>{draft.product_code.toUpperCase()}</ReadOnlyValue>
            ) : (
              <Input
                id="quote-code"
                value={draft.product_code}
                placeholder="Vd: NAP0085"
                onChange={(event) => patch({ product_code: event.target.value })}
              />
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="quote-supplier">Nhà cung cấp</Label>
            {canPickSupplier ? (
              //  Mã đang lưu mà không còn trong danh mục (NCC đã ngừng) vẫn hiện nguyên mã, không bị làm trống.
              <SearchSelect
                id="quote-supplier"
                searchInTrigger
                clearable
                value={draft.supplier_code}
                options={supplierOptions}
                placeholder="Bỏ trống nếu chưa rõ"
                searchPlaceholder="Tìm theo mã hoặc tên NCC…"
                onChange={(supplier_code) => patch({ supplier_code })}
              />
            ) : (
              <Input
                id="quote-supplier"
                value={draft.supplier_code}
                placeholder="Bỏ trống nếu chưa rõ"
                onChange={(event) => patch({ supplier_code: event.target.value })}
              />
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="quote-price">
              Đơn giá (VNĐ, chưa VAT) <RequiredMark />
            </Label>
            <NumberInput
              id="quote-price"
              maxDecimals={PRICE_MAX_DECIMALS}
              value={draft.price}
              onChange={(price) => patch({ price })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="quote-vat">VAT (%)</Label>
            <NumberInput
              id="quote-vat"
              max={99.99}
              maxDecimals={2}
              value={draft.vat}
              onChange={(vat) => patch({ vat })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="quote-from">
              Ngày hiệu lực <RequiredMark />
            </Label>
            <DatePicker
              id="quote-from"
              value={draft.valid_from}
              onChange={(valid_from) => patch({ valid_from })}
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="quote-note">Ghi chú</Label>
            <Textarea
              id="quote-note"
              rows={2}
              value={draft.note}
              onChange={(event) => patch({ note: event.target.value })}
            />
          </div>

          {error && <p className="text-sm text-destructive sm:col-span-2">{error}</p>}

          <DialogFooter className="sm:col-span-2">
            {item && (
              <PermissionGate entity="packaging_price_list" action="delete">
                <div className="sm:mr-auto">
                  <DeleteConfirmButton
                    recordName={`báo giá ${item.product_code}`}
                    pending={remove.isPending}
                    onConfirm={async () => {
                      await remove.mutateAsync(item.id)
                      onOpenChange(false)
                    }}
                  />
                </div>
              </PermissionGate>
            )}
            <Button
              type="button"
              variant="outline"
              disabled={pending}
              onClick={() => onOpenChange(false)}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={pending}>
              {save.isPending && <Loader2 className="size-4 animate-spin" />}
              {item ? 'Lưu thay đổi' : 'Lưu báo giá'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
