import { LEAVE_STATUS } from '../types/leave'

/**
 * Ba kết cục KHÔNG-DUYỆT. Cả ba ghi lý do vào chung một cột `decision_note` ở
 * backend, nên chỗ nào muốn in lý do cũng phải hỏi trạng thái trước: đơn ĐÃ
 * DUYỆT cũng có thể có ghi chú, mà tô đỏ ghi chú đó thì đọc thành bị từ chối.
 */
export const BAD_LEAVE_OUTCOMES: number[] = [
  LEAVE_STATUS.REJECTED,
  LEAVE_STATUS.RETURNED,
  LEAVE_STATUS.CANCELLED,
]

export function isBadLeaveOutcome(status: number): boolean {
  return BAD_LEAVE_OUTCOMES.includes(status)
}

/**
 * Lý do không-duyệt, đã dọn để in trên MỘT DÒNG (ô trạng thái của bảng).
 *
 * Ba thứ phải dọn, cả ba đều đã thấy trong dữ liệu thật:
 *  · khoảng trắng thừa hai đầu — người ta dán chữ vào ô lý do;
 *  · **xuống dòng và tab** — trong ô một dòng, `\n` không tạo dòng mới mà biến
 *    thành một khoảng trắng khổng lồ giữa hai chữ, hoặc bị nuốt mất tùy trình
 *    duyệt. Gộp mọi cụm trắng thành đúng một dấu cách;
 *  · lý do của đơn KHÔNG thuộc ba kết cục xấu — trả rỗng để chỗ gọi khỏi phải
 *    tự nhớ luật.
 *
 * KHÔNG cắt bớt độ dài ở đây: cắt bằng mã là mất chữ thật, còn cắt bằng CSS
 * (`truncate`) thì chuỗi đầy đủ vẫn nằm trong `title` để rê chuột đọc tiếp.
 * Cột `decision_note` chặn ở 500 ký tự, nhưng hàm này không dựa vào con số đó.
 */
export function decisionNoteOf(request: {
  status: number
  decision_note?: string | null
}): string {
  if (!isBadLeaveOutcome(request.status)) return ''
  return (request.decision_note ?? '').replace(/\s+/g, ' ').trim()
}

/**
 * Nhãn cho ô lý do, nói rõ đây là lý do của VIỆC GÌ.
 *
 * Ba kết cục xấu dùng chung cột `decision_note`, nên một đoạn chữ trần trụi
 * đứng cạnh huy hiệu đọc thành lý do NGHỈ (cột «Lý do» ngay bên phải cũng là
 * chữ tự do) chứ không phải lý do bị chặn.
 */
export function decisionNoteLabelOf(status: number): string {
  if (status === LEAVE_STATUS.REJECTED) return 'Lý do từ chối'
  if (status === LEAVE_STATUS.RETURNED) return 'Lý do trả về'
  if (status === LEAVE_STATUS.CANCELLED) return 'Lý do hủy yêu cầu'
  return ''
}
