import { ACTION } from '../types/approval'

/**
 * Màu của huy hiệu ứng với việc người duyệt đã bấm.
 *
 * **Từ chối** phải đỏ còn **trả lại** thì không: từ chối là phiếu chết hẳn, trả
 * lại là phiếu còn sống và người nộp sửa rồi gửi lại. Tô cùng màu là bảng nói
 * sai mức độ của việc đã xảy ra.
 */
export const ACTION_TONE: Record<number, 'default' | 'destructive' | 'outline' | 'secondary'> = {
  [ACTION.approve]: 'default',
  [ACTION.reject]: 'destructive',
  [ACTION.return]: 'secondary',
}
