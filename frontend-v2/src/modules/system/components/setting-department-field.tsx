import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { SearchSelect } from '@/shared/ui/search-select'

import type { SettingField } from '../types/setting'

interface SettingDepartmentFieldProps {
  field: SettingField
  disabled: boolean
  onChange: (key: string, value: unknown) => void
}

/**
 * Ô cấu hình kiểu `department` — CHỌN từ danh mục Phòng ban thay cho gõ mã (bao-CR-529).
 *
 * Giá trị gửi lên vẫn là MÃ phòng (vd `PBA017`), đúng thứ backend lưu từ bao-CR-524;
 * backend chặn mã không có / phòng đã ngừng dùng ở cửa lưu. Để trống = phòng mặc định
 * backend tự chọn (câu gợi ý nói rõ là phòng nào).
 *
 * Thiếu quyền đọc danh mục Phòng ban thì rơi về ô chữ: cứ mount là gọi thì người
 * chỉ có quyền cấu hình ăn 403, và ô chọn rỗng trông như «chưa có phòng nào».
 */
export function SettingDepartmentField({ field, disabled, onChange }: SettingDepartmentFieldProps) {
  const inputId = `setting-${field.key}`
  const { can } = usePermission()
  const canReadDepartments = can('department', 'read')
  const { data } = useDepartments({ page_size: 500 }, { enabled: canReadDepartments })
  const value = typeof field.value === 'string' ? field.value : ''

  //  Chỉ phòng đang dùng mới được mời chọn. Mã đang lưu mà không còn trong danh
  //  sách thì `SearchSelect` vẫn hiện nguyên văn — không giấu, kẻo tưởng ô trống.
  const options = useMemo(
    () =>
      (data?.items ?? [])
        .filter((item) => item.is_active)
        .map((item) => ({ value: item.code, label: `${item.name} · ${item.code}` })),
    [data?.items],
  )

  return (
    <div className="flex flex-col gap-1.5 py-2 sm:col-span-2">
      <Label htmlFor={inputId} className="text-[13px]">
        {field.label}
      </Label>
      {canReadDepartments ? (
        <SearchSelect
          id={inputId}
          value={value}
          onChange={(next) => onChange(field.key, next)}
          options={options}
          placeholder="Để trống = phòng mặc định"
          searchPlaceholder="Gõ tên hoặc mã phòng…"
          emptyMessage="Không có phòng nào khớp"
          disabled={disabled}
          clearable
        />
      ) : (
        <Input
          id={inputId}
          value={value}
          disabled={disabled}
          onChange={(event) => onChange(field.key, event.target.value)}
        />
      )}
      {field.hint && <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{field.hint}</p>}
    </div>
  )
}
