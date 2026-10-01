import { useCallback, useMemo, useState } from 'react'

import type { LinesTableSelection } from '@/shared/data-table/lines-table'

interface UseLineSelectionOptions<T> {
  rows: T[]
  rowKey: (row: T, index: number) => string | number
  /** Tắt hẳn (không có cột tick) — vd phiếu đã gửi duyệt. */
  enabled?: boolean
  /** Dòng không cho tick (vd dòng đơn hàng đã hoàn thành / đã hủy). */
  isSelectable?: (row: T, index: number) => boolean
  unselectableReason?: string
}

/**
 * Tick chọn nhiều DÒNG trên bảng dòng chứng từ để xóa một lần — bao-CR-547 (đại ca chốt
 * 01/10/2026: chỉ ở form tạo hoặc phiếu Nháp).
 *
 * Dòng chưa lưu không có id nên khóa dòng là `rowKey` (có cả chỉ số); xóa xong thì nơi dùng gọi
 * `clear()` vì chỉ số đã trôi. `selectedIndexes` luôn tính lại từ `rows` hiện tại — dòng đã mất
 * khỏi mảng thì không còn trong lô, kể cả khi khóa cũ vẫn nằm trong `Set`.
 */
export function useLineSelection<T>({
  rows,
  rowKey,
  enabled = true,
  isSelectable,
  unselectableReason,
}: UseLineSelectionOptions<T>) {
  const [selectedKeys, setSelectedKeys] = useState<Set<string | number>>(new Set())

  const selectableIndexes = useMemo(
    () => rows.map((_, index) => index).filter((index) => !isSelectable || isSelectable(rows[index], index)),
    [rows, isSelectable],
  )
  const selectedIndexes = useMemo(
    () => selectableIndexes.filter((index) => selectedKeys.has(rowKey(rows[index], index))),
    [selectableIndexes, selectedKeys, rows, rowKey],
  )

  const clear = useCallback(() => setSelectedKeys(new Set()), [])

  const selection = useMemo<LinesTableSelection<T> | undefined>(() => {
    if (!enabled) return undefined
    const allSelected = selectableIndexes.length > 0 && selectedIndexes.length === selectableIndexes.length
    return {
      isSelected: (row, index) => selectedKeys.has(rowKey(row, index)),
      onToggle: (row, index) => {
        const key = rowKey(row, index)
        setSelectedKeys((prev) => {
          const next = new Set(prev)
          if (next.has(key)) next.delete(key)
          else next.add(key)
          return next
        })
      },
      onToggleAll: () => {
        setSelectedKeys(
          allSelected ? new Set() : new Set(selectableIndexes.map((index) => rowKey(rows[index], index))),
        )
      },
      allSelected,
      someSelected: selectedIndexes.length > 0,
      isSelectable,
      unselectableReason,
    }
  }, [enabled, selectableIndexes, selectedIndexes, selectedKeys, rowKey, rows, isSelectable, unselectableReason])

  return { selection, selectedIndexes, clear }
}
