import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentLinkRuleApi } from '../api/document-link-rule-api'
import type { DocTypeLinkRuleInput } from '../types/document-link-rule'

/** Quy tắc quan hệ theo LOẠI văn bản — danh mục nền, khai một lần (E01). */

export function useDocumentLinkRules() {
  return useQuery({
    queryKey: queryKeys.document.linkRules(),
    queryFn: () => documentLinkRuleApi.list(),
  })
}

export function useDocumentLinkRule(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.linkRule(id ?? 0),
    queryFn: () => documentLinkRuleApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useLinkRuleOptions() {
  return useQuery({
    queryKey: queryKeys.document.linkRuleOptions(),
    queryFn: () => documentLinkRuleApi.options(),
    //  Nhãn của mười loại quan hệ không đổi trong một phiên làm việc.
    staleTime: Infinity,
  })
}

export function useSaveDocumentLinkRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocTypeLinkRuleInput }) =>
      id ? documentLinkRuleApi.update(id, values) : documentLinkRuleApi.create(values),
    onSuccess: (rule) => {
      toast.success('Đã lưu quy tắc quan hệ')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRules() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRule(rule.id) })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteDocumentLinkRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentLinkRuleApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa quy tắc quan hệ')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRules() })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
