import { Lock } from 'lucide-react'
import { useFormContext, type FieldPath } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import type { EmployeeProfileFormValues } from '../schemas/employee-schema'
import type { CodeOption } from '../types/employee-codes'

/**
 * Ô nhập của FORM HỒ SƠ NHÂN SỰ — bốn kiểu, khai một chỗ.
 *
 * Hồ sơ có hơn 30 ô; chép `<FormField render={...}>` từng ô thì mỗi tab dài
 * 400 dòng và sửa một chi tiết hiển thị phải sửa ba chỗ. Bốn helper dưới đây
 * đọc form qua `useFormContext`, nên nơi gọi chỉ cần nằm trong `<Form>`.
 */

type ProfileFieldName = FieldPath<EmployeeProfileFormValues>

interface BaseFieldProps {
  name: ProfileFieldName
  label: string
  description?: string
  disabled?: boolean
}

export function EmployeeTextField({
  name,
  label,
  description,
  disabled,
  placeholder,
  type = 'text',
}: BaseFieldProps & { placeholder?: string; type?: 'text' | 'email' | 'tel' }) {
  const form = useFormContext<EmployeeProfileFormValues>()

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Input
              type={type}
              placeholder={placeholder}
              disabled={disabled}
              {...field}
              value={(field.value as string | number | null) ?? ''}
            />
          </FormControl>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

/** Ô SỐ nguyên. Chuỗi rỗng đọc thành `0`, không để `NaN` lọt vào form. */
export function EmployeeNumberField({ name, label, description, disabled }: BaseFieldProps) {
  const form = useFormContext<EmployeeProfileFormValues>()

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Input
              type="number"
              min={0}
              disabled={disabled}
              value={String((field.value as number) ?? 0)}
              onChange={(e) => field.onChange(Number(e.target.value) || 0)}
              onBlur={field.onBlur}
              name={field.name}
              ref={field.ref}
            />
          </FormControl>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

export function EmployeeDateField({ name, label, description, disabled }: BaseFieldProps) {
  const form = useFormContext<EmployeeProfileFormValues>()

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          {/*  Cột ngày là `DATE NULL` nên API trả `null` cho ô chưa khai; ô ngày
               nhận `null` là mở hồ sơ ra đã đỏ lỗi, chưa gõ gì. */}
          <DatePicker
            value={(field.value as string | null) ?? ''}
            onChange={field.onChange}
            disabled={disabled}
          />
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

/**
 * Ô CHỌN mã số. Mục `0` (chưa khai) hiện thành `placeholder`, không thành một
 * dòng chữ "Chưa khai" — Radix cấm option value rỗng nên vẫn phải có mục `0`
 * trong danh sách, chỉ là gắn nhãn cho nó.
 */
export function EmployeeCodeSelect({
  name,
  label,
  description,
  disabled,
  options,
  unknownLabel = '— Chưa khai —',
}: BaseFieldProps & { options: readonly CodeOption[]; unknownLabel?: string }) {
  const form = useFormContext<EmployeeProfileFormValues>()

  return (
    <FormField
      control={form.control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <Select
            value={String((field.value as number) ?? 0)}
            onValueChange={(v) => field.onChange(Number(v))}
            disabled={disabled}
          >
            <FormControl>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {options.map((item) => (
                <SelectItem key={item.value} value={String(item.value)}>
                  {item.value === 0 ? unknownLabel : item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {description && <FormDescription>{description}</FormDescription>}
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

/**
 * Dải cảnh báo đặt ĐẦU tab chứa trường nhạy cảm, khi người xem không có quyền.
 *
 * ⚠️ Bắt buộc phải nói ra. Backend che bằng cách trả **chuỗi rỗng** — nhìn giống
 * hệt ô chưa ai nhập. Không có dòng này thì người dùng đọc hồ sơ ra và tin rằng
 * công ty chưa có số tài khoản ngân hàng của người đó.
 */
export function SensitiveFieldsNotice() {
  return (
    <div className="flex items-start gap-2 rounded-md border border-dashed bg-muted/40 p-3 text-sm text-muted-foreground">
      <Lock className="mt-0.5 size-4 shrink-0" />
      <span>
        Một số ô đang ẩn với bạn: CCCD, tài khoản ngân hàng, địa chỉ nhà, ngày sinh, mã
        số thuế và số BHXH. Chúng hiện <strong>trống</strong> dù hồ sơ có thể đã có dữ
        liệu, và bấm Lưu cũng <strong>không làm mất</strong> phần đó.
      </span>
    </div>
  )
}
