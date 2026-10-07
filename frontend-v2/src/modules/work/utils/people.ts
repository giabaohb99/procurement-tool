/**
 * Cách hiển thị NGƯỜI trong phân hệ Công việc.
 *
 * Tách khỏi `task-card.tsx` vì panel chi tiết cũng vẽ avatar y hệt — hai bản
 * chép tay thì thẻ và panel lệch chữ tắt của cùng một người.
 */

import { nameInitials } from '@/shared/utils/name-initials'

/**
 * Chữ tắt trên avatar: chữ cái đầu của HAI TỪ CUỐI («Huỳnh Gia Bảo» → «GB»),
 * cùng luật với bảng dự án và menu tài khoản. Trước bao-CR-604 thẻ việc và
 * nhật ký lấy hai chữ đầu của TỪ CUỐI («BẢ») — đại ca soi 07/10 thấy xấu và
 * khó nhận ra người. Tên rỗng trả «?» để ô không trống.
 */
export function initials(name: string): string {
  return nameInitials(name) || '?'
}

/** Tên bày ra cho một nhân sự; chưa có tên thì lấy mã số làm chỗ bấu víu. */
export function personName(name: string, employeeId: number): string {
  return name || `Nhân sự #${employeeId}`
}
