import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentBookApi } from '../api/document-book-api'
import type { DocumentBookInput } from '../types/document-book'

/**
 * Danh sách sổ. Nạp cả danh mục một lần, lọc và tìm tại trình duyệt.
 *
 * `year` đi vào query vì backend tính `next_no` và `issued_count` theo năm —
 * đổi năm trên màn hình là phải đọc lại, không lọc ở client được.
 */
export function useDocumentBooks(year?: number) {
  const query = useQuery({
    queryKey: queryKeys.document.books(year),
    queryFn: () => documentBookApi.list(year ? { year } : {}),
  })

  const items = useMemo(() => query.data?.items ?? [], [query.data])
  return { ...query, items }
}

export function useDocumentBook(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.book(id ?? 0),
    queryFn: () => documentBookApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

/** Bộ đếm của một sổ theo năm — tách khỏi bản ghi sổ vì đổi năm là đọc lại. */
export function useBookCounter(id?: number, year?: number) {
  return useQuery({
    queryKey: queryKeys.document.bookCounter(id ?? 0, year ?? 0),
    queryFn: () => documentBookApi.counter(id as number, year),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useSaveDocumentBook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DocumentBookInput }) =>
      id ? documentBookApi.update(id, values) : documentBookApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật sổ' : 'Đã tạo sổ văn bản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteDocumentBook() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentBookApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa sổ')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
    // Sổ đã cấp số thì backend từ chối xóa. Câu báo của backend nói rõ phải làm
    // gì tiếp (chuyển sang Ngừng dùng) nên hiện nguyên văn, đừng nuốt mất.
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
