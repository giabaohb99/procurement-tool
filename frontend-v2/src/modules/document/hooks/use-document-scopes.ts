import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentScopeApi } from '../api/document-scope-api'
import type { DocumentScopeInput } from '../types/document-scope'

/** Phạm vi áp dụng của văn bản (F01–F05). */

export function useDocumentScopes(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.scopes(documentId ?? 0),
    queryFn: () => documentScopeApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useScopeOptions() {
  return useQuery({
    queryKey: queryKeys.document.scopeOptions(),
    queryFn: () => documentScopeApi.options(),
    //  Nhãn ba chiều và hai chế độ không đổi trong một phiên làm việc.
    staleTime: Infinity,
  })
}

/** F05 — văn bản đang áp dụng cho chính tôi. */
export function useDocumentsAppliedToMe() {
  return useQuery({
    queryKey: queryKeys.document.appliesToMe(),
    queryFn: () => documentScopeApi.appliesToMe(),
  })
}

function useInvalidateScopes(documentId: number) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.scopes(documentId) })
    //  Đổi phạm vi là đổi luôn danh sách "áp dụng cho tôi" của người khác —
    //  ít nhất của chính người vừa sửa.
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.appliesToMe() })
  }
}

export function useAddDocumentScope(documentId: number) {
  const invalidate = useInvalidateScopes(documentId)

  return useMutation({
    mutationFn: (values: DocumentScopeInput) => documentScopeApi.create(documentId, values),
    onSuccess: () => {
      toast.success('Đã thêm phạm vi áp dụng')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteDocumentScope(documentId: number) {
  const invalidate = useInvalidateScopes(documentId)

  return useMutation({
    mutationFn: (scopeId: number) => documentScopeApi.remove(documentId, scopeId),
    onSuccess: () => {
      toast.success('Đã gỡ dòng phạm vi')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
