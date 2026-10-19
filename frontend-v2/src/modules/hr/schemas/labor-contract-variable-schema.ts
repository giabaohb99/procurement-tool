import { z } from 'zod'

import type { LaborContractVariable } from '../types/labor-contract-variable'
import { VARIABLE_SOURCE_SYSTEM, VARIABLE_TYPE_TEXT } from '../types/labor-contract-variable'

/** Hình dạng mã biến của backend (`variable_rules.CODE_RE`). Danh sách từ cấm / mã hệ thống để backend kiểm. */
export const VARIABLE_CODE_PATTERN = /^[a-z][a-z0-9_]{1,39}$/

const labelText = z.string().trim().min(1, 'Nhập tên hiển thị').max(200, 'Tên hiển thị tối đa 200 ký tự')
const descriptionText = z.string().trim().max(500, 'Mô tả tối đa 500 ký tự')

/**
 * Form hộp thêm / sửa biến. Chỉ kiểm HÌNH DẠNG và độ dài khớp cột backend (40/200/500/255/2000, thứ tự
 * 0..9999); luật nghiệp vụ (từ cấm, trùng mã hệ thống, kiểu của giá trị mặc định) do backend trả 422.
 * Biến hệ thống chỉ sửa tên / mô tả / ẩn nên các ô còn lại bỏ qua kiểm.
 */
export function buildVariableSchema(isSystem: boolean) {
  return z.object({
    code: isSystem
      ? z.string()
      : z
          .string()
          .trim()
          .max(40, 'Mã biến tối đa 40 ký tự')
          .regex(VARIABLE_CODE_PATTERN, 'Mã biến gồm chữ thường không dấu, số, dấu gạch dưới; bắt đầu bằng chữ (vd so_ngay_phep)'),
    label: labelText,
    description: descriptionText,
    example: isSystem ? z.string() : z.string().trim().max(255, 'Ví dụ tối đa 255 ký tự'),
    value_type: z.number().int().min(1).max(5),
    default_value: isSystem ? z.string() : z.string().max(2000, 'Giá trị mặc định tối đa 2000 ký tự'),
    is_required: z.boolean(),
    is_active: z.boolean(),
    is_hidden: z.boolean(),
    sort_order: isSystem
      ? z.number()
      : z.number().int('Thứ tự là số nguyên').min(0, 'Thứ tự từ 0').max(9999, 'Thứ tự tối đa 9999'),
  })
}

export type VariableFormValues = z.infer<ReturnType<typeof buildVariableSchema>>

export function buildVariableFormDefaults(variable: LaborContractVariable | null): VariableFormValues {
  if (!variable) {
    return {
      code: '',
      label: '',
      description: '',
      example: '',
      value_type: VARIABLE_TYPE_TEXT,
      default_value: '',
      is_required: false,
      is_active: true,
      is_hidden: false,
      sort_order: 0,
    }
  }
  return {
    code: variable.code,
    label: variable.label,
    description: variable.description,
    example: variable.example,
    value_type: variable.value_type,
    default_value: variable.default_value,
    is_required: variable.is_required,
    is_active: variable.is_active,
    is_hidden: variable.is_hidden,
    sort_order: variable.sort_order,
  }
}

export function isSystemVariable(variable: Pick<LaborContractVariable, 'source'> | null): boolean {
  return variable?.source === VARIABLE_SOURCE_SYSTEM
}
