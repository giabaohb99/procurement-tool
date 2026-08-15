import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { toast } from 'sonner'

import type { ListParams } from '@/shared/types/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentTemplateApi } from '../api/document-template-api'
import type { DocumentTemplateInput } from '../types/document-template'

export function useDocumentTemplates(params: ListParams = {}, enabled = true) {
  const query = useQuery({
    queryKey: queryKeys.document.templates(params),
    queryFn: () => documentTemplateApi.list(params),
    enabled,
  })

  const items = useMemo(() => query.data?.items ?? [], [query.data])
  return { ...query, items }
}

/** Mẫu đang dùng của đúng loại văn bản, dùng cho ô chọn ở trang tạo. */
export function useActiveDocumentTemplates(docTypeId: number, enabled = true) {
  return useDocumentTemplates({ doc_type_id: docTypeId, is_active: true }, enabled && docTypeId > 0)
}

export function useDocumentTemplate(id?: number | null) {
  return useQuery({
    queryKey: queryKeys.document.template(id ?? 0),
    queryFn: () => documentTemplateApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useSaveDocumentTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocumentTemplateInput }) =>
      id ? documentTemplateApi.update(id, values) : documentTemplateApi.create(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật văn bản mẫu' : 'Đã tạo văn bản mẫu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteDocumentTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentTemplateApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa văn bản mẫu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}
