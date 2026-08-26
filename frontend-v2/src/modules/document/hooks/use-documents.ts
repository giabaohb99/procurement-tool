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

/**
 * Nhịp hỏi lại khi văn bản ĐANG CHẠY trong bộ máy duyệt.
 *
 * Người duyệt có thể bị đổi bất cứ lúc nào ở màn Luồng duyệt (CR-114). Không
 * hỏi lại thì người vừa mất việc vẫn ngồi trong trang chi tiết với nút *Duyệt*
 * sáng trưng cho tới khi họ tự tải lại trang — bấm vào chỉ nhận lỗi.
 *
 * 20 giây, cùng nhịp với chuông thông báo.
 */
const PENDING_POLL_MS = 20_000

/**
 * Nhịp hỏi lại khi văn bản chỉ đang MỞ ĐỌC.
 *
 * Thưa hơn hẳn nhịp đang duyệt vì việc cần bắt ở đây hiếm hơn nhiều: người khác
 * **bãi bỏ** văn bản trong lúc mình đang đọc. Bãi bỏ nay thu hồi luôn quyền xem
 * (`revoke_access.py` ở backend) nên nhịp này chính là thứ khiến người đọc bị đá
 * ra thay vì ngồi lại với một trang đã chết — trước đây `false`, tức là **không
 * bao giờ** biết.
 */
const READ_POLL_MS = 60_000

export function useDocument(id?: number, options: { dangDuyet?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.document.record(id ?? 0),
    queryFn: () => documentApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
    refetchInterval: options.dangDuyet ? PENDING_POLL_MS : READ_POLL_MS,
    //  Quay lại tab là hỏi ngay, không đợi hết nhịp: người dùng chuyển sang màn
    //  khác rồi quay về là lúc hay gặp nhất.
    refetchOnWindowFocus: true,
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
 * Gợi ý cho ô «Nơi lưu trữ cứng» — các ngăn tủ đã từng được gõ.
 *
 * Danh sách này là thứ duy nhất giữ cho một ô chữ tự do khỏi thành mỗi người
 * một kiểu ("Tủ A2" / "tu a2" / "TỦ A2"), nên nó phải hiện ngay lúc gõ chứ
 * không phải một màn danh mục ai đó nhớ ra thì vào sửa.
 */
export function useStorageLocations() {
  return useQuery({
    queryKey: queryKeys.document.storageLocations(),
    queryFn: () => documentApi.storageLocations(),
    //  Danh sách ngăn tủ gần như đứng yên trong một phiên làm việc.
    staleTime: 5 * 60_000,
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

/** Sao chép một văn bản thành bản nháp độc lập; không phải clone xuống pháp nhân con. */
export function useCopyDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: number) => documentApi.copy(documentId),
    onSuccess: () => {
      toast.success('Đã tạo bản sao ở trạng thái nháp')
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
 * Bỏ bản nháp do chính mình vừa mở ở màn *Tạo văn bản* (nút «Hủy»).
 *
 * KHÔNG báo toast xanh: đây là thao tác dọn dẹp ngầm khi người dùng rời form,
 * họ không «làm» gì để mà được xác nhận. Bên gọi tự bắt lỗi.
 */
export function useDiscardDraft() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentApi.discardDraft(id),
    onSuccess: () => {
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
    //  Cả cụm `approval`: phiên của chứng từ này đổi, mà hộp «Chờ tôi duyệt»
    //  của người duyệt cũng vừa có thêm/bớt một việc.
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
    mutationFn: (input?: { applyMode?: number; mailboxId?: number }) =>
      documentApi.approve(documentId, input?.applyMode, input?.mailboxId),
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
