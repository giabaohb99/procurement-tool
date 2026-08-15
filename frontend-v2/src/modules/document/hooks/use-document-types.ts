import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { docTypeApi, type DocumentTypeInput } from '../api/doc-catalog-api'
import type { DocumentType } from '../types/document-type'

/**
 * Danh mục LOẠI VĂN BẢN — nạp cả danh sách một lần (dưới 100 dòng), tìm và lọc
 * ngay tại trình duyệt. Xem ghi chú trong `api/doc-catalog-api.ts`.
 */
export function useDocumentTypes() {
  const query = useQuery({
    queryKey: queryKeys.document.docTypes(),
    queryFn: () => docTypeApi.list(),
  })

  const items = useMemo(() => {
    const rows = query.data?.items ?? []
    // Sắp ở client: `sort_order` là thứ tự Hành chính muốn thấy, backend trả
    // theo id giảm dần nên loại thêm sau lại nhảy lên đầu bảng.
    return [...rows].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id)
  }, [query.data])

  return { ...query, items }
}

/** Loại đang bật — dùng cho ô chọn loại khi tạo văn bản. */
export function useActiveDocumentTypes(): DocumentType[] {
  const { items } = useDocumentTypes()
  return useMemo(() => items.filter((item) => item.is_active), [items])
}

export function useDocumentType(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.docType(id ?? 0),
    queryFn: () => docTypeApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useSaveDocumentType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocumentTypeInput }) =>
      id ? docTypeApi.update(id, values) : docTypeApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật loại văn bản' : 'Đã thêm loại văn bản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteDocumentType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => docTypeApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa loại văn bản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}
