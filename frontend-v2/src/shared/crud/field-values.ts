import type { CrudFormField } from './types'

/**
 * Quy đổi giá trị giữa DẠNG LƯU (payload gửi backend) và DẠNG NHẬP (ô trên form).
 *
 * Tách ra khỏi hai màn dùng nó (`crud-form-dialog` thêm mới, `crud-detail-page`
 * sửa) vì cả hai BẮT BUỘC quy đổi giống hệt nhau: lệch một chỗ là thêm mới với
 * sửa cho ra hai kết quả khác nhau trên cùng một trường.
 */

/** Số chữ số thập phân giữ lại cho DẠNG LƯU của trường phần trăm. */
const RATIO_DECIMALS = 6

function round(value: number, decimals: number): number {
  const factor = 10 ** decimals
  return Math.round(value * factor) / factor
}

/**
 * TỈ LỆ (0.08) -> SỐ PHẦN TRĂM để đổ vào ô nhập (8).
 *
 * Phải làm tròn: `0.07 * 100` trong JS ra `7.000000000000001`, đổ thẳng vào ô
 * `type="number"` là người dùng nhìn thấy nguyên cái đuôi đó.
 */
export function ratioToPercentInput(ratio: unknown): number {
  const num = Number(ratio)
  if (!Number.isFinite(num)) return 0
  return round(num * 100, RATIO_DECIMALS - 2)
}

/** SỐ PHẦN TRĂM người dùng gõ (8) -> TỈ LỆ để gửi backend (0.08). */
export function percentInputToRatio(percent: unknown): number {
  const num = Number(percent)
  if (!Number.isFinite(num)) return 0
  return round(num / 100, RATIO_DECIMALS)
}

/**
 * Giá trị khởi tạo cho react-hook-form.
 *
 * `defaultValue` khai trong config luôn ở DẠNG LƯU (vd `defaultValue: 0.08` cho
 * VAT 8%) để giống hệt thứ backend trả về — người viết config không phải nhớ
 * trường nào quy đổi, trường nào không.
 */
export function buildFormDefaults(
  fields: CrudFormField[],
  item?: Record<string, unknown> | null,
): Record<string, unknown> {
  const values: Record<string, unknown> = {}

  for (const field of fields) {
    const stored = item ? item[field.name] : undefined
    const source = stored !== undefined ? stored : field.defaultValue

    if (source !== undefined) {
      values[field.name] = field.type === 'percent' ? ratioToPercentInput(source) : source
    } else if (field.type === 'switch') {
      values[field.name] = true
    } else if (field.type === 'number' || field.type === 'percent') {
      values[field.name] = 0
    } else {
      values[field.name] = ''
    }
  }

  return values
}

/** Giá trị trên form -> payload gửi backend. */
export function toApiPayload(
  fields: CrudFormField[],
  values: Record<string, unknown>,
): Record<string, unknown> {
  const payload: Record<string, unknown> = { ...values }

  for (const field of fields) {
    const raw = payload[field.name]
    if (raw === undefined) continue

    if (field.type === 'percent') {
      // Ô trống nghĩa là 0%, không phải "bỏ trường này đi": backend khai `vat`
      // là số bắt buộc nên gửi chuỗi rỗng sẽ 422.
      payload[field.name] = percentInputToRatio(raw === '' ? 0 : raw)
    } else if (field.type === 'number' && raw !== '') {
      payload[field.name] = Number(raw)
    }
  }

  return payload
}
