import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentSignatureApi } from '../api/document-signature-api'
import type { DocumentSignatureInput } from '../types/document-signature'

/** Chữ ký trên văn bản (J02, J03). */

export function useDocumentSignatures(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.signatures(documentId ?? 0),
    queryFn: () => documentSignatureApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useSignKinds() {
  return useQuery({
    queryKey: queryKeys.document.signKinds(),
    queryFn: () => documentSignatureApi.kinds(),
    staleTime: Infinity,
  })
}

export function useSignDocument(documentId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (values: DocumentSignatureInput) =>
      documentSignatureApi.sign(documentId, values),
    onSuccess: (signature) => {
      toast.success(`Đã ghi nhận ${signature.sign_kind_label.toLowerCase()}`)
      void queryClient.invalidateQueries({
        queryKey: queryKeys.document.signatures(documentId),
      })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
