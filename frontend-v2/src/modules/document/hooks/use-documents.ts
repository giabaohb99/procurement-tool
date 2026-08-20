import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { documentApi, type DocumentInput, type DocumentListParams } from '../api/document-api'

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
    //  Đổi loại/phòng/pháp nhân là đổi khóa truy vấn. Không giữ kết quả cũ thì
    //  `data` về `undefined`, cả khối cảnh báo biến mất rồi hiện lại — mà nó
    //  nằm giữa lưới ô nhập nên hai ô bên dưới nhảy lên rồi tụt xuống. Giữ lại
    //  và làm mờ trong lúc nạp (xem `DocumentSuggestionList`) thì đứng yên.
    placeholderData: keepPreviousData,
  })
}

/**
 * Quan hệ TIÊN QUYẾT còn thiếu của loại đang chọn (E04b).
 *
 * Nạp sẵn ngay khi người dùng chọn loại — dù cảnh báo chỉ hiện lúc bấm Tạo:
 * hỏi tại đúng nhịp bấm thì người dùng phải chờ một vòng mạng giữa cái bấm và
 * cái hộp thoại, mà đó là nhịp họ đang sốt ruột nhất.
 *
 * Rỗng = không cảnh báo gì. Hỏng mạng cũng coi như rỗng: đây là lời nhắc, không
 * phải cổng chặn — chặn người dùng lại vì một truy vấn phụ hỏng là sai.
 */
export function useDocumentPrerequisites(docTypeId: number) {
  return useQuery({
    queryKey: queryKeys.document.prerequisites(docTypeId),
    queryFn: () => documentApi.prerequisites(docTypeId),
    enabled: docTypeId > 0,
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
  book_id?: number | null
}) {
  return useQuery({
    queryKey: queryKeys.document.numberPreview(params),
    queryFn: () => documentApi.numberPreview(params),
    enabled: params.doc_type_id > 0 && params.company_id > 0,
    //  Bốn ô nhập đều đổi khóa truy vấn này. Không giữ kết quả cũ thì mỗi lần
    //  chọn, dòng số hiệu nháy về câu "Chọn loại và pháp nhân để xem số" rồi
    //  mới có số — và câu chú thích bên dưới đổi độ dài theo, kéo cả lưới xô
    //  một nhịp.
    placeholderData: keepPreviousData,
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

export function useUpdateDocumentIssueNumber(documentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { issue_number: string; reason: string }) =>
      documentApi.updateIssueNumber(documentId, values),
    onSuccess: () => {
      toast.success('Đã cập nhật số hiệu')
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

  /**
   * Nạp lại CẢ HAI họ dữ liệu: bản ghi văn bản **và** phiên duyệt của nó.
   *
   * ⚠️ Trước 20/08/2026 hàm này chỉ nạp lại `document.all`, và đó là một lỗ
   * thật. Bấm «Gửi duyệt» xong: văn bản nạp lại nên sang «Đang duyệt», nhưng
   * phiên duyệt vẫn là kết quả cũ (`null`, hỏi từ lúc còn Nháp). Trang chi tiết
   * ẩn hai nút của luồng MỘT BƯỚC bằng điều kiện «có phiên đang chạy không» —
   * đọc phải dữ liệu cũ nên nó kết luận là không, và **«Trả lại» + «Duyệt và ban
   * hành» vẫn hiện** dù phiếu đã vào bộ máy nhiều bước.
   *
   * Bấm vào chỉ nhận lỗi 409 từ `approval_bridge.chan_duong_cu`. Băng tiến
   * trình duyệt cũng không hiện cho tới khi người dùng tự F5.
   */
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
    //  Cả cụm `approval`: phiên của chứng từ này đổi, mà hộp «Việc của tôi» của
    //  người duyệt cũng vừa có thêm/bớt một việc.
    void queryClient.invalidateQueries({ queryKey: queryKeys.approval.all })
  }

  const submit = useMutation({
    mutationFn: () => documentApi.submit(documentId),
    onSuccess: () => {
      toast.success('Đã gửi duyệt')
      refresh()
    },
  })

  const approve = useMutation({
    mutationFn: (applyMode?: number) => documentApi.approve(documentId, applyMode),
    onSuccess: (doc) => {
      //  Số hiệu thường được cấp đúng lúc này (`number_when = 2`) — nói ra luôn
      //  để người duyệt biết văn bản vừa mang số gì.
      toast.success(doc.display_code ? `Đã ban hành ${doc.display_code}` : 'Đã duyệt và ban hành')
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

  /**
   * Xác nhận ĐÃ RÀ SOÁT xong — tắt cờ «cần rà lại».
   *
   * Nằm chung `useDocumentWorkflow` vì cùng họ: đều đổi trạng thái bản ghi và
   * đều phải nạp lại cả cụm dữ liệu văn bản sau khi chạy.
   */
  const confirmReviewed = useMutation({
    mutationFn: (ketLuan: string) => documentApi.confirmReviewed(documentId, ketLuan),
    onSuccess: () => {
      toast.success('Đã ghi nhận rà soát xong')
      refresh()
    },
  })

  return { submit, approve, reject, revoke, confirmReviewed }
}
