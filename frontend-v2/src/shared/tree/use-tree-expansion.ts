import { useCallback, useMemo, useState } from 'react'

export interface UseTreeExpansionOptions {
  /** id các node mở sẵn lúc dựng lần đầu. */
  defaultExpandedIds?: (string | number)[]
}

/**
 * Giữ TẬP HỢP node đang MỞ của một `TreeView` — tách khỏi component vẽ để nơi
 * dùng tự quyết định nguồn trạng thái (ví dụ mở sẵn theo id đang chọn trên URL)
 * mà không phải đọc vào bên trong `TreeView`.
 */
export function useTreeExpansion(options: UseTreeExpansionOptions = {}) {
  const [expandedIds, setExpandedIds] = useState<Set<string | number>>(
    () => new Set(options.defaultExpandedIds ?? []),
  )

  const isExpanded = useCallback((id: string | number) => expandedIds.has(id), [expandedIds])

  const toggle = useCallback((id: string | number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const expand = useCallback((id: string | number) => {
    setExpandedIds((prev) => (prev.has(id) ? prev : new Set(prev).add(id)))
  }, [])

  const collapse = useCallback((id: string | number) => {
    setExpandedIds((prev) => {
      if (!prev.has(id)) return prev
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  /**
   * Mở ĐỦ mọi tổ tiên của một node — dùng khi cần đưa một node đang nằm trong
   * nhánh gập ra chỗ nhìn thấy được (dán link thẳng tới id đó, tìm rồi nhảy tới…).
   * Nhận cả MẢNG id tổ tiên (gốc → gần nhất), không phải một id đơn.
   */
  const expandAncestors = useCallback((ancestorIds: (string | number)[]) => {
    if (ancestorIds.length === 0) return
    setExpandedIds((prev) => {
      const next = new Set(prev)
      for (const id of ancestorIds) next.add(id)
      return next
    })
  }, [])

  const expandAll = useCallback((ids: (string | number)[]) => {
    setExpandedIds(new Set(ids))
  }, [])

  const collapseAll = useCallback(() => {
    setExpandedIds(new Set())
  }, [])

  return useMemo(
    () => ({
      expandedIds,
      isExpanded,
      toggle,
      expand,
      collapse,
      expandAncestors,
      expandAll,
      collapseAll,
    }),
    [expandedIds, isExpanded, toggle, expand, collapse, expandAncestors, expandAll, collapseAll],
  )
}
