/**
 * duoc-CR-784 — hộp thoại đặt ngưỡng giá SÀN / TRẦN cho một mã (một dòng mỗi mã, bảng
 * `tab_product_price_limit`). Ô bỏ trống = không đặt phía đó. Giá đang dùng ra ngoài ngưỡng thì Bảng giá
 * và màn Tác động tô đỏ.
 */
import { Loader2 } from 'lucide-react'
import { useState } from 'react'

import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'

import {
  usePackagingPriceLimit,
  useSavePackagingPriceLimit,
} from '../hooks/use-packaging-price-list'
import type { PackagingPriceLimit } from '../types/packaging-cost-types'

interface PackagingPriceLimitDialogProps {
  code: string
  name?: string
  onClose: () => void
}

export function PackagingPriceLimitDialog({ code, name, onClose }: PackagingPriceLimitDialogProps) {
  const { data, isLoading } = usePackagingPriceLimit(code)

  return (
    <Dialog open onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Ngưỡng giá {code}</DialogTitle>
          <DialogDescription>
            {name || 'Đặt giá sàn / trần để cảnh báo khi giá mua hoặc báo giá ra ngoài khoảng.'}
          </DialogDescription>
        </DialogHeader>
        {isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          //  Dựng form SAU khi có dữ liệu để state khởi tạo đúng ngưỡng đang có (khỏi effect đồng bộ).
          <LimitForm code={code} existing={data ?? null} onClose={onClose} />
        )}
      </DialogContent>
    </Dialog>
  )
}

function LimitForm({
  code,
  existing,
  onClose,
}: {
  code: string
  existing: PackagingPriceLimit | null
  onClose: () => void
}) {
  const [floor, setFloor] = useState(Number(existing?.floor_price ?? 0))
  const [ceiling, setCeiling] = useState(Number(existing?.ceiling_price ?? 0))
  const [note, setNote] = useState(existing?.note ?? '')
  const [error, setError] = useState<string | null>(null)
  const save = useSavePackagingPriceLimit()
  const once = useSingleFlight()

  const submit = () =>
    once(async () => {
      //  Ô xóa trắng trả 0 → coi là "không đặt" (gửi null), không phải ngưỡng 0 đồng.
      const floorPrice = floor > 0 ? floor : null
      const ceilingPrice = ceiling > 0 ? ceiling : null
      if (floorPrice != null && ceilingPrice != null && floorPrice > ceilingPrice) {
        setError('Giá sàn không được lớn hơn giá trần.')
        return
      }
      setError(null)
      await save.mutateAsync({
        id: existing?.id ?? null,
        payload: {
          product_code: code,
          floor_price: floorPrice,
          ceiling_price: ceilingPrice,
          note: note.trim(),
        },
      })
      onClose()
    })

  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault()
        void submit()
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="limit-floor">Giá sàn</Label>
          <NumberInput
            id="limit-floor"
            placeholder="Không đặt"
            maxDecimals={PRICE_MAX_DECIMALS}
            value={floor}
            onChange={setFloor}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="limit-ceiling">Giá trần</Label>
          <NumberInput
            id="limit-ceiling"
            placeholder="Không đặt"
            maxDecimals={PRICE_MAX_DECIMALS}
            value={ceiling}
            onChange={setCeiling}
          />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="limit-note">Ghi chú</Label>
        <Textarea
          id="limit-note"
          rows={2}
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <DialogFooter>
        <Button type="button" variant="outline" disabled={save.isPending} onClick={onClose}>
          Hủy
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {save.isPending && <Loader2 className="size-4 animate-spin" />}
          Lưu ngưỡng
        </Button>
      </DialogFooter>
    </form>
  )
}
