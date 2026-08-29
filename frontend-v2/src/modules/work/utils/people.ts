/**
 * Cách hiển thị NGƯỜI trong phân hệ Công việc.
 *
 * Tách khỏi `task-card.tsx` vì panel chi tiết cũng vẽ avatar y hệt — hai bản
 * chép tay thì thẻ và panel lệch chữ tắt của cùng một người.
 */

/** Chữ tắt trên avatar: hai chữ cái đầu của TỪ CUỐI — tên Việt gọi theo tên. */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  return words[words.length - 1].slice(0, 2).toUpperCase()
}

/** Tên bày ra cho một nhân sự; chưa có tên thì lấy mã số làm chỗ bấu víu. */
export function personName(name: string, employeeId: number): string {
  return name || `Nhân sự #${employeeId}`
}
