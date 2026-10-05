import { useState } from 'react'

import type { EmployeeWorkHistoryFormValues } from '../schemas/employee-work-history-schema'
import type { EmployeeWorkHistory } from '../types/employee-work-history'

/** Tùy chọn khi mở hộp ở chế độ TẠO MỚI — xem `openCreate`. */
export interface OpenCreateOptions {
  /** Ép Số QĐ bắt buộc (nút «+ Thêm quyết định» của tab Quyết định bổ nhiệm). */
  requireDecisionNo?: boolean
  /** Đè tiêu đề hộp lúc tạo mới. Bỏ trống = giữ tiêu đề mặc định «Thêm quá trình công tác». */
  createTitle?: string
}

/**
 * Điều phối hộp thêm/sửa «Quá trình công tác» (`EmployeeWorkHistoryFormDialog`)
 * — NÂNG lên chỗ chung (đại ca chốt 03/10/2026, mục 3) để cả tab «Quá trình
 * công tác» (`openCreate`/`openEdit`) VÀ tab «Quyết định bổ nhiệm» (chỉ
 * `openCreate` — khu đó không có nút Sửa) cùng dùng, không chép logic ra hai
 * bản. Mỗi tab tự gọi hook này MỘT LẦN và tự dựng `<EmployeeWorkHistoryFormDialog>`
 * của riêng nó — hai hook KHÔNG chia sẻ state (không cần, vì chỉ một tab mở
 * hộp tại một thời điểm) nhưng CHIA SẺ đúng một bộ quy tắc chuyển trạng thái.
 */
export function useEmployeeWorkHistoryEditorDialog() {
  const [open, setOpen] = useState(false)
  const [editRow, setEditRow] = useState<EmployeeWorkHistory | null>(null)
  const [seed, setSeed] = useState<Partial<EmployeeWorkHistoryFormValues>>()
  const [requireDecisionNo, setRequireDecisionNo] = useState(false)
  const [createTitle, setCreateTitle] = useState<string>()

  function openCreate(initial?: Partial<EmployeeWorkHistoryFormValues>, options?: OpenCreateOptions) {
    setEditRow(null)
    setSeed(initial)
    setRequireDecisionNo(Boolean(options?.requireDecisionNo))
    setCreateTitle(options?.createTitle)
    setOpen(true)
  }

  function openEdit(row: EmployeeWorkHistory) {
    setEditRow(row)
    setSeed(undefined)
    setRequireDecisionNo(false)
    setCreateTitle(undefined)
    setOpen(true)
  }

  return {
    open,
    onOpenChange: setOpen,
    editRow,
    seed,
    requireDecisionNo,
    createTitle,
    openCreate,
    openEdit,
  }
}
