import {
  FALLBACK_CONFIDENTIAL_LEVELS,
  FALLBACK_URGENCY_LEVELS,
} from '@/modules/document/types/security-level'
import type { ConditionOp } from '../helpers/node-condition'

/**
 * Giá trị của ô lấy ở đâu ra. `level` dùng BẢN DỰ PHÒNG khai ngay tại đây (mảng
 * này dựng lúc import module, không gọi được hook) vì mức mật / độ khẩn nay là
 * danh mục sửa được — không còn là nguồn chân lý, xem đầu
 * `modules/document/types/security-level.ts`. Ba nguồn còn lại là danh mục
 * động, bộ dựng nạp bằng hook của phân hệ tương ứng.
 */
export type ConditionValueSource = 'level' | 'doc_type' | 'company' | 'department' | 'employee'

export interface ConditionFieldDef {
  /** Phải khớp KHÓA trong bối cảnh phiếu (`approval_bridge.boi_canh`). */
  name: string
  label: string
  source: ConditionValueSource
  /** Chỉ bày những phép có nghĩa với ô này — bày đủ tám phép là bày cả phép sai. */
  ops: ConditionOp[]
  choices?: { value: number; label: string }[]
  hint?: string
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

/**
 * Loại chứng từ nào đã khai được điều kiện bằng bộ dựng.
 *
 * Loại chưa có mặt ở đây thì chưa có cầu nối sang bộ máy duyệt
 * (`approval_bridge` mới chỉ có ở văn bản) — bày một danh mục ô đoán mò còn tệ
 * hơn nói thẳng là chưa hỗ trợ.
 */
export const CONDITION_FIELDS_BY_ENTITY: Record<string, ConditionFieldDef[]> = {
  document: DOCUMENT_CONDITION_FIELDS,
}

export function conditionFieldsOf(entity: string): ConditionFieldDef[] {
  return CONDITION_FIELDS_BY_ENTITY[entity] ?? []
}
