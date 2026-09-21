/**
 * ĐIỀU KIỆN ÁP DỤNG của hồ sơ — *«giấy này phải kèm theo chứng từ nào»*.
 *
 * ⚠️ Bộ mã phải khớp `backend/app/modules/dossier/applicability.py`. Gõ tay ở
 * đây vì `gen_status_ts.py` chỉ sinh cho bộ mã trạng thái CHUỖI — cùng cảnh với
 * `hr/types/leave.ts` và `hr/types/employee-codes.ts`. Có test chốt số mục,
 * nhưng thêm mã ở backend vẫn phải nhớ sửa tay bên này.
 *
 * ⚠️ **HAI CA RỖNG, HAI NGHĨA NGƯỢC NHAU** — chỗ dễ hiểu nhầm nhất của cả tính
 * năng, và cả hai đều im lặng:
 *   * `apply_doc_kinds` rỗng → hồ sơ **không bao giờ** hiện ra ở đâu. Mặc định.
 *   * `apply_doc_kinds` có, `apply_conditions` rỗng → áp cho **MỌI** phiếu loại
 *     đó. Giao diện phải nói thành câu, đừng để người dùng suy ra từ bảng trống.
 */

/** Loại chứng từ mà hồ sơ gắn vào được. */
export const DOC_KINDS = {
  PURCHASE_REQUEST: 'purchase_request',
  PURCHASE_ORDER: 'purchase_order',
  SURVEY_REQUEST: 'survey_request',
  SURVEY: 'survey',
} as const

export type DocKind = (typeof DOC_KINDS)[keyof typeof DOC_KINDS]

export const DOC_KIND_LABEL: Record<DocKind, string> = {
  [DOC_KINDS.PURCHASE_REQUEST]: 'Yêu cầu mua hàng',
  [DOC_KINDS.PURCHASE_ORDER]: 'Đơn mua hàng',
  [DOC_KINDS.SURVEY_REQUEST]: 'Yêu cầu báo giá',
  [DOC_KINDS.SURVEY]: 'Phiếu khảo sát',
}

/** Thứ tự bày ô chọn — theo đúng dòng chảy nghiệp vụ, không theo bảng chữ cái. */
export const DOC_KIND_ORDER: DocKind[] = [
  DOC_KINDS.SURVEY,
  DOC_KINDS.SURVEY_REQUEST,
  DOC_KINDS.PURCHASE_REQUEST,
  DOC_KINDS.PURCHASE_ORDER,
]

/**
 * Cảnh báo riêng của từng màn — rỗng là không có gì phải dặn.
 *
 * ⚠️ Câu của YCBG không phải lời khuyên cho vui: dòng YCBG **không mang mã sản
 * phẩm** (`tab_survey_request_line` chỉ có `item_group`), mã chỉ có ở phương án
 * đã chốt. Không nói ra thì người khai gắn điều kiện theo sản phẩm, thấy nó
 * không bao giờ khớp, và đi tìm lỗi ở một chỗ không có lỗi nào.
 */
export const DOC_KIND_WARNING: Partial<Record<DocKind, string>> = {
  [DOC_KINDS.SURVEY_REQUEST]:
    'Dòng YCBG chưa có mã sản phẩm — điều kiện theo Sản phẩm chỉ khớp sau khi ' +
    'chốt phương án. Muốn khớp ngay từ lúc lập phiếu thì dùng Phân loại VTBB/NL.',
}

/** Chiều khai điều kiện — đều là cột có thật trên dòng hàng. */
export const APPLY_FIELDS = {
  PRODUCT_CODE: 'product_code',
  ITEM_GROUP: 'item_group',
} as const

export type ApplyField = (typeof APPLY_FIELDS)[keyof typeof APPLY_FIELDS]

export const APPLY_FIELD_LABEL: Record<ApplyField, string> = {
  [APPLY_FIELDS.PRODUCT_CODE]: 'Sản phẩm',
  [APPLY_FIELDS.ITEM_GROUP]: 'Phân loại VTBB/NL',
}

/**
 * Phép so sánh. Cố ý KHÔNG có `gt`/`lt` như bộ máy duyệt: so mã sản phẩm
 * «lớn hơn» thì ra một câu không ai đọc được nghĩa.
 */
export const APPLY_OPS = {
  EQ: 'eq',
  NE: 'ne',
  IN: 'in',
  NOT_IN: 'not_in',
  CONTAINS: 'contains',
} as const

export type ApplyOp = (typeof APPLY_OPS)[keyof typeof APPLY_OPS]

export const APPLY_OP_LABEL: Record<ApplyOp, string> = {
  [APPLY_OPS.EQ]: 'là',
  [APPLY_OPS.NE]: 'khác',
  [APPLY_OPS.IN]: 'thuộc',
  [APPLY_OPS.NOT_IN]: 'không thuộc',
  [APPLY_OPS.CONTAINS]: 'chứa',
}

/** Phép nhận NHIỀU giá trị — ô nhập của chúng là danh sách ngăn bằng dấu phẩy. */
export const MULTI_VALUE_OPS: ApplyOp[] = [APPLY_OPS.IN, APPLY_OPS.NOT_IN]

export function isMultiValueOp(op: ApplyOp): boolean {
  return MULTI_VALUE_OPS.includes(op)
}

/** Trần khai ở backend (`applicability.py`) — nhắc lại để giao diện chặn sớm. */
export const MAX_APPLY_CONDITIONS = 10
export const MAX_APPLY_VALUES = 50
export const MAX_APPLY_VALUE_LEN = 100

/** MỘT dòng điều kiện. `value` là chuỗi với phép một giá trị, mảng với `in`/`not_in`. */
export interface ApplyCondition {
  field: ApplyField
  op: ApplyOp
  value: string | string[]
}

/**
 * TIẾN ĐỘ của một tờ hồ sơ TRÊN MỘT chứng từ — bốn mức, khớp
 * `backend/app/modules/dossier/constants.py` (`DP_*`).
 *
 * ⚠️ **Đừng lẫn với `DOSSIER_STATUS`.** Hai thang nói hai chuyện:
 *   · `DOSSIER_STATUS` (nháp/đang lưu/lưu trữ) = tờ giấy ĐÃ CÓ trong kho công
 *     ty chưa — một giá trị cho cả công ty.
 *   · `DOSSIER_PROGRESS` = việc làm tờ giấy đó CHO PHIẾU ĐANG MỞ tới đâu rồi —
 *     mỗi phiếu một giá trị. Thẻ «Hồ sơ cần hoàn thành» đo tiến độ bằng thang
 *     NÀY; đo bằng thang kia thì mọi phiếu ra cùng một con số.
 */
export const DOSSIER_PROGRESS = {
  IDLE: 0,
  DOING: 1,
  REVIEW: 2,
  DONE: 3,
} as const

export type DossierProgressStatus = (typeof DOSSIER_PROGRESS)[keyof typeof DOSSIER_PROGRESS]

export const DOSSIER_PROGRESS_LABEL: Record<DossierProgressStatus, string> = {
  [DOSSIER_PROGRESS.IDLE]: 'Chưa bắt đầu',
  [DOSSIER_PROGRESS.DONE]: 'Hoàn thành',
  [DOSSIER_PROGRESS.DOING]: 'Đang làm',
  [DOSSIER_PROGRESS.REVIEW]: 'Chờ duyệt',
}

/** Thứ tự bày ô chọn — theo dòng chảy công việc, không theo giá trị mã. */
export const DOSSIER_PROGRESS_ORDER: DossierProgressStatus[] = [
  DOSSIER_PROGRESS.IDLE,
  DOSSIER_PROGRESS.DOING,
  DOSSIER_PROGRESS.REVIEW,
  DOSSIER_PROGRESS.DONE,
]

/** Hồ sơ khớp một chứng từ — bộ trường vừa đủ cho thẻ «Hồ sơ cần kèm». */
export interface ApplicableDossier {
  id: number
  code: string
  name: string
  /** KHÓA loại — gom nhóm bằng nó, đừng gom bằng `dossier_type_name`. */
  dossier_type_id: number
  dossier_type_name: string
  status: number
  status_label: string
  /** Ghi chú ngắn — cột MÔ TẢ trên dòng hồ sơ của thẻ «Hồ sơ cần hoàn thành». */
  note: string
  expiry_date: string | null
  expiry_state: number
  expiry_state_label: string
  expiry_days: number | null
  /** Câu lý do do BACKEND dựng — đừng ghép lại ở TypeScript, xem `reason_of`. */
  reason: string
  /**
   * Số thứ tự các dòng hàng mà tờ hồ sơ này khớp.
   *
   * ⚠️ **RỖNG = hồ sơ CHUNG** (áp cho cả phiếu), KHÔNG phải «không khớp dòng
   * nào» — hồ sơ không khớp thì backend đã loại khỏi danh sách. Lẫn hai nghĩa
   * là bộ hồ sơ chung biến mất khỏi chế độ xem «Theo dòng hàng», đúng nhóm
   * đông nhất và quan trọng nhất.
   */
  matched_lines: number[]

  //  ----- TIẾN ĐỘ RIÊNG CỦA CHỨNG TỪ ĐANG MỞ (`tab_dossier_progress`) -----
  //  ⚠️ Cặp (chứng từ × hồ sơ) chưa ai động tới thì KHÔNG có dòng dưới DB;
  //  backend trả bộ mặc định «chưa bắt đầu · bắt buộc · chưa ai nhận». Nên mấy
  //  ô này LUÔN có giá trị, không bao giờ `undefined`.
  progress_status: DossierProgressStatus
  progress_status_label: string
  /** `progress_status === DONE`. Backend tính sẵn để hai bên khỏi lệch luật. */
  progress_done: boolean
  /** Bắt buộc với PHIẾU NÀY — cùng một tờ có thể bắt buộc ở phiếu này mà không ở phiếu khác. */
  required: boolean
  assignee_id: number
  assignee_name: string
  /** Hẹn xong hôm nào CHO PHIẾU NÀY. Khác hẳn `expiry_date` của tờ giấy. */
  planned_date: string | null
  /** Ghi chú riêng của phiếu — KHÔNG phải `note` (mô tả dùng chung của tờ giấy). */
  progress_note: string
  file_note: string
  /** Đã có dòng thật dưới DB chưa. Chỉ để gỡ lỗi, giao diện không vẽ khác theo nó. */
  progress_saved: boolean

  /** `id` các tờ phải xong TRƯỚC tờ này, TRÊN PHIẾU NÀY. */
  depends: number[]
  /**
   * Những tờ tiên quyết CHƯA xong — kèm tên để dựng câu «chờ: …» khỏi phải tra
   * ngược. Rỗng = tờ này mở khóa.
   *
   * ⚠️ **Backend tính, đừng tự suy từ `depends` ở TypeScript.** Luật có lọc id
   * CHẾT (tờ tiên quyết không còn áp dụng cho phiếu sau khi điều kiện đổi); hai
   * bản luật sẽ lệch nhau đúng ở ca đó, và cái lệch là một tờ khóa vĩnh viễn.
   */
  waiting: { id: number; name: string }[]
  /** `waiting.length > 0`. Tờ đang khóa thì KHÔNG tick xong được. */
  locked: boolean
}

/** MỘT dòng hàng của chứng từ — khung của chế độ xem «Theo dòng hàng». */
export interface ApplicableDocLine {
  no: number
  /** Tên dễ đọc do backend dựng (tên SP, hoặc phân loại + thông số với YCBG). */
  label: string
  product_code: string
  item_group: string
}

export interface ApplicableDossiersResult {
  items: ApplicableDossier[]
  doc_kind: DocKind
  doc_id: number
  doc_kind_label: string
  /** Dòng hàng của chính chứng từ này — trả kèm để khỏi gọi thêm một lượt. */
  lines: ApplicableDocLine[]
}

/**
 * Đọc `value` của một dòng điều kiện ra CHUỖI cho ô nhập, và ngược lại.
 *
 * ⚠️ Một chỗ duy nhất biết luật «ngăn bằng dấu phẩy». Rải ra hai nơi thì nơi
 * ĐỌC và nơi GHI sẽ lệch nhau ở đúng ca có khoảng trắng thừa, và người dùng gõ
 * `SP-001, SP-002` rồi lưu ra một mã tên là `" SP-002"`.
 */
export function conditionValueToText(value: string | string[]): string {
  return Array.isArray(value) ? value.join(', ') : (value ?? '')
}

export function textToConditionValue(text: string, op: ApplyOp): string | string[] {
  if (!isMultiValueOp(op)) return text.trim()
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}
