/**
 * Nút chính của hộp xếp ca (duoc-CR-761): nhãn nói đúng việc sẽ làm, và KHÔNG BAO GIỜ tắt mà không có lý do. Thuần,
 * không dính React — chân hộp chỉ việc bày `label` + `reason`.
 */

export interface ShiftSubmitInput {
  /** Đang gửi một lượt ghi. */
  pending: boolean
  /** Ô chưa có ca và mẫu tuần còn đang nạp (khung chưa bày). */
  templateLoading: boolean
  /** Mọi dòng khung hợp lệ (không trùng, Đến sau Từ, không quá 12 khung). */
  rowsValid: boolean
  /** Tổng số ô (người × ngày) của lượt lưu; > 1 = lưu hàng loạt. */
  cells: number
  /** Câu chặn của phần "Áp cùng ca" (vượt trần / có ô bị đơn nghỉ giữ); `null` = áp được. */
  bulkWarning: string | null
  /** Ô đang mở đã có ca riêng. */
  hasShift: boolean
  /** Người dùng đã sửa khung hoặc ghi chú. */
  dirty: boolean
}

export interface ShiftSubmitState {
  /** "Lưu" khi chỉ ô này; "Lưu cho N ô" khi có chọn thêm ngày / người. */
  label: string
  bulk: boolean
  enabled: boolean
  /** Vì sao nút đang tắt — luôn có khi `enabled` sai. */
  reason: string | null
}

export function resolveShiftSubmit(input: ShiftSubmitInput): ShiftSubmitState {
  const bulk = input.cells > 1
  const label = bulk ? `Lưu cho ${input.cells} ô` : 'Lưu'
  const reason = (() => {
    if (input.pending) return 'Đang lưu…'
    if (input.templateLoading) return 'Đang tải lịch tuần…'
    if (!input.rowsValid) return 'Còn khung giờ bị lỗi'
    if (bulk && input.bulkWarning) return 'Có ô không áp được — xem cảnh báo ở trên'
    //  Ô chưa có ca: chưa sửa gì thì không lưu (bấm nhầm Lưu sẽ biến mẫu tuần thành ca riêng). Lưu hàng loạt thì được:
    //  chép đúng khung đang thấy sang ô khác là một thay đổi thật.
    if (!bulk && !input.hasShift && !input.dirty) return 'Chưa thay đổi gì'
    return null
  })()
  return { label, bulk, enabled: reason === null, reason }
}
