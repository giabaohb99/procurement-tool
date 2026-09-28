import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  deleteLeaveAttachment,
  fetchLeaveAttachments,
  uploadLeaveAttachments,
  type LeaveAttachment,
} from '../api/leave-attachment-api'

/** Tệp đính kèm của MỘT tờ đơn. Đơn chưa lưu (`id = 0`) thì không gọi gì. */
export function useLeaveAttachments(requestId: number) {
  return useQuery({
    queryKey: queryKeys.hr.leaveAttachments(requestId),
    queryFn: () => fetchLeaveAttachments(requestId),
    enabled: requestId > 0,
  })
}

export function useUploadLeaveAttachments(requestId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (files: File[]) => uploadLeaveAttachments(requestId, files),
    onSuccess: (uploaded: LeaveAttachment[]) => {
      toast.success(
        uploaded.length > 1 ? `Đã tải lên ${uploaded.length} tệp` : 'Đã tải lên tệp',
      )
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.leaveAttachments(requestId),
      })
    },
    //  KHÔNG khai `onError`: `httpClient` đã tự bày toast cho mọi lệnh khác GET,
    //  thêm nữa là hai câu báo lỗi cho một lần bấm.
  })
}

export function useDeleteLeaveAttachment(requestId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (linkId: number) => deleteLeaveAttachment(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.leaveAttachments(requestId),
      })
    },
  })
}
