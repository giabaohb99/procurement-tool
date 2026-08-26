import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { mailboxApi } from '../api/mailbox-api'
import type { MailboxInput } from '../types/mailbox'

/**
 * HỘP THƯ GỬI (26/08/2026).
 *
 * Danh sách nhỏ (vài dòng) nên không phân trang, không lọc — nạp một phát.
 */
export function useMailboxes() {
  return useQuery({
    queryKey: queryKeys.system.mailboxes(),
    queryFn: () => mailboxApi.list(),
  })
}

export function useMailboxActions() {
  const queryClient = useQueryClient()
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.system.mailboxes() })
  }

  const save = useMutation({
    mutationFn: ({ id, input }: { id?: number; input: MailboxInput }) =>
      id ? mailboxApi.update(id, input) : mailboxApi.create(input),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã lưu hộp thư' : 'Đã tạo hộp thư')
      refresh()
    },
  })

  const clearPassword = useMutation({
    mutationFn: (id: number) => mailboxApi.clearPassword(id),
    onSuccess: () => {
      //  Nói rõ hậu quả: xóa mật khẩu là hộp thư NGỪNG gửi được ngay, không phải
      //  chỉ là dọn một ô trống.
      toast.success('Đã xóa mật khẩu ứng dụng — hộp thư tạm thời không gửi được')
      refresh()
    },
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => mailboxApi.deactivate(id),
    onSuccess: () => {
      toast.success('Đã ngừng dùng hộp thư')
      refresh()
    },
  })

  return { save, clearPassword, deactivate }
}
