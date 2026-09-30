import type { ConditionField } from '@/shared/condition-builder/condition-rule'

/**
 * Giá trị của ô lấy ở đâu ra. `handler_department` khác `department` ở một chỗ:
 * phòng thu mua mặc định bị gỡ khỏi danh sách (xem `PR_DISPATCH_CONDITION_FIELDS`).
 */
export type PrDispatchValueSource =
  | 'handler_department'
  | 'department'
  | 'company'
  | 'employee'
  | 'none'

export interface PrDispatchConditionField extends ConditionField {
  source: PrDispatchValueSource
}

/**
 * Các ô của phiếu YCMH đem ra làm «điều kiện bỏ qua bước thu mua duyệt lần 2»
 * (ô `pr_dispatch_skip_rules` ở màn Cấu hình hệ thống — bao-CR-497, bộ chọn ở
 * bao-CR-528).
 *
 * Đúng bằng những khóa `purchase_request/service.dispatch_context()` đưa vào
 * điều kiện (bảng `DISPATCH_CONTEXT_FIELDS` cùng tệp). Thêm một ô ở đây mà
 * backend không gửi khóa đó thì cửa lưu trả 400 — đó là cố ý, đừng nới.
 *
 * ⚠️ «Phòng xử lý»: bối cảnh phiếu đưa phòng thu mua mặc định (Sản xuất -Thu
 * mua) vào dưới dạng **0** — tức «để trống». Vì vậy phòng đó KHÔNG có trong danh
 * sách chọn của ô này: chọn nó ở phép «thuộc» thì không phiếu nào khớp. Điều
 * kiện hay dùng nhất là «Phòng xử lý có giá trị» = phiếu nhờ phòng khác xử lý.
 */
export const PR_DISPATCH_CONDITION_FIELDS: PrDispatchConditionField[] = [
  {
    name: 'handler_dept_id',
    label: 'Phòng xử lý',
    source: 'handler_department',
    ops: ['not_empty', 'empty', 'in', 'not_in'],
  },
  { name: 'department_id', label: 'Phòng lập phiếu', source: 'department', ops: ['in', 'not_in'] },
  { name: 'company_id', label: 'Công ty', source: 'company', ops: ['in', 'not_in'] },
  { name: 'requester_id', label: 'Người yêu cầu', source: 'employee', ops: ['in', 'not_in'] },
  { name: 'is_urgent', label: 'Đơn gấp', source: 'none', kind: 'bool', ops: ['eq'] },
  {
    name: 'line_count',
    label: 'Số dòng hàng',
    source: 'none',
    kind: 'number',
    ops: ['lte', 'gte', 'eq', 'lt', 'gt'],
  },
]

/** Mã phòng thu mua mặc định khi ô `central_purchasing_dept_code` để trống (khớp backend). */
export const DEFAULT_CENTRAL_DEPT_CODE = 'PBA017'

/**
 * Bộ trường điều kiện màn Cấu hình vẽ được bằng bộ chọn. Ô `type: 'condition'`
 * khai bộ lạ thì hàng cấu hình rơi về ô chữ — thà sửa được dạng chuỗi còn hơn
 * bày một bộ chọn đoán mò.
 */
export const SUPPORTED_CONDITION_ENTITIES = ['pr_dispatch']
