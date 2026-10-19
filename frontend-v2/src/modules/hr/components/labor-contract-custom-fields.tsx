// duoc-CR-630 — khối «Thông tin bổ sung cho mẫu» trong hộp Lập / Sửa hợp đồng: mỗi biến TÙY CHỈNH đang
// dùng một ô nhập theo kiểu. Biến đã ngừng dùng mà hợp đồng còn giữ giá trị thì hiện CHỈ ĐỌC (vẫn in vào
// mẫu cũ). Không có biến nào → không vẽ khối. Bắt buộc chỉ chặn ở bước Sinh tệp / Đã ký (backend), KHÔNG
// chặn lưu nháp.
import type { UseFormReturn } from 'react-hook-form'

import { FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import type { LaborContractFormValues } from '../schemas/labor-contract-schema'
import type { LaborContractInputField } from '../types/labor-contract-variable'
import { formatVariableValue } from '../utils/labor-contract-variable-value'
import { LaborContractVariableValueInput } from './labor-contract-variable-value-input'

interface CustomFieldsProps {
  form: UseFormReturn<LaborContractFormValues>
  /** Mọi biến tùy chỉnh (đang dùng + ngừng dùng) từ `/input-fields?include_inactive=true`. */
  fields: readonly LaborContractInputField[] | undefined
}

export function LaborContractCustomFields({ form, fields }: CustomFieldsProps) {
  const stored = form.watch('custom_values') ?? {}
  const active = (fields ?? []).filter((f) => f.is_active)
  const frozen = (fields ?? []).filter((f) => !f.is_active && stored[f.code])
  if (active.length === 0 && frozen.length === 0) return null

  return (
    <section className="space-y-4 rounded-md border p-3" aria-label="Thông tin bổ sung cho mẫu">
      <h3 className="text-sm font-semibold">Thông tin bổ sung cho mẫu</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        {active.map((f) => (
          <FormField
            key={f.code}
            control={form.control}
            name={`custom_values.${f.code}`}
            render={({ field }) => (
              <FormItem className={f.value_type === 2 ? 'sm:col-span-2' : undefined}>
                <FormLabel>
                  {f.label}
                  {f.is_required && (
                    <>
                      {' '}
                      <RequiredMark hint="Bắt buộc khi sinh tệp và khi chuyển sang Đã ký" />
                    </>
                  )}
                </FormLabel>
                <FormControl>
                  <LaborContractVariableValueInput
                    valueType={f.value_type}
                    value={field.value ?? ''}
                    onChange={field.onChange}
                    aria-label={f.label}
                  />
                </FormControl>
                {f.is_required && (
                  <FormDescription>Bắt buộc khi sinh tệp (lưu nháp vẫn để trống được).</FormDescription>
                )}
                {f.description && <FormDescription>{f.description}</FormDescription>}
                <FormMessage />
              </FormItem>
            )}
          />
        ))}
        {frozen.map((f) => (
          <div key={f.code} className="space-y-2">
            <p className="text-sm font-medium leading-none">{f.label}</p>
            <ReadOnlyValue multiline={f.value_type === 2}>{formatVariableValue(f.value_type, stored[f.code] ?? '')}</ReadOnlyValue>
            <p className="text-[0.8rem] text-muted-foreground">Biến đã ngừng dùng — vẫn được in vào mẫu cũ, không sửa được.</p>
          </div>
        ))}
      </div>
    </section>
  )
}
