import type { PurchaseOrderDetail } from '../types/purchase-order-detail'

type Row = { id?: number }

/**
 * bao-CR-758 — dữ liệu ĐMH vừa nạp lại từ máy chủ mà màn hình đang có phần SỬA CHƯA LƯU.
 *
 * Trước đây trang thay nguyên bản nháp bằng bản máy chủ mỗi khi dữ liệu đơn đổi (`useHasChanged`):
 * lượt nạp lại của lần Lưu trước về muộn, hay một thao tác khác làm mới đơn (đổi tình trạng hồ sơ,
 * tiến độ dòng, chi phí), là giá người dùng vừa gõ mất sạch — bấm Lưu thì gửi lên giá cũ, đúng
 * cảnh "gõ giá mới mà lưu không ăn, phải tải lại trang" ở PO01178.
 *
 * Gộp ba bên: `base` là bản máy chủ mà bản nháp dựng từ đó. Ô nào bản nháp khác `base` là người
 * dùng đã sửa -> giữ; còn lại lấy bản máy chủ mới. Dòng hàng / dòng chi phí khớp theo `id`; dòng
 * chưa lưu (chưa có id) giữ nguyên; dòng người dùng đã bỏ thì vẫn bỏ.
 */
export function rebasePurchaseOrderDraft(
  base: PurchaseOrderDetail,
  draft: PurchaseOrderDetail,
  server: PurchaseOrderDetail,
): PurchaseOrderDetail {
  if (draft === base) return server
  const next = mergeChangedKeys(base, draft, server) as PurchaseOrderDetail
  next.items = rebaseRows(base.items, draft.items, server.items)
  next.import_costs = rebaseRows(base.import_costs ?? [], draft.import_costs ?? [], server.import_costs ?? [])
  return next
}

function mergeChangedKeys<T extends object>(base: T, draft: T, server: T): T {
  const next = { ...server }
  for (const key of Object.keys(draft) as (keyof T)[]) {
    if (key === 'items' || key === 'import_costs') continue
    if (!Object.is(draft[key], base[key])) next[key] = draft[key]
  }
  return next
}

function rebaseRows<T extends Row>(base: T[], draft: T[], server: T[]): T[] {
  if (draft === base) return server
  const baseById = new Map(base.filter((row) => row.id).map((row) => [row.id, row]))
  const serverById = new Map(server.filter((row) => row.id).map((row) => [row.id, row]))
  const merged: T[] = []
  for (const row of draft) {
    if (!row.id) {
      merged.push(row)                       // dòng mới chưa lưu
      continue
    }
    const before = baseById.get(row.id)
    const latest = serverById.get(row.id)
    if (!latest) {
      //  Máy chủ đã bỏ dòng: người dùng không đụng tới thì bỏ theo, đã sửa thì giữ lại để họ thấy.
      if (before && row !== before) merged.push(row)
      continue
    }
    merged.push(!before || row === before ? latest : mergeChangedKeys(before, row, latest))
  }
  //  Dòng máy chủ mới có (người khác thêm) mà bản gốc chưa có.
  for (const row of server) {
    if (row.id && !baseById.has(row.id) && !draft.some((current) => current.id === row.id)) {
      merged.push(row)
    }
  }
  return merged
}
