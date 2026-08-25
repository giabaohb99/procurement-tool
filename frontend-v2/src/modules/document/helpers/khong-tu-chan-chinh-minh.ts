import type { AuthUser } from '@/core/auth/auth-types'
import { SUBJECT_KIND } from '../types/document-access'

/**
 * Id mà người đang đăng nhập **KHÔNG được tự đưa vào cụm «không cho phép»**.
 *
 * Trả `0` nghĩa là không phải chặn ai: đang khai chiều *cho phép*, hoặc loại đối
 * tượng không dính tới người này (vai trò), hoặc tài khoản chưa gắn hồ sơ nhân
 * sự nên không có gì để so.
 *
 * ⚠️ Đây là lỗi người dùng đã dính thật (24/08/2026): tự đưa mình vào cụm «không
 * cho phép» rồi bấm Tạo → văn bản ra đời mà **chính người lập không còn quyền
 * xem**. Danh sách hiện «Tổng 0 văn bản» kèm ba toast đỏ liên tiếp, và không ai
 * gỡ hộ được vì họ cũng không mở nổi văn bản đó nữa.
 *
 * Chặn cả PHÒNG BAN và PHÁP NHÂN của mình, không riêng cá nhân: chặn phòng mình
 * thì mình nằm trong phòng đó, kết cục y hệt.
 *
 * Vai trò (`SUBJECT_KIND.role`) cố ý KHÔNG chặn — hồ sơ đăng nhập không nói
 * người này đang giữ những vai trò nào, mà đoán mò rồi khóa nhầm một lựa chọn
 * hợp lệ thì phiền hơn.
 */
export function idKhongDuocTuChan(
  subjectKind: number,
  user: AuthUser | null | undefined,
  isDeny: boolean,
): number {
  if (!isDeny || !user) return 0
  if (subjectKind === SUBJECT_KIND.employee) return user.employee_id ?? 0
  if (subjectKind === SUBJECT_KIND.department) return user.department_id ?? 0
  if (subjectKind === SUBJECT_KIND.company) return user.company_id ?? 0
  return 0
}
