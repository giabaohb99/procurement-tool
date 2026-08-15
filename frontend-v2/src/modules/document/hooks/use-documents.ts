import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import {
  documentApi,
  type DocumentInput,
  type DocumentListParams,
} from '../api/document-api'

/**
 * VĂN BẢN — đọc/ghi qua API thật.
 *
 * Danh sách **phân trang và tìm kiếm ở backend**, không nạp hết về rồi lọc tại
 * trình duyệt như ba danh mục nền: bảng này sẽ lên vài chục nghìn dòng, mà quan
 * trọng hơn là lọc ở client thì máy người dùng phải nhận về cả những văn bản họ
 * không được xem.
 */

export function useDocuments(params: DocumentListParams = {}) {
  return useQuery({
    queryKey: queryKeys.document.records(params),
    queryFn: () => documentApi.list(params),
    //  Giữ trang cũ trong lúc nạp trang mới: bảng không nháy trắng mỗi lần đổi
    //  bộ lọc hay sang trang.
    placeholderData: keepPreviousData,
  })
}

export function useDocument(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.record(id ?? 0),
    queryFn: () => documentApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

/**
 * Văn bản CÙNG LOẠI CÙNG PHÒNG đang còn hiệu lực (B05).
 *
 * Hiện ngay trong form soạn để người dùng thấy "đã có rồi" trước khi ngồi gõ
 * bản thứ hai cho cùng một việc — đây là thứ còn lại chống đẻ trùng quy trình
 * sau khi bước xin phép bị cắt khỏi bản 1.
 */
export function useDocumentSuggestions(params: {
  doc_type_id: number
  department_id?: number | null
  company_id?: number | null
  exclude_id?: number
}) {
  return useQuery({
    queryKey: queryKeys.document.suggestions(params),
    queryFn: () => documentApi.suggestions(params),
    enabled: params.doc_type_id > 0,
  })
}

/**
 * Số hiệu SẼ cấp — chỉ để xem trước.
 *
 * ⚠️ Không chiếm số và có thể lệch nếu có người được cấp số ngay sau đó. Số
 * thật do backend cấp trong cùng giao dịch ghi bản ghi.
 */
export function useNumberPreview(params: {
  doc_type_id: number
  company_id: number
  department_id?: number | null
}) {
  return useQuery({
    queryKey: queryKeys.document.numberPreview(params),
    queryFn: () => documentApi.numberPreview(params),
    enabled: params.doc_type_id > 0 && params.company_id > 0,
  })
}

export function useSaveDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      values,
    }: {
      id?: number
      values: DocumentInput & { content_html?: string }
    }) => (id ? documentApi.update(id, values) : documentApi.create(values)),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật văn bản' : 'Đã tạo văn bản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa văn bản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    },
  })
}

/**
 * Ba nút của luồng duyệt MỘT BƯỚC tạm thời.
 *
 * P3 sẽ thay bằng bộ máy duyệt dùng chung (nhiều bước, rẽ nhánh, người thay
 * thế). Gói gọn trong một hook để lúc thay chỉ phải sửa một chỗ.
 */
export function useDocumentWorkflow(documentId: number) {
  const queryClient = useQueryClient()

  const refresh = () =>
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })

  const submit = useMutation({
    mutationFn: () => documentApi.submit(documentId),
    onSuccess: () => {
      toast.success('Đã gửi duyệt')
      refresh()
    },
  })

  const approve = useMutation({
    mutationFn: () => documentApi.approve(documentId),
    onSuccess: (doc) => {
      //  Số hiệu thường được cấp đúng lúc này (`number_when = 2`) — nói ra luôn
      //  để người duyệt biết văn bản vừa mang số gì.
      toast.success(
        doc.display_code ? `Đã ban hành ${doc.display_code}` : 'Đã duyệt và ban hành',
      )
      refresh()
    },
  })

  const reject = useMutation({
    mutationFn: (reason: string) => documentApi.reject(documentId, reason),
    onSuccess: () => {
      toast.success('Đã trả lại bản nháp')
      refresh()
    },
  })

  const revoke = useMutation({
    mutationFn: (reason: string) => documentApi.revoke(documentId, reason),
    onSuccess: () => {
      toast.success('Đã bãi bỏ văn bản')
      refresh()
    },
  })

  return { submit, approve, reject, revoke }
}
