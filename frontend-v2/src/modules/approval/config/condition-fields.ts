import { CONFIDENTIAL_LEVELS, URGENCY_LEVELS } from '@/modules/document/types/security-level'
import type { ConditionOp } from '../helpers/node-condition'

/**
 * Giá trị của ô lấy ở đâu ra. `level` là thang cố định khai ngay tại đây; ba
 * nguồn còn lại là danh mục động, bộ dựng nạp bằng hook của phân hệ tương ứng.
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
const OPS_THANG: ConditionOp[] = ['gte', 'lte', 'eq', 'ne']
/** Danh mục thì không có "lớn hơn" — id lớn hơn không nghĩa là gì cả. */
const OPS_DANH_MUC: ConditionOp[] = ['in', 'not_in']

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
    ops: OPS_THANG,
    choices: CONFIDENTIAL_LEVELS.map((item) => ({ value: item.id, label: item.name })),
    hint: 'Ví dụ: chỉ văn bản từ Mật trở lên mới qua bước này.',
  },
  {
    name: 'urgency',
    label: 'Độ khẩn',
    source: 'level',
    ops: OPS_THANG,
    choices: URGENCY_LEVELS.map((item) => ({ value: item.id, label: item.name })),
  },
  { name: 'doc_type_id', label: 'Loại văn bản', source: 'doc_type', ops: OPS_DANH_MUC },
  { name: 'company_id', label: 'Pháp nhân', source: 'company', ops: OPS_DANH_MUC },
  { name: 'department_id', label: 'Phòng ban soạn', source: 'department', ops: OPS_DANH_MUC },
  { name: 'signer_employee_id', label: 'Người ký', source: 'employee', ops: OPS_DANH_MUC },
  { name: 'owner_employee_id', label: 'Người phụ trách', source: 'employee', ops: OPS_DANH_MUC },
  { name: 'drafter_employee_id', label: 'Người soạn', source: 'employee', ops: OPS_DANH_MUC },
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
