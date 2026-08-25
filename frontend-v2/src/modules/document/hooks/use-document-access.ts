import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { documentAccessApi } from '../api/document-api'
import type { DocumentAccessInput } from '../types/document-access'

/**
 * QUYỀN TRÊN TỪNG VĂN BẢN — ai được thấy, đọc, sửa, xóa văn bản này.
 *
 * Danh sách trả về CẢ dòng đã thu hồi (thu hồi là đánh dấu, không xóa dòng) —
 * bảng trên trang chi tiết hiện chúng ở dạng mờ, vì câu người ta hỏi khi có
 * chuyện là "hồi tháng 7 ai đọc được văn bản này".
 */

export function useDocumentAccess(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.access(documentId ?? 0),
    queryFn: () => documentAccessApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

/**
 * Tôi được làm gì trên ĐÚNG văn bản này.
 *
 * ⚠️ Chỉ để ẩn nút cho đỡ vướng mắt. Chốt chặn thật nằm ở backend
 * (`ensure_can` trong từng endpoint) — đừng bao giờ coi kết quả này là bảo mật.
 */
export function useDocumentPermissions(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.permissions(documentId ?? 0),
    queryFn: () => documentAccessApi.permissions(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useGrantAccess(documentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (values: DocumentAccessInput) =>
      documentAccessApi.grant(documentId, values),
    onSuccess: (row) => {
      toast.success(
        row.effect === 2
          ? `Đã cấm ${row.subject_name || 'đối tượng'} truy cập văn bản này`
          : `Đã chia quyền cho ${row.subject_name || 'đối tượng'}`,
      )
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useRevokeAccess(documentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ accessId, reason }: { accessId: number; reason: string }) =>
      documentAccessApi.revoke(documentId, accessId, reason),
    onSuccess: () => {
      toast.success('Đã hủy quyền truy cập')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}
