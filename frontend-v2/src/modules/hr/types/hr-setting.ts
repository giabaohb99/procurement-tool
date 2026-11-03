/**
 * Một ô của trang Cài đặt nhân sự (duoc-CR-713) — chính là trường nhóm `hr` của `GET /api/settings`
 * (`FIELDS` ở `backend/app/modules/setting/service.py`). Backend giữ nhãn, lời giải thích, tab và dải số; trang chỉ
 * vẽ lại — thêm một cài đặt mới ở backend là trang tự có (đúng tab), không phải sửa ở đây.
 *
 * Khai riêng ở phân hệ Nhân sự (không mượn kiểu của phân hệ Quản trị) để khỏi import chéo phân hệ.
 */
export type HrSettingType = 'bool' | 'roles' | 'int' | 'str' | 'code_prefix' | 'int_list'

/** Tab của trang — backend gán qua khóa `tab`. */
export type HrSettingTab = 'employee' | 'leave' | 'contract'

export interface HrSettingField {
  key: string
  group: string
  tab: HrSettingTab
  label: string
  type: HrSettingType
  value: unknown
  hint?: string
  /** Dải số của ô `int` — cửa lưu backend kiểm lại, đây chỉ để gợi ý trên ô nhập. */
  min?: number
  max?: number
}

/** Hình dạng `GET /api/settings` — chỉ phần trang này đọc. */
export interface SettingsPayloadForHr {
  fields: (Omit<HrSettingField, 'type' | 'tab'> & { type: string; tab?: string })[]
}

/** Giá trị đang soạn: công tắc = boolean, vai trò = mảng mã, còn lại = chuỗi đúng như gõ. */
export type HrSettingValue = boolean | string[] | string
export type HrSettingValues = Record<string, HrSettingValue>
