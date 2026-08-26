import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { Mailbox, MailboxInput } from '../types/mailbox'

const BASE_URL = '/api/mailboxes'

export const mailboxApi = {
  list: () => apiGet<Mailbox[]>(BASE_URL),

  get: (id: number) => apiGet<Mailbox>(`${BASE_URL}/${id}`),

  create: (input: MailboxInput) => apiPost<Mailbox>(BASE_URL, input),

  update: (id: number, input: MailboxInput) =>
    apiPatch<Mailbox>(`${BASE_URL}/${id}`, input),

  /**
   * Xóa hẳn mật khẩu ứng dụng — cố ý là một lời gọi RIÊNG.
   *
   * Không gộp vào `update` bằng cách gửi chuỗi rỗng: rỗng ở `update` nghĩa là
   * "giữ nguyên" (xem `MailboxInput.smtp_password`). Hai ý nghĩa khác nhau thì
   * phải là hai đường khác nhau, không thì sửa một cái nhãn cũng làm hộp thư
   * ngừng gửi được.
   */
  clearPassword: (id: number) => apiDelete<Mailbox>(`${BASE_URL}/${id}/password`),

  /** Ngừng dùng (không xóa hẳn — nhật ký thư cũ còn trỏ vào đây). */
  deactivate: (id: number) => apiDelete<Mailbox>(`${BASE_URL}/${id}`),
}
