/**
 * HỒ SƠ — dữ liệu THẬT, bảng `tab_dossier`, API `/api/dossiers`.
 *
 * Trường phải khớp `DossierResponse` ở `backend/app/modules/dossier/schema.py`.
 *
 * Một dòng = một bộ giấy tờ công ty đang giữ. Phần khung (mã · tên · loại · nơi
 * giữ · hạn hiệu lực) là CỘT THẬT; phần riêng của từng loại nằm trong
 * `extra_fields`, khai ở `DossierType.field_schema` — xem `dossier-field.ts`.
 */
import type { ApplyCondition, DocKind } from './dossier-applicability'
import type { DossierFieldDef, DossierFieldType } from './dossier-field'

/**
 * Tình trạng hồ sơ — mã **SỐ** theo luật R2 (QĐ-11): kho lưu số, tiếng Việt chỉ
 * sống ở tầng hiển thị. Gõ tay ở đây vì `gen_status_ts.py` chỉ sinh cho bộ mã
 * CHUỖI; đổi ở `backend/.../dossier/constants.py` thì phải nhớ sửa tay bên này
 * (có test chốt số mục).
 *
 * ⚠️ **Cố ý KHÔNG có «Hết hạn» / «Sắp hết hạn».** Hai thứ đó suy ra từ
 * `expiry_date`, xem `DOSSIER_EXPIRY` bên dưới. Lưu chúng thành trạng thái là
 * tự dựng một sự thật thứ hai: tới nửa đêm nó sai, và phải có tác vụ chạy nền
 * đi lật từng dòng cho nó đúng lại.
 */
export const DOSSIER_STATUS = {
  /** Mới lập, chưa nộp vào kho hồ sơ. */
  DRAFT: 1,
  /** Đã nộp, đang theo dõi. */
  ACTIVE: 2,
  /** Hết vòng đời, chuyển kho lưu trữ. */
  ARCHIVED: 3,
} as const

export type DossierStatus = (typeof DOSSIER_STATUS)[keyof typeof DOSSIER_STATUS]

export const DOSSIER_STATUS_LABEL: Record<DossierStatus, string> = {
  [DOSSIER_STATUS.DRAFT]: 'Nháp',
  [DOSSIER_STATUS.ACTIVE]: 'Đang lưu',
  [DOSSIER_STATUS.ARCHIVED]: 'Đã lưu trữ',
}

/**
 * Tình trạng HIỆU LỰC — **suy ra, không lưu cột nào**. Backend tính mỗi lần đọc
 * (`dossier/expiry.py`) và gửi kèm trong phong bì.
 *
 * ⚠️ Đừng tự so `expiry_date` với hôm nay ở TypeScript để khỏi gọi API. Hai bản
 * luật ngày tháng sẽ lệch nhau vào đúng một ngày không ai để ý — và bên lệch là
 * bên người dùng nhìn. Bản in với tệp Excel cũng đọc con số của backend.
 */
export const DOSSIER_EXPIRY = {
  /** `expiry_date` bỏ trống — vô thời hạn, một câu trả lời THẬT. */
  NONE: 0,
  VALID: 1,
  /** Còn hạn nhưng trong ngưỡng cảnh báo (30 ngày). */
  NEAR: 2,
  OVER: 3,
} as const

export type DossierExpiryState = (typeof DOSSIER_EXPIRY)[keyof typeof DOSSIER_EXPIRY]

export const DOSSIER_EXPIRY_LABEL: Record<DossierExpiryState, string> = {
  [DOSSIER_EXPIRY.NONE]: 'Vô thời hạn',
  [DOSSIER_EXPIRY.VALID]: 'Còn hạn',
  [DOSSIER_EXPIRY.NEAR]: 'Sắp hết hạn',
  [DOSSIER_EXPIRY.OVER]: 'Hết hạn',
}

/** Giá trị của một ô tùy biến — vô hướng, backend chặn cây lồng nhau. */
export type DossierFieldValue = string | number | boolean | null

//  ⚠️ `type` chứ KHÔNG `interface`: khung CRUD ràng `T extends CrudRecord`
//  (`Record<string, unknown>`), mà TypeScript chỉ cấp "chỉ mục ngầm" cho type
//  alias — một `interface` y hệt sẽ báo không gán được.
export type Dossier = {
  id: number
  /** Máy cấp `HS0001` khi bỏ trống; không sửa được sau khi tạo. */
  code: string
  name: string
  dossier_type_id: number
  /**
   * Nhãn loại ĐÃ CHÉP — không phải trường suy ra lúc đọc.
   *
   * Backend giữ cột chữ riêng vì bản in và tệp Excel đọc thẳng nó (duoc-CR-320),
   * và tự chép lại khi danh mục đổi tên. Bày cột này chứ đừng đi tra tên qua
   * `dossier_type_id`: tra thì mỗi dòng một lần gọi.
   */
  dossier_type_name: string
  status: DossierStatus
  status_label: string
  /** Ngày cấp / ngày ký trên chính tờ giấy. ISO `yyyy-mm-dd`, rỗng = chưa nhập. */
  issued_date: string | null
  /** ⚠️ Rỗng = **vô thời hạn**, không phải thiếu dữ liệu. */
  expiry_date: string | null
  expiry_state: DossierExpiryState
  expiry_state_label: string
  /** Số ngày còn lại; âm = đã quá hạn; `null` = vô thời hạn (KHÁC `0`). */
  expiry_days: number | null
  /** Người chịu trách nhiệm theo dõi. `0` = chưa gắn. */
  owner_employee_id: number
  owner_name: string
  /** Bộ phận đang giữ bản gốc. */
  department_id: number
  department_name: string
  company_id: number
  company_name: string
  /** Nơi giữ bản giấy — vd `Tủ A2 · P. Hành chính`. */
  storage_location: string
  note: string
  /**
   * Giá trị của bộ trường tùy biến — khóa lấy từ `field_schema` của LOẠI **và**
   * từ `custom_fields` của chính hồ sơ này. Hai nguồn khai, MỘT kho giá trị.
   */
  extra_fields: Record<string, DossierFieldValue>
  /**
   * TRƯỜNG RIÊNG của hồ sơ này — người lập tự khai tại chỗ, không đụng khuôn
   * của loại. Cùng cấu trúc với `DossierType.field_schema`.
   *
   * ⚠️ Khóa không được trùng với ô của loại (backend chặn ở
   * `service.apply_extra_fields`): chung kho `extra_fields` nên trùng là hai ô
   * cùng ghi vào một chỗ.
   */
  custom_fields: DossierFieldDef[]
  /**
   * ĐIỀU KIỆN ÁP DỤNG — hồ sơ này phải kèm theo chứng từ nào.
   *
   * ⚠️ **Hai ca rỗng, hai nghĩa ngược nhau**: `apply_doc_kinds` rỗng = không
   * hiện ở đâu cả; có màn mà `apply_conditions` rỗng = áp cho MỌI phiếu loại
   * đó. Xem `dossier-applicability.ts`.
   */
  apply_doc_kinds: DocKind[]
  apply_conditions: ApplyCondition[]
  /**
   * HỒ SƠ TIÊN QUYẾT — `id` các tờ phải hoàn thành trước tờ này.
   *
   * ⚠️ Ràng buộc thuộc về TỜ GIẤY (khai một lần cho cả kho), nhưng «xong» thì
   * tính theo TỪNG CHỨNG TỪ — nên một tờ đang khóa ở phiếu A có thể đã mở ở
   * phiếu B. Chỗ tính khóa nằm ở backend, xem `ApplicableDossier.locked`.
   */
  depends: number[]
  /** Bộ sinh CRUD gắn thêm cho mọi bản ghi (bao-CR-294). */
  updated_at?: string | null
}

/**
 * Tiền tố tên ô của trường tùy biến trên biểu mẫu.
 *
 * ⚠️ Dấu chấm là CÓ Ý: react-hook-form hiểu nó là đường dẫn lồng nhau, nên
 * `register('extra_fields.so_gp')` tự dựng ra `{extra_fields: {so_gp: …}}` —
 * đúng hình dạng backend nhận, không phải ghép tay lúc gửi. Xem
 * `shared/crud/field-path.ts`.
 */
export const EXTRA_FIELD_PREFIX = 'extra_fields'

/** Tên ô trên biểu mẫu của một trường tùy biến. */
export function extraFieldName(key: string): string {
  return `${EXTRA_FIELD_PREFIX}.${key}`
}

/** Kiểu ô của khung CRUD tương ứng với kiểu trường tùy biến. */
export type { DossierFieldType }

/** Trần số hồ sơ tiên quyết — khớp `MAX_DOSSIER_DEPENDS` ở backend. */
export const MAX_DOSSIER_DEPENDS = 30
