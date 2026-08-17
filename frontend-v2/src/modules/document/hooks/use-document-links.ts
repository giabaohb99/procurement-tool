import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentLinkApi } from '../api/document-link-api'
import type { DocumentExcerptInput, DocumentLinkInput } from '../types/document-link'

/**
 * QUAN HỆ CHA–CON của một văn bản (nhóm E) và BẢN TRÍCH (C19).
 *
 * Khai thêm / gỡ một quan hệ đều nạp lại **cả ba** thứ: danh sách quan hệ, các ô
 * còn thiếu, và cây tài liệu. Chúng đọc cùng một sự thật — cập nhật lẻ một chỗ
 * thì băng "còn thiếu quan hệ bắt buộc" ở lại trên màn hình sau khi đã khai đủ.
 */

export function useDocumentLinks(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.links(documentId ?? 0),
    queryFn: () => documentLinkApi.list(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useDocumentLinkSlots(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.linkSlots(documentId ?? 0),
    queryFn: () => documentLinkApi.slots(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

/**
 * J04 — bản xem trước lúc ban hành.
 *
 * `enabled` để hộp thoại chỉ hỏi khi thật sự mở: đây là truy vấn nặng nhất của
 * trang (đọc quan hệ, phạm vi, xem trước số hiệu) mà 99% lượt mở văn bản không
 * cần tới nó.
 */
export function useIssuePreview(documentId?: number, enabled = false) {
  return useQuery({
    queryKey: queryKeys.document.issuePreview(documentId ?? 0),
    queryFn: () => documentLinkApi.issuePreview(documentId as number),
    enabled: enabled && typeof documentId === 'number' && documentId > 0,
  })
}

/**
 * J10 — nhãn "đã bị sửa đổi".
 *
 * Nạp cho MỌI văn bản, không chờ người dùng mở tab nào: đây là cảnh báo bắt
 * buộc, giấu sau một cú bấm thì cũng như không có.
 */
export function useDocumentAmendedBy(documentId?: number) {
  return useQuery({
    queryKey: queryKeys.document.amendedBy(documentId ?? 0),
    queryFn: () => documentLinkApi.amendedBy(documentId as number),
    enabled: typeof documentId === 'number' && documentId > 0,
  })
}

export function useDocumentTree(documentId?: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.document.tree(documentId ?? 0),
    queryFn: () => documentLinkApi.tree(documentId as number),
    enabled: enabled && typeof documentId === 'number' && documentId > 0,
  })
}

function useInvalidateLinks(documentId: number) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.links(documentId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkSlots(documentId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.tree(documentId) })
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.amendedBy(documentId) })
  }
}

export function useAddDocumentLink(documentId: number) {
  const invalidate = useInvalidateLinks(documentId)

  return useMutation({
    mutationFn: (values: DocumentLinkInput) => documentLinkApi.create(documentId, values),
    onSuccess: () => {
      toast.success('Đã khai quan hệ')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteDocumentLink(documentId: number) {
  const invalidate = useInvalidateLinks(documentId)

  return useMutation({
    mutationFn: (linkId: number) => documentLinkApi.remove(documentId, linkId),
    onSuccess: () => {
      toast.success('Đã gỡ quan hệ')
      invalidate()
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useCreateExcerpt(documentId: number) {
  const queryClient = useQueryClient()
  const invalidate = useInvalidateLinks(documentId)

  return useMutation({
    mutationFn: (values: DocumentExcerptInput) =>
      documentLinkApi.createExcerpt(documentId, values),
    onSuccess: (excerpt) => {
      toast.success(`Đã tạo bản trích «${excerpt.title}»`)
      invalidate()
      //  Bản trích là một VĂN BẢN MỚI — danh sách văn bản phải thấy nó ngay.
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
