import type {
  HrSettingField,
  HrSettingTab,
  HrSettingType,
  HrSettingValue,
  HrSettingValues,
  SettingsPayloadForHr,
} from '../types/hr-setting'

const TYPES: readonly HrSettingType[] = ['bool', 'roles', 'int', 'str', 'code_prefix', 'int_list']
const TABS: readonly HrSettingTab[] = ['employee', 'leave', 'contract']

/** Thứ tự + nhãn tab (giống trang HR Settings của ERPNext: Nhân viên đứng đầu). */
export const HR_SETTING_TABS: { value: HrSettingTab; label: string }[] = [
  { value: 'employee', label: 'Nhân viên' },
  { value: 'leave', label: 'Nghỉ phép' },
  { value: 'contract', label: 'Hợp đồng lao động' },
]

/** Ô phụ thuộc công tắc nào: công tắc TẮT thì ô bị làm mờ / khóa (vai trò miễn chỉ có nghĩa khi đang chặn lùi ngày). */
export const HR_SETTING_DEPENDS_ON: Record<string, string> = {
  leave_backdated_roles: 'leave_restrict_backdated',
}

/** Lấy các ô nhóm `hr` có kiểu + tab trang biết vẽ; ô lạ thì bỏ, không đoán. */
export function pickHrSettingFields(payload: SettingsPayloadForHr | undefined): HrSettingField[] {
  return (payload?.fields ?? []).filter(
    (field): field is HrSettingField =>
      field.group === 'hr' &&
      (TYPES as readonly string[]).includes(field.type) &&
      (TABS as readonly string[]).includes(field.tab ?? ''),
  )
}

/** Chuỗi `"a, b,,a"` → `['a', 'b']`: bỏ khoảng trắng, ô rỗng, trùng — cùng luật backend lưu. */
export function parseRoleCodes(raw: unknown): string[] {
  const items = Array.isArray(raw) ? raw : String(raw ?? '').split(',')
  return [...new Set(items.map((item) => String(item).trim()).filter(Boolean))]
}

/** Giá trị đang lưu → giá trị form. Công tắc chỉ BẬT khi đúng `true` (không coi chuỗi "true" là bật). */
export function toHrSettingValue(field: HrSettingField): HrSettingValue {
  if (field.type === 'bool') return field.value === true
  if (field.type === 'roles') return parseRoleCodes(field.value)
  return field.value === null || field.value === undefined ? '' : String(field.value)
}

export function toHrSettingValues(fields: HrSettingField[]): HrSettingValues {
  return Object.fromEntries(fields.map((field) => [field.key, toHrSettingValue(field)]))
}

/** Giá trị form → thân lưu (`values` của `PUT /api/settings`): vai trò gửi `"a,b"`, ô chữ / số gửi nguyên chuỗi đã cắt. */
export function toHrSettingPayload(fields: HrSettingField[], values: HrSettingValues): Record<string, unknown> {
  return Object.fromEntries(
    fields.map((field) => {
      const value = values[field.key]
      if (field.type === 'bool') return [field.key, value === true]
      if (field.type === 'roles') return [field.key, (Array.isArray(value) ? value : []).join(',')]
      return [field.key, typeof value === 'string' ? value.trim() : '']
    }),
  )
}
