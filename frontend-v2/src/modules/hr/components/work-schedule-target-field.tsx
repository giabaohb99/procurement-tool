import { useQuery } from '@tanstack/react-query'
import { useController, useWatch, type Control } from 'react-hook-form'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { CrudRecord } from '@/shared/crud'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect, type SearchSelectOption } from '@/shared/ui/search-select'
import { SYSTEM_LEVEL_LABEL, WORK_SCHEDULE_LEVEL_CODE } from '../types/work-schedule'
import { isChosenId } from '../utils/work-schedule-validation'

interface WorkScheduleTargetFieldProps {
  control: Control<CrudRecord>
  /** Tên ô đối tượng trong form (`target_id`). */
  name: string
  /** Tên ô cấp để theo dõi (`target_level`). */
  levelName: string
  /**
   * Tên ô ẨN giữ `target_name` của dòng đang sửa. Đối tượng đã lưu mà không còn trong
   * danh sách (nhân sự đã nghỉ, ngoài phạm vi…) thì hiện tên này thay vì «#7».
   */
  nameFieldName?: string
  disabled?: boolean
}

type Row = Record<string, unknown>

/** Nguồn danh sách theo cấp; «Toàn hệ thống» không có đối tượng nên không có nguồn. */
const SOURCES: Record<number, { url: string; label: (row: Row) => string }> = {
  [WORK_SCHEDULE_LEVEL_CODE.COMPANY]: { url: '/api/companies', label: (r) => String(r.name ?? '') },
  [WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT]: { url: '/api/departments', label: (r) => String(r.name ?? '') },
  [WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE]: {
    url: '/api/employees',
    label: (r) => [r.code, r.full_name].filter(Boolean).join(' — '),
  },
}

/** Lấy mảng bản ghi từ `{items: []}` hoặc mảng trần; dạng khác -> rỗng. */
function extractRows(payload: unknown): Row[] {
  const rows =
    Array.isArray(payload)
      ? payload
      : payload && typeof payload === 'object' && 'items' in payload
        ? (payload as { items: unknown }).items
        : []
  return Array.isArray(rows) ? (rows as Row[]) : []
}

/**
 * Ô «Đối tượng áp dụng» — danh sách ĐỔI THEO cấp đang chọn. Cấp «Toàn hệ thống»
 * ẩn ô chọn (giá trị luôn 0). Việc xóa đối tượng khi đổi cấp do
 * `WorkScheduleLevelField` lo; backend vẫn kiểm đối tượng có thật.
 */
export function WorkScheduleTargetField({
  control,
  name,
  levelName,
  nameFieldName = 'target_name',
  disabled = false,
}: WorkScheduleTargetFieldProps) {
  const level = Number(useWatch({ control, name: levelName }))
  const savedName = String(useWatch({ control, name: nameFieldName }) ?? '').trim()
  const { field, fieldState } = useController({
    control,
    name,
    //  `formValues` luôn là giá trị MỚI NHẤT của cả form — cấp «Toàn hệ thống» không có đối tượng.
    rules: {
      validate: (value, formValues) =>
        Number(formValues[levelName]) === WORK_SCHEDULE_LEVEL_CODE.SYSTEM ||
        isChosenId(value) ||
        'Chọn đối tượng áp dụng.',
    },
  })
  const source = SOURCES[level]

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.hr.workScheduleTargets(level),
    queryFn: async () => {
      const rows = extractRows(await apiGet<unknown>(source.url, { params: { page_size: 1000 } }))
      return rows.map<SearchSelectOption>((row) => ({
        value: String(row.id ?? ''),
        label: source.label(row) || `#${String(row.id ?? '')}`,
      }))
    },
    enabled: Boolean(source),
    //  Ngắn: nhân sự / phòng ban mới tạo ở màn khác phải có mặt khi HR quay lại gán lịch.
    staleTime: 30 * 1000,
  })

  if (level === WORK_SCHEDULE_LEVEL_CODE.SYSTEM) {
    return (
      <div className="space-y-1.5">
        <Label>Đối tượng áp dụng</Label>
        <ReadOnlyValue>{SYSTEM_LEVEL_LABEL}</ReadOnlyValue>
      </div>
    )
  }
  if (!source) return null

  const value = Number(field.value) > 0 ? String(field.value) : ''
  const options = data ?? []
  //  Đối tượng đang lưu mà không còn trong danh sách (nhân sự đã nghỉ…) vẫn phải
  //  hiện ra, kẻo ô trống và người sửa tưởng chưa chọn.
  const withCurrent =
    value && !options.some((o) => o.value === value)
      ? [{ value, label: savedName || `#${value}` }, ...options]
      : options

  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>
        Đối tượng áp dụng
        <RequiredMark />
      </Label>
      {disabled ? (
        <ReadOnlyValue>{withCurrent.find((o) => o.value === value)?.label ?? ''}</ReadOnlyValue>
      ) : (
        <SearchSelect
          id={name}
          value={value}
          onChange={(next) => field.onChange(next ? Number(next) : 0)}
          options={withCurrent}
          searchInTrigger
          placeholder={isLoading ? 'Đang tải…' : 'Chọn đối tượng'}
          searchPlaceholder="Tìm theo tên hoặc mã…"
          emptyMessage="Chưa có mục nào để chọn"
        />
      )}
      {fieldState.error?.message && (
        <p role="alert" className="text-xs text-destructive">
          {fieldState.error.message}
        </p>
      )}
      {isError && (
        <p className="text-xs text-destructive">
          Không tải được danh sách đối tượng. Thử tải lại trang.
        </p>
      )}
    </div>
  )
}
