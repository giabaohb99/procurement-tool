import type { WorkLabelField, WorkMember, WorkTaskLabelValue } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'
import { personName } from './people'

function blank(fieldId: number): WorkTaskLabelValue {
  return {
    field_id: fieldId,
    option_id: null,
    value_text: '',
    value_number: null,
    value_date: '',
    value_employee_id: null,
    value_employee_name: '',
  }
}

/**
 * Dựng giá trị nhãn để HIỂN THỊ cho dòng đang soạn (task chưa tồn tại).
 *
 * `LabelFieldInput` nhận vào `WorkTaskLabelValue[]` — thứ máy chủ trả về — còn
 * `onChange` của nó lại trả ra giá trị thô, đa hình theo `field_type`. Với task
 * đã có thì không sao: ghi xuống máy chủ rồi đọc lại. Dòng đang soạn thì chưa có
 * gì để đọc lại, nên phải tự dịch ngược ngay tại chỗ, không thì người dùng chọn
 * xong mà ô vẫn trống trơn và tưởng bấm hụt.
 *
 * Giá trị không hợp kiểu (bản nháp cũ, người dùng bấm bỏ chọn) trả về mảng RỖNG
 * — cùng nghĩa "chưa đặt" với dữ liệu thật.
 */
export function toDraftLabelValues(
  field: WorkLabelField,
  raw: unknown,
  members: WorkMember[],
): WorkTaskLabelValue[] {
  if (raw === null || raw === undefined || raw === '') return []

  switch (field.field_type) {
    case WORK_FIELD_TYPE.MULTI:
      if (!Array.isArray(raw)) return []
      return raw
        .filter((id): id is number => typeof id === 'number')
        .map((id) => ({ ...blank(field.id), option_id: id }))

    case WORK_FIELD_TYPE.PERSON: {
      if (typeof raw !== 'number') return []
      const member = members.find((m) => m.employee_id === raw)
      return [
        {
          ...blank(field.id),
          value_employee_id: raw,
          value_employee_name: member ? personName(member.employee_name, raw) : '',
        },
      ]
    }

    case WORK_FIELD_TYPE.NUMBER:
      return [{ ...blank(field.id), value_number: String(raw) }]

    case WORK_FIELD_TYPE.DATE:
      return typeof raw === 'string' ? [{ ...blank(field.id), value_date: raw }] : []

    case WORK_FIELD_TYPE.TEXT:
      return typeof raw === 'string' ? [{ ...blank(field.id), value_text: raw }] : []

    default:
      return typeof raw === 'number' ? [{ ...blank(field.id), option_id: raw }] : []
  }
}
