import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentNumberingRuleApi } from '../api/document-numbering-rule-api'
import type {
  DocumentNumberingRuleInput,
  NumberingDirection,
} from '../types/document-numbering-rule'

export function useDocumentNumberingRules(direction: NumberingDirection) {
  return useQuery({
    queryKey: queryKeys.document.numberingRules(direction),
    queryFn: () => documentNumberingRuleApi.list(direction),
  })
}

export function useSaveDocumentNumberingRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocumentNumberingRuleInput }) =>
      id ? documentNumberingRuleApi.update(id, values) : documentNumberingRuleApi.create(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật quy tắc đánh số' : 'Đã tạo quy tắc đánh số')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.numberingRuleAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.numberPreviewAll })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteDocumentNumberingRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => documentNumberingRuleApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa quy tắc đánh số')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.numberingRuleAll })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.numberPreviewAll })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
