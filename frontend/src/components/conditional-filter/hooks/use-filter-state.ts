import { useCallback, useState } from 'react'
import { newRowId } from '../helpers/new-row-id'
import type { Conjunction, FilterFieldDefinition, FilterState, FilterValue, OperatorType } from '../types'

const EMPTY: FilterState = { rows: [], conjunction: 'and' }

/** State NHÁP của bảng lọc — người dùng sửa thoải mái, chỉ khi bấm "Áp dụng" mới ghi lên URL.
 *  Port từ FilterCN (hooks/use-filter-state), thay crypto.randomUUID bằng newRowId. */
export function useFilterState(initial?: FilterState) {
  const [state, setState] = useState<FilterState>(initial || EMPTY)

  const addRow = useCallback(() => {
    setState((prev) => ({
      ...prev,
      rows: [...prev.rows, { id: newRowId(), field: null, operator: null, value: null }],
    }))
  }, [])

  const removeRow = useCallback((id: string) => {
    setState((prev) => ({ ...prev, rows: prev.rows.filter((r) => r.id !== id) }))
  }, [])

  // Đổi field → reset operator + giá trị (operator cũ có thể không hợp lệ với kiểu field mới)
  const updateField = useCallback((id: string, field: FilterFieldDefinition) => {
    setState((prev) => ({
      ...prev,
      rows: prev.rows.map((r) => (r.id === id ? { ...r, field, operator: null, value: null } : r)),
    }))
  }, [])

  // Đổi operator → reset giá trị (vd đang "bằng" (chuỗi) chuyển sang "trong khoảng" (mảng))
  const updateOperator = useCallback((id: string, operator: OperatorType) => {
    setState((prev) => ({
      ...prev,
      rows: prev.rows.map((r) => (r.id === id ? { ...r, operator, value: null } : r)),
    }))
  }, [])

  const updateValue = useCallback((id: string, value: FilterValue) => {
    setState((prev) => ({
      ...prev,
      rows: prev.rows.map((r) => (r.id === id ? { ...r, value } : r)),
    }))
  }, [])

  const setConjunction = useCallback((conjunction: Conjunction) => {
    setState((prev) => ({ ...prev, conjunction }))
  }, [])

  const reset = useCallback(() => setState(EMPTY), [])

  /** Nạp đè state từ ngoài (dùng khi URL đổi: bấm back, xóa chip, đổi trang danh sách) */
  const overrideState = useCallback((next: FilterState) => setState(next), [])

  return { state, addRow, removeRow, updateField, updateOperator, updateValue, setConjunction, reset, overrideState }
}

export type FilterStateApi = ReturnType<typeof useFilterState>
