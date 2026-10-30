import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'

import { purchaseRequestSupportApi } from '@/modules/procurement/api/purchase-request-support-api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentApi } from '../api/document-api'

/**
 * Tệp của MỌI phiên bản của một văn bản — nguồn dữ liệu của tab "Tệp"
 * (phase 09). Khác `useQuery` của `document-attachment-list.tsx` (chỉ một
 * phiên bản): đây gộp cả văn bản trong một lần gọi.
 */
export function useDocumentFiles(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.files(documentId ?? 0),
    queryFn: () => documentApi.listAllAttachments(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

/**
 * Tải tệp lên PHIÊN BẢN ĐANG DÙNG — nút "Tải tệp lên" của tab Tệp lúc 0 tệp
 * (`document-files-tab.tsx`). Đi cùng đường với `document-attachment-list.tsx`
 * (`entity = 'document_version'`), chỉ khác nơi gọi và nơi vô hiệu cache.
 */
export function useUploadDocumentFile(documentId: number, currentVersionId?: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (files: File[]) =>
      purchaseRequestSupportApi.uploadAttachments(
        'document_version',
        currentVersionId as number,
        files,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.files(documentId) })
      //  `attachment_count` treo trên chính bản ghi văn bản (dùng để chọn tab
      //  mặc định lần sau) — đổi số tệp thì bản ghi đó cũng phải đọc lại.
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.record(documentId) })
    },
  })
}

/**
 * Gỡ MỘT tệp khỏi phiên bản (xóa liên kết `tab_file_link`) — nút "Xóa tệp" của tab Tệp. Backend cho phép khi người
 * dùng có quyền SỬA văn bản (với bản lưu trữ hợp đồng lao động: `labor_contract.write`) và phiên bản chưa bị khóa.
 */
export function useDeleteDocumentFile(documentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (linkId: number) => purchaseRequestSupportApi.deleteAttachment(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.files(documentId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.record(documentId) })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
