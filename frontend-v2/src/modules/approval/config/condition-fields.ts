import {
  FALLBACK_CONFIDENTIAL_LEVELS,
  FALLBACK_URGENCY_LEVELS,
} from '@/modules/document/types/security-level'
import type { ConditionField, ConditionOp } from '@/shared/condition-builder/condition-rule'

/**
 * Giá trị của ô lấy ở đâu ra. `level` dùng BẢN DỰ PHÒNG khai ngay tại đây (mảng
 * này dựng lúc import module, không gọi được hook) vì mức mật / độ khẩn nay là
 * danh mục sửa được — không còn là nguồn chân lý, xem đầu
 * `modules/document/types/security-level.ts`. Ba nguồn còn lại là danh mục
 * động, bộ dựng nạp bằng hook của phân hệ tương ứng.
 */
export type ConditionValueSource =
  | 'level'
  | 'doc_type'
  | 'seal_type'
  | 'company'
  | 'department'
  | 'employee'

/**
 * Một ô của luồng duyệt. `name` phải khớp KHÓA trong bối cảnh phiếu
 * (`approval_bridge.boi_canh`); phần chung (nhãn, phép so) ở `ConditionField`.
 */
export interface ConditionFieldDef extends ConditionField {
  source: ConditionValueSource
  choices?: { value: number; label: string }[]
}

/** Phép so lớn nhỏ chỉ có nghĩa trên thang có thứ bậc (mức mật, độ khẩn). */
const MONTH_OPS: ConditionOp[] = ['gte', 'lte', 'eq', 'ne']
/** Danh mục thì không có "lớn hơn" — id lớn hơn không nghĩa là gì cả. */
const CATALOG_OPS: ConditionOp[] = ['in', 'not_in']

/**
 * Các ô của VĂN BẢN có thể đem ra rẽ nhánh.
 *
 * Đúng bằng những khóa `approval_bridge.boi_canh()` đưa sang — thêm một ô ở đây
 * mà backend không gửi khóa đó thì điều kiện **không bao giờ khớp** và nhánh
 * lặng lẽ không chạy. Cố ý bỏ `id` (văn bản cụ thể): đó là việc của bộ chọn
 * «Áp cho phiếu nào» ở tầng luồng, lặp lại ở đây chỉ làm hai chỗ nói khác nhau.
 */
export const DOCUMENT_CONDITION_FIELDS: ConditionFieldDef[] = [
  {
    name: 'secrecy_level',
    label: 'Mức mật',
    source: 'level',
    ops: MONTH_OPS,
    // `.value`, KHÔNG phải `.id`: điều kiện lưu xuống DB dạng
    // `{"field":"secrecy_level","op":"gte","value":3}`, so trực tiếp với con số
    // trên văn bản (`tab_document.secrecy_level`), không phải khóa chính danh mục.
    choices: FALLBACK_CONFIDENTIAL_LEVELS.map((item) => ({ value: item.value, label: item.name })),
    hint: 'Ví dụ: chỉ văn bản từ Mật trở lên mới qua bước này.',
  },
  {
    name: 'urgency',
    label: 'Độ khẩn',
    source: 'level',
    ops: MONTH_OPS,
    choices: FALLBACK_URGENCY_LEVELS.map((item) => ({ value: item.value, label: item.name })),
  },
  { name: 'doc_type_id', label: 'Loại văn bản', source: 'doc_type', ops: CATALOG_OPS },
  { name: 'company_id', label: 'Pháp nhân', source: 'company', ops: CATALOG_OPS },
  { name: 'department_id', label: 'Phòng ban soạn', source: 'department', ops: CATALOG_OPS },
  { name: 'signer_employee_id', label: 'Người ký', source: 'employee', ops: CATALOG_OPS },
  { name: 'owner_employee_id', label: 'Người phụ trách', source: 'employee', ops: CATALOG_OPS },
  { name: 'drafter_employee_id', label: 'Người soạn', source: 'employee', ops: CATALOG_OPS },
]

/** Hai loại phiếu đặt xe — khớp `TYPE_CAR` / `TYPE_DELIVERY` của backend. */
export const BOOKING_REQUEST_TYPES = [
  { value: 1, label: 'Đặt xe công tác' },
  { value: 2, label: 'Giao hàng' },
]

/**
 * Các ô của PHIẾU ĐẶT XE đem ra rẽ nhánh (bao-CR-579).
 *
 * Khớp `vehicle_booking/approval_bridge.entity_context`. Ô người là
 * `requester_employee_id` (id NHÂN SỰ), không phải `requester_id` — cột đó trên
 * phiếu là id TÀI KHOẢN, chọn người ở bộ dựng ra id nhân sự nên so với nó là
 * không bao giờ khớp.
 */
export const VEHICLE_BOOKING_CONDITION_FIELDS: ConditionFieldDef[] = [
  {
    name: 'request_type',
    label: 'Loại phiếu',
    source: 'level',
    ops: ['eq', 'ne'],
    choices: BOOKING_REQUEST_TYPES,
    hint: 'Ví dụ: phiếu giao hàng đi luồng có thêm Giám đốc.',
  },
  { name: 'company_id', label: 'Pháp nhân', source: 'company', ops: CATALOG_OPS },
  { name: 'department_id', label: 'Phòng ban người tạo', source: 'department', ops: CATALOG_OPS },
  { name: 'requester_employee_id', label: 'Người tạo phiếu', source: 'employee', ops: CATALOG_OPS },
]

/**
 * Các ô của PHIẾU DUYỆT DẤU đem ra rẽ nhánh (bao-CR-579). Khớp
 * `seal_request/approval_bridge.entity_context`. «Pháp nhân» là công ty CHÍNH
 * của phiếu; phiếu đóng dấu nhiều công ty thì chỉ công ty đầu được xét.
 */
export const SEAL_REQUEST_CONDITION_FIELDS: ConditionFieldDef[] = [
  { name: 'seal_type_id', label: 'Loại con dấu', source: 'seal_type', ops: CATALOG_OPS },
  { name: 'company_id', label: 'Pháp nhân (công ty chính)', source: 'company', ops: CATALOG_OPS },
  { name: 'department_id', label: 'Phòng ban', source: 'department', ops: CATALOG_OPS },
  { name: 'requester_employee_id', label: 'Người tạo phiếu', source: 'employee', ops: CATALOG_OPS },
]

/**
 * Loại chứng từ nào đã khai được điều kiện bằng bộ dựng.
 *
 * Loại chưa có mặt ở đây thì bộ dựng nói thẳng là chưa hỗ trợ thay vì bày một
 * danh mục ô đoán mò. Thêm một loại vào đây phải đi kèm khóa tương ứng trong
 * `entity_context` của `approval_bridge` bên backend, nếu không điều kiện không
 * bao giờ khớp và nhánh lặng lẽ không chạy.
 */
export const CONDITION_FIELDS_BY_ENTITY: Record<string, ConditionFieldDef[]> = {
  document: DOCUMENT_CONDITION_FIELDS,
  vehicle_booking: VEHICLE_BOOKING_CONDITION_FIELDS,
  seal_request: SEAL_REQUEST_CONDITION_FIELDS,
}

/** Một ô trên phiếu ghi sẵn người duyệt — dùng cho cách chọn «Lấy từ một ô trên phiếu». */
export interface ApproverFieldDef {
  name: string
  label: string
}

/**
 * Các ô CHỌN ĐƯỢC cho cách «Lấy từ một ô trên phiếu» (bao-CR-579).
 *
 * Trước đây là ô gõ tay tên cột — gõ sai một chữ thì bước không ra ai, phiếu kẹt.
 * Khóa phải khớp `entity_context` bên backend và phải mang id NHÂN SỰ.
 */
export const APPROVER_FIELDS_BY_ENTITY: Record<string, ApproverFieldDef[]> = {
  document: [
    { name: 'signer_employee_id', label: 'Người ký' },
    { name: 'owner_employee_id', label: 'Người phụ trách' },
    { name: 'drafter_employee_id', label: 'Người soạn' },
  ],
  //  Đặt xe CỐ Ý không có ô nào: form tạo phiếu đặt xe không cho người tạo chọn người
  //  duyệt, nên `first_approver_employee_id` luôn trống — khai bước theo ô đó là phiếu
  //  kẹt ngay chặng 1. Có ô chọn trên form rồi mới mở lại.
  vehicle_booking: [],
  seal_request: [
    { name: 'first_approver_employee_id', label: 'Trưởng bộ phận do người tạo chọn trên phiếu' },
  ],
}

export function approverFieldsOf(entity: string): ApproverFieldDef[] {
  return APPROVER_FIELDS_BY_ENTITY[entity] ?? []
}

export function conditionFieldsOf(entity: string): ConditionFieldDef[] {
  return CONDITION_FIELDS_BY_ENTITY[entity] ?? []
}
