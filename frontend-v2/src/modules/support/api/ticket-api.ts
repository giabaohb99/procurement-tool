import { apiGet, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Ticket, TicketDetail, TicketFile } from '../types/ticket'

/** Một tệp vừa tải lên, chờ gắn vào tin nhắn (kết quả `/upload-file`). */
export interface UploadedFile {
  file_id: number
  filename: string
  url: string
  content_type: string
  size: number
}

const TICKET_URL = '/api/tickets'
const ATTACHMENT_URL = '/api/attachments'

export const ticketApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Ticket>>(TICKET_URL, { params }),

  getById: (id: number) => apiGet<TicketDetail>(`${TICKET_URL}/${id}`),

  /** Tệp gửi kèm lúc TẠO phiếu (entity `ticket`). Tệp trong tin nhắn đã nằm sẵn ở `message.files`. */
  listAttachments: (id: number) =>
    apiGet<TicketFile[]>(ATTACHMENT_URL, { params: { entity: 'ticket', entity_id: id } }),

  /**
   * Tải tệp của MỘT tin nhắn lên trước, giữ `file_id`, rồi mới gắn vào tin nhắn
   * lúc gửi — giống bản v1: upload ngay khi chọn/dán/kéo-thả.
   */
  uploadMessageFiles: (files: File[]) => {
    const body = new FormData()
    body.append('entity', 'ticket_message')
    files.forEach((file) => body.append('files', file))
    return apiPost<UploadedFile[]>(`${ATTACHMENT_URL}/upload-file`, body)
  },

  /** Gửi một lượt trao đổi. Backend trả về CHI TIẾT phiếu đã cập nhật (kèm tin mới). */
  reply: (id: number, body: string, fileIds: number[]) =>
    apiPost<TicketDetail>(`${TICKET_URL}/${id}/messages`, { body, file_ids: fileIds }),

  /** Nhận / trả phiếu. `assigneeId = 0` = trả về hàng chờ. Chỉ người xử lý gọi được. */
  assign: (id: number, assigneeId: number) =>
    apiPost<TicketDetail>(`${TICKET_URL}/${id}/assign`, { assignee_id: assigneeId }),

  setStatus: (id: number, status: string) =>
    apiPost<TicketDetail>(`${TICKET_URL}/${id}/status`, { status }),

  create: (data: {
    subject: string
    department?: string
    priority?: string
    body?: string
    company_id?: number
    origin_url?: string
    file_ids?: number[]
  }) => apiPost<TicketDetail>(TICKET_URL, data),
}
