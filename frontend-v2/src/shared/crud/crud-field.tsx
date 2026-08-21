import { Controller, type Control, type FieldErrors, type UseFormRegister } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { withCurrentValue } from './field-values'
import type { CrudFormField } from './types'
import { useCrudSourceOptions } from './use-crud'

type FormValues = Record<string, unknown>

interface CrudFieldProps {
  field: CrudFormField
  register: UseFormRegister<FormValues>
  control: Control<FormValues>
  errors: FieldErrors<FormValues>
  /** Chỉ xem: hiện chữ thường thay vì ô nhập (xem `ReadOnlyValue`). */
  isReadonly?: boolean
}

/**
 * Một ô của form CRUD — dùng CHUNG cho hộp thoại thêm mới và trang chi tiết.
 *
 * Trước đây hai màn mỗi màn giữ một bản sao y hệt nhau; thêm kiểu ô mới phải sửa
 * hai chỗ và quên một chỗ là thêm mới với sửa hiện khác nhau.
 */
export function CrudField({ field, register, control, errors, isReadonly }: CrudFieldProps) {
  const isFullWidth = field.fullWidth || field.type === 'textarea'
  const errorMessage = errors[field.name]?.message as string | undefined

  return (
    <div className={cn('space-y-1.5', isFullWidth && 'sm:col-span-2')}>
      <Label htmlFor={field.name} className="flex items-center gap-1">
        {field.label}
        {field.required && !isReadonly && <span className="text-destructive">*</span>}
      </Label>

      {isReadonly ? (
        <CrudFieldReadOnly field={field} control={control} />
      ) : field.type === 'textarea' ? (
        <Textarea
          id={field.name}
          placeholder={field.placeholder}
          rows={3}
          {...register(field.name, {
            required: field.required ? `${field.label} là bắt buộc` : false,
          })}
        />
      ) : field.type === 'switch' ? (
        <Controller
          control={control}
          name={field.name}
          render={({ field: controllerField }) => (
            <div className="flex items-center gap-3 pt-1">
              <Switch
                id={field.name}
                checked={Boolean(controllerField.value)}
                onCheckedChange={controllerField.onChange}
              />
              <span className="text-sm font-normal text-muted-foreground">
                {controllerField.value ? 'Đang dùng / Hoạt động' : 'Ngừng / Ẩn'}
              </span>
            </div>
          )}
        />
      ) : field.type === 'select' ? (
        <CrudSelectField field={field} control={control} />
      ) : field.type === 'date' ? (
        <Controller
          control={control}
          name={field.name}
          rules={{ required: field.required ? `${field.label} là bắt buộc` : false }}
          render={({ field: controllerField }) => (
            <DatePicker
              value={String(controllerField.value ?? '')}
              onChange={controllerField.onChange}
            />
          )}
        />
      ) : (
        <Input
          id={field.name}
          type={field.type === 'number' || field.type === 'percent' ? 'number' : 'text'}
          step={field.type === 'percent' ? '0.1' : undefined}
          placeholder={field.placeholder}
          {...register(field.name, {
            required: field.required ? `${field.label} là bắt buộc` : false,
            // Ràng buộc của backend cho trường tỉ lệ là `ge=0, lt=1` (CR-058), tức
            // 0 <= phần trăm < 100. Chặn ngay tại form cho khỏi ăn 422 sau khi bấm Lưu.
            ...(field.type === 'percent'
              ? {
                  min: { value: 0, message: `${field.label} không được âm` },
                  max: { value: 99.99, message: `${field.label} phải nhỏ hơn 100` },
                }
              : {}),
          })}
        />
      )}

      {field.hint && <p className="text-xs text-muted-foreground">{field.hint}</p>}
      {errorMessage && <p className="text-xs text-destructive">{errorMessage}</p>}
    </div>
  )
}

/**
 * Ô CHỈ XEM.
 *
 * ⚠️ KHÔNG dùng `<Input disabled>` ở đây: `disabled` gỡ luôn khả năng nhận con
 * trỏ nên không bôi đen / không copy được — mã số thuế, số tài khoản ngân hàng
 * của nhà cung cấp là những thứ người dùng chép ra ngoài nhiều nhất (CR-105).
 */
function CrudFieldReadOnly({
  field,
  control,
}: {
  field: CrudFormField
  control: Control<FormValues>
}) {
  const { data: remoteOptions } = useCrudSourceOptions(
    // Ô chọn tĩnh thì khỏi gọi mạng chỉ để dịch một nhãn.
    field.type === 'select' && !field.options ? field.source : undefined,
  )

  return (
    <Controller
      control={control}
      name={field.name}
      render={({ field: controllerField }) => {
        const value = controllerField.value

        if (field.type === 'switch') {
          return (
            <ReadOnlyValue>{value ? 'Đang dùng / Hoạt động' : 'Ngừng / Ẩn'}</ReadOnlyValue>
          )
        }
        if (field.type === 'percent') {
          return <ReadOnlyValue>{`${Number(value ?? 0)}%`}</ReadOnlyValue>
        }
        if (field.type === 'date') {
          return <ReadOnlyValue>{formatDate(String(value ?? ''))}</ReadOnlyValue>
        }
        if (field.type === 'select') {
          const options = field.options ?? remoteOptions ?? []
          const matched = options.find((opt) => String(opt.value) === String(value ?? ''))
          return <ReadOnlyValue>{matched?.label ?? String(value ?? '')}</ReadOnlyValue>
        }

        return (
          <ReadOnlyValue multiline={field.type === 'textarea'}>
            {String(value ?? '')}
          </ReadOnlyValue>
        )
      }}
    />
  )
}

function CrudSelectField({
  field,
  control,
}: {
  field: CrudFormField
  control: Control<FormValues>
}) {
  const { data: remoteOptions, isLoading } = useCrudSourceOptions(field.source)
  const options = field.options ?? remoteOptions ?? []

  return (
    <Controller
      control={control}
      name={field.name}
      rules={{ required: field.required ? `${field.label} là bắt buộc` : false }}
      render={({ field: controllerField }) => (
        <Select
          value={String(controllerField.value ?? '')}
          onValueChange={(val) => {
            // ⚠️ BỎ QUA chuỗi rỗng — KHÔNG phải người dùng chọn.
            //
            // Radix giữ một thẻ `<select>` ẩn để đồng bộ với form, và đồng bộ bằng
            // cách GÁN THẲNG `select.value`. Trình duyệt ép giá trị nào chưa có
            // `<option>` tương ứng NGAY LÚC ĐÓ về chuỗi rỗng rồi bắn `change`, Radix
            // gọi ngược `onValueChange('')` và giá trị thật trong form bị xóa trắng.
            // Trúng đúng hai ca hay gặp: ô nạp options từ API (options về SAU khi
            // `reset` đổ dữ liệu) và giá trị cũ ngoài danh sách khai (mục bù của
            // `withCurrentValue` vào danh sách chậm hơn một nhịp vẽ) — mở hợp đồng
            // HDX0177 thì "Loại hợp đồng" và "Công ty pháp nhân" đều hiện chữ gợi ý
            // như ô trống, bấm Lưu là ghi rỗng đè lên dữ liệu thật.
            // Người dùng không cách nào chọn ra chuỗi rỗng (`SelectItem value=""` là
            // lỗi của Radix), nên gặp '' thì chắc chắn là nhịp đồng bộ này.
            if (val === '') return
            // Options kiểu boolean gửi lên dạng chuỗi, phải dựng lại đúng kiểu.
            if (val === 'true') controllerField.onChange(true)
            else if (val === 'false') controllerField.onChange(false)
            else controllerField.onChange(val)
          }}
          disabled={isLoading}
        >
          <SelectTrigger id={field.name} className="w-full">
            <SelectValue placeholder={field.placeholder || `Chọn ${field.label.toLowerCase()}`} />
          </SelectTrigger>
          <SelectContent>
            {withCurrentValue(options, controllerField.value).map((opt) => (
              <SelectItem key={String(opt.value)} value={String(opt.value)}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    />
  )
}
