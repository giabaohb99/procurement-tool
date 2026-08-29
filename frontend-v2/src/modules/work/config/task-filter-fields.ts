import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { workApi } from '../api/work-api'
import {
  fieldHasOptions,
  WORK_FIELD_TYPE,
  WORK_STATUS_LABELS,
  WORK_TASK_STATUS,
  type WorkLabelField,
} from '../types/work'
import { multiKey } from '../utils/task-conditions'

/**
 * Khai các trường cho BỘ LỌC ĐIỀU KIỆN của bảng công việc (§3.3) — nút «Lọc»
 * trên thanh công cụ, đúng chỗ Lark đặt nó.
 *
 * Lọc chạy hoàn toàn Ở TRÌNH DUYỆT (`applyClientFilter`) vì bảng đã tải cả
 * danh sách: nút này KHÔNG dịch ra query param, nên tên trường ở đây không cần
 * nằm trong whitelist nào của backend — nó là tên khóa trong
 * `toFilterableTask`.
 *
 * Trường ĐA TRỊ (người phụ trách, và mọi trường tùy biến kiểu chọn nhiều — Tag
 * chẳng hạn) không so bằng `=` được vì một việc mang nhiều giá trị; chúng được
 * ghép thành chuỗi `|3|7|` và chỉ mở hai phép *chứa / không chứa* — xem
 * `multiKey`.
 */
export function buildTaskFilterFields(
  listId: number,
  labelFields: WorkLabelField[] = [],
): FilterFieldDefinition[] {
  return [
    { name: 'title', label: 'Tiêu đề', type: 'text' },
    {
      name: 'status',
      label: 'Trạng thái',
      type: 'select',
      operators: ['is', 'is_not', 'in', 'not_in'],
      options: Object.values(WORK_TASK_STATUS).map((v) => ({
        value: String(v),
        label: WORK_STATUS_LABELS[v],
      })),
    },
    {
      name: 'section_id',
      label: 'Cột',
      type: 'combobox',
      operators: ['is', 'is_not', 'in', 'not_in'],
      fetchOptions: async () => {
        const rows = await workApi.sections(listId)
        return rows.map((s) => ({ value: String(s.id), label: s.name }))
      },
    },
    {
      name: 'pic_keys',
      label: 'Người phụ trách',
      type: 'combobox',
      //  Một việc có nhiều người phụ trách nên «bằng» vô nghĩa: chỉ hỏi được
      //  danh sách đó CÓ CHỨA người này không.
      operators: ['contains', 'not_contains', 'is_empty', 'is_not_empty'],
      fetchOptions: async () => {
        const rows = await workApi.members(listId)
        return rows.map((m) => ({
          value: multiKey(m.employee_id),
          label: m.employee_name || m.employee_code,
        }))
      },
    },
    {
      //  Thay cho lát cắt «Tôi tạo» đã bỏ khỏi thanh công cụ.
      name: 'creator_employee_id',
      label: 'Người tạo',
      type: 'combobox',
      operators: ['is', 'is_not', 'in', 'not_in'],
      fetchOptions: async () => {
        const rows = await workApi.members(listId)
        return rows.map((m) => ({
          value: String(m.employee_id),
          label: m.employee_name || m.employee_code,
        }))
      },
    },
    { name: 'due_date', label: 'Hạn chót', type: 'date' },
    { name: 'start_date', label: 'Ngày bắt đầu', type: 'date' },
    { name: 'created_at', label: 'Ngày tạo', type: 'date' },
    { name: 'completed_at', label: 'Ngày hoàn thành', type: 'date' },
    ...labelFields.map(labelFilterField),
  ]
}

/**
 * Một TRƯỜNG TÙY BIẾN thành một trường lọc. Độ ưu tiên đi đúng đường này — nó
 * không còn là cột cứng nên cũng không còn khai tay ở danh sách trên.
 *
 * Trường có bộ giá trị dùng phép «chứa» chứ không «bằng»: kiểu chọn nhiều thì
 * một việc mang nhiều giá trị, mà chuỗi đã rào `|` nên không khớp nhầm.
 */
function labelFilterField(field: WorkLabelField): FilterFieldDefinition {
  const name = `label_${field.id}`
  if (fieldHasOptions(field.field_type))
    return {
      name,
      label: field.name,
      type: 'select',
      operators: ['contains', 'not_contains', 'is_empty', 'is_not_empty'],
      options: field.options.map((o) => ({ value: multiKey(o.id), label: o.name })),
    }
  if (field.field_type === WORK_FIELD_TYPE.DATE)
    return { name, label: field.name, type: 'date' }
  if (field.field_type === WORK_FIELD_TYPE.NUMBER)
    return { name, label: field.name, type: 'number' }
  return { name, label: field.name, type: 'text' }
}
