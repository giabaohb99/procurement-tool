import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentVersionApi, type VersionInput } from '../api/document-api'

/**
 * PHIÊN BẢN VĂN BẢN.
 *
 * Danh sách và nội dung tách làm hai key: danh sách phiên bản gọi liên tục (mỗi
 * lần mở tab), còn nội dung một bản dài cỡ vài trăm KB — gộp chung thì mở tab
 * phiên bản là tải về vài MB không ai đọc.
 */

export function useDocumentVersions(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.versions(documentId ?? 0),
    queryFn: () => documentVersionApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

/** Một phiên bản KÈM nội dung — trang soạn thảo và màn xem bản cũ dùng. */
export function useDocumentVersion(documentId?: number, versionId?: number | null) {
  return useQuery({
    queryKey: queryKeys.document.version(documentId ?? 0, versionId ?? 0),
    queryFn: () => documentVersionApi.getById(documentId as number, versionId as number),
    enabled: Boolean(documentId && versionId),
  })
}

/**
 * Mở phiên bản mới.
 *
 * Lỗi 409 ở đây là chuyện thường chứ không phải sự cố: người khác vừa mở bản
 * nháp trước mình. Backend trả kèm tên người đang giữ, nên hiện nguyên câu của
 * nó thay vì một câu chung chung.
 */
export function useOpenVersion(documentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (values: VersionInput) => documentVersionApi.create(documentId, values),
    onSuccess: (version) => {
      toast.success(`Đã mở phiên bản ${version.version_no}`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
    onError: (error) => {
      toast.error(extractErrorMessage(error))
    },
  })
}

/**
 * Ghi nội dung bản nháp — đường mà tự động lưu gọi theo nhịp gõ.
 *
 * KHÔNG `invalidateQueries` sau mỗi lần lưu: nạp lại nội dung trong lúc người
 * dùng đang gõ sẽ đè mất những chữ vừa nhập.
 */
export function useSaveVersionContent(documentId: number, versionId?: number | null) {
  return useMutation({
    mutationFn: (payload: {
      content_html: string
      change_summary?: string
      effective_from?: string | null
    }) => documentVersionApi.saveContent(documentId, versionId as number, payload),
  })
}
