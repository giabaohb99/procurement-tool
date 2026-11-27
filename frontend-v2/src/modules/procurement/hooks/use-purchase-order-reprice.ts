import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { queryKeys } from '@/shared/constants/query-keys'
import { confirm as confirmDialog } from '@/shared/ui/confirm-dialog'
import { purchaseOrderApi } from '../api/purchase-order-api'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import {
  applyRepriceDraft,
  collectRepriceLines,
  findLinesBelowReceived,
  summarizeReprice,
  updateRepriceDraft,
  updateRepriceDraftFromItems,
  type RepriceDraft,
} from '../utils/purchase-order-reprice'

/** Câu hiện trên ô khi danh sách dòng bị chặn chưa về — chưa biết thì chưa cho sửa. */
const LOCKS_LOADING_REASON = 'Đang kiểm tra dòng này có sửa giá được không…'

/**
 * Chế độ "Sửa giá" của chi tiết ĐMH đã duyệt: bật / tắt, bản nháp giá, danh sách dòng bị chặn và
 * lượt lưu `POST /reprice`. Bảng dòng và hộp chi tiết dòng dùng chung một bản nháp này.
 */
export function usePurchaseOrderReprice(purchaseOrderId: number, savedItems: PurchaseOrderItem[]) {
  const queryClient = useQueryClient()
  const [active, setActive] = useState(false)
  const [draft, setDraft] = useState<RepriceDraft>({})
  //  `disabled={isPending}` chỉ đúng ở lượt vẽ sau — bấm đúp vẫn ra hai request. Chặn trong cùng tick.
  const savingRef = useRef(false)

  const locksQuery = useQuery({
    queryKey: queryKeys.procurement.purchaseOrderRepriceLocks(purchaseOrderId),
    queryFn: () => purchaseOrderApi.getRepriceLocks(purchaseOrderId),
    enabled: active && purchaseOrderId > 0,
  })

  const mutation = useMutation({
    mutationFn: () =>
      purchaseOrderApi.reprice(purchaseOrderId, {
        items: collectRepriceLines(savedItems, draft),
      }),
    onSuccess: ({ message }) => {
      toast.success(message || 'Đã cập nhật giá')
      setActive(false)
      setDraft({})
      //  Công nợ, tồn kho, YCTT nháp đều tính lại phía máy chủ.
      void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.finance.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.inventory.all })
    },
  })

  const summary = useMemo(() => summarizeReprice(savedItems, draft), [savedItems, draft])
  const savedById = useMemo(
    () => new Map(savedItems.filter((item) => item.id).map((item) => [item.id, item])),
    [savedItems],
  )

  function lockReasonOf(item: PurchaseOrderItem): string {
    if (!item.id) return 'Dòng chưa lưu'
    if (locksQuery.isPending) return LOCKS_LOADING_REASON
    if (locksQuery.isError) return 'Không kiểm tra được dòng này — tải lại trang rồi thử lại'
    return locksQuery.data?.[String(item.id)] ?? ''
  }

  function originalOf(item: PurchaseOrderItem): PurchaseOrderItem | undefined {
    return item.id ? savedById.get(item.id) : undefined
  }

  function start() {
    setDraft({})
    setActive(true)
  }

  async function cancel() {
    if (summary.changedCount > 0) {
      const ok = await confirmDialog({
        title: 'Bỏ phần sửa giá?',
        message: `Đã sửa ${summary.changedCount} dòng chưa lưu. Thoát là mất phần vừa sửa.`,
      })
      if (!ok) return
    }
    setActive(false)
    setDraft({})
  }

  async function save() {
    if (savingRef.current) return
    if (summary.changedCount === 0) {
      toast.error('Chưa sửa dòng nào')
      return
    }
    const belowReceived = findLinesBelowReceived(savedItems, draft)
    if (belowReceived.length) {
      toast.error(`SL đặt không được nhỏ hơn SL đã nhận: ${belowReceived.join(', ')}`)
      return
    }
    savingRef.current = true
    try {
      await mutation.mutateAsync()
    } catch {
      //  Lỗi 400 của máy chủ đã hiện bằng toast chung của httpClient; giữ nguyên bản nháp để sửa tiếp.
    } finally {
      savingRef.current = false
    }
  }

  return {
    active,
    summary,
    saving: mutation.isPending,
    start,
    cancel,
    save,
    lockReasonOf,
    originalOf,
    /** Dòng để vẽ: bản đã lưu đè phần giá đang sửa. Chế độ tắt thì trả nguyên danh sách. */
    applyTo: (items: PurchaseOrderItem[]) => (active ? applyRepriceDraft(items, draft) : items),
    /** Bảng gửi lại cả danh sách sau mỗi ô gõ. */
    updateFromItems: (nextItems: PurchaseOrderItem[]) =>
      setDraft((current) => updateRepriceDraftFromItems(current, savedItems, nextItems)),
    /** Hộp chi tiết gửi lại một dòng. */
    updateLine: (next: PurchaseOrderItem) => {
      const original = originalOf(next)
      if (original) setDraft((current) => updateRepriceDraft(current, original, next))
    },
  }
}

export type PurchaseOrderRepriceState = ReturnType<typeof usePurchaseOrderReprice>
