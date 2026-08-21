import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { ticketApi } from '../api/ticket-api'
import type { TicketDetail } from '../types/ticket'

/** Danh sách phiếu. `keepPreviousData` để đổi trang / bộ lọc không nháy khung rỗng. */
export function useTickets(params: ListParams = {}) {
  const query: ListParams = { page: 1, page_size: appConfig.defaultPageSize, ...params }
  return useQuery({
    queryKey: queryKeys.support.tickets(query),
    queryFn: () => ticketApi.list(query),
    placeholderData: keepPreviousData,
  })
}

export function useTicket(id: number) {
  return useQuery({
    queryKey: queryKeys.support.ticket(id),
    queryFn: () => ticketApi.getById(id),
    enabled: id > 0,
  })
}

/** Tệp gửi kèm lúc tạo phiếu — chỉ đọc, không đổi trong vòng đời phiếu. */
export function useTicketAttachments(id: number) {
  return useQuery({
    queryKey: queryKeys.support.ticketAttachments(id),
    queryFn: () => ticketApi.listAttachments(id),
    enabled: id > 0,
  })
}

/**
 * Ba việc ghi đều trả về CHI TIẾT phiếu mới → ghi thẳng vào cache chi tiết
 * (`setQueryData`) để màn cập nhật tức thì, đồng thời vô hiệu cả nhánh `support`
 * để DANH SÁCH (trạng thái, người xử lý) cũng làm mới khi quay ra.
 */
function useTicketWriter(id: number) {
  const queryClient = useQueryClient()
  return (updated: TicketDetail) => {
    queryClient.setQueryData(queryKeys.support.ticket(id), updated)
    void queryClient.invalidateQueries({ queryKey: queryKeys.support.all })
  }
}

/**
 * Gửi trả lời. Nhận thẳng `fileIds` vì ô soạn thảo đã tải tệp lên ngay khi
 * chọn / dán / kéo-thả (để hiện thẻ xem trước tức thì như bản v1), không đợi
 * tới lúc bấm Gửi mới tải.
 */
export function useReplyTicket(id: number) {
  const apply = useTicketWriter(id)
  return useMutation({
    mutationFn: ({ body, fileIds }: { body: string; fileIds: number[] }) =>
      ticketApi.reply(id, body, fileIds),
    onSuccess: apply,
  })
}

export function useAssignTicket(id: number) {
  const apply = useTicketWriter(id)
  return useMutation({
    mutationFn: (assigneeId: number) => ticketApi.assign(id, assigneeId),
    onSuccess: (updated, assigneeId) => {
      apply(updated)
      toast.success(assigneeId ? 'Bạn đã nhận phiếu này' : 'Đã trả phiếu về hàng chờ')
    },
  })
}

/**
 * Nút "Nhận" trên DANH SÁCH: mỗi dòng một phiếu khác nhau nên id đi theo biến
 * `mutate`, không cố định như hook chi tiết ở trên. Chỉ cần làm mới danh sách.
 */
export function useTakeTicket() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ ticketId, assigneeId }: { ticketId: number; assigneeId: number }) =>
      ticketApi.assign(ticketId, assigneeId),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.support.ticket(updated.id), updated)
      void queryClient.invalidateQueries({ queryKey: queryKeys.support.all })
      toast.success(`Bạn đã nhận phiếu ${updated.code}`)
    },
  })
}

export function useSetTicketStatus(id: number) {
  const apply = useTicketWriter(id)
  return useMutation({
    mutationFn: (status: string) => ticketApi.setStatus(id, status),
    onSuccess: (updated) => {
      apply(updated)
      toast.success('Đã cập nhật trạng thái')
    },
  })
}

export function useCreateTicket() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      subject: string
      department?: string
      priority?: string
      body?: string
      company_id?: number
      origin_url?: string
      file_ids?: number[]
    }) => ticketApi.create(data),
    onSuccess: (newTicket) => {
      queryClient.setQueryData(queryKeys.support.ticket(newTicket.id), newTicket)
      void queryClient.invalidateQueries({ queryKey: queryKeys.support.all })
      toast.success(`Đã tạo phiếu hỗ trợ #${newTicket.code}`)
    },
  })
}
