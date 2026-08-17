import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentCloneApi } from '../api/document-clone-api'
import type { DocumentCloneInput } from '../types/document-clone'

/** Clone xuống pháp nhân con (F06–F10). */

export function useDocumentClones(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.clones(documentId ?? 0),
    queryFn: () => documentCloneApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useCreateClones(documentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (values: DocumentCloneInput) => documentCloneApi.create(documentId, values),
    onSuccess: (clones) => {
      toast.success(`Đã tạo ${clones.length} bản nháp cho pháp nhân con`)
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.clones(documentId) })
      //  Bản clone là VĂN BẢN MỚI — danh sách văn bản phải thấy chúng ngay.
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
