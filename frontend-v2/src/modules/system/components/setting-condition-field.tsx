import { ConditionBuilder } from '@/shared/condition-builder/condition-builder'
import { Label } from '@/shared/ui/label'

import { PR_DISPATCH_CONDITION_FIELDS } from '../config/pr-dispatch-condition-fields'
import { usePrDispatchConditionChoices } from '../hooks/use-pr-dispatch-condition-choices'
import { useSettings } from '../hooks/use-settings'
import type { SettingField } from '../types/setting'

interface SettingConditionFieldProps {
  field: SettingField
  disabled: boolean
  onChange: (key: string, value: unknown) => void
}

/**
 * Ô cấu hình kiểu `condition` — BỘ CHỌN ĐIỀU KIỆN thay cho ô gõ JSON (bao-CR-528).
 *
 * Ô «Điều kiện bỏ qua điều phối» của YCMH (bao-CR-497) từng là ô chữ bắt quản
 * trị gõ `[{"field":"handler_dept_id","op":"not_empty"}]`; đại ca chê «cấu hình
 * là gõ code vào à». Giá trị gửi lên vẫn là đúng chuỗi JSON đó — backend kiểm ở
 * cửa lưu và trả câu lỗi tiếng Việt nếu hỏng.
 */
export function SettingConditionField({ field, disabled, onChange }: SettingConditionFieldProps) {
  //  Mã phòng thu mua mặc định lấy từ bản ĐÃ LƯU (cùng truy vấn của trang, đã
  //  nằm sẵn trong đệm): phòng đó bị gỡ khỏi ô «Phòng xử lý».
  const { data } = useSettings()
  const centralCode = data?.fields.find((item) => item.key === 'central_purchasing_dept_code')?.value
  const getOptions = usePrDispatchConditionChoices(
    typeof centralCode === 'string' ? centralCode : '',
  )
  const value = typeof field.value === 'string' ? field.value : ''

  return (
    <div className="flex flex-col gap-1.5 py-2 sm:col-span-2">
      <Label className="text-[13px]">{field.label}</Label>
      <ConditionBuilder
        value={value}
        onChange={(condition) => onChange(field.key, condition)}
        fields={PR_DISPATCH_CONDITION_FIELDS}
        getOptions={getOptions}
        disabled={disabled}
        emptyText={
          <>
            Chưa đặt điều kiện — <b>không phiếu nào</b> được bỏ qua bước thu mua duyệt lần 2.
          </>
        }
        sentencePrefix="Bỏ qua bước thu mua duyệt lần 2 khi: "
        advancedText={
          <>
            Ô này đang giữ điều kiện <b>khai tay</b> từ trước, bộ chọn không diễn tả được. Hệ
            thống vẫn đọc nó như cũ; muốn sửa thì bỏ đi rồi chọn lại.
          </>
        }
      />
      {field.hint && (
        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{field.hint}</p>
      )}
    </div>
  )
}
