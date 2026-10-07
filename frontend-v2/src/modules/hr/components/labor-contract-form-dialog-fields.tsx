import type { ReactNode } from 'react'
import type { UseFormReturn } from 'react-hook-form'

import { LABOR_CONTRACT_TYPE } from '@/shared/constants/statuses'
import { DatePicker } from '@/shared/ui/date-picker'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { NumberInput } from '@/shared/ui/number-input'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import type { LaborContractFormValues } from '../schemas/labor-contract-schema'
import { endDateRule } from '../utils/labor-contract-rules'
import { LaborContractTermPresets } from './labor-contract-term-presets'

interface LaborContractFormDialogFieldsProps {
  form: UseFormReturn<LaborContractFormValues>
  onSubmit: (values: LaborContractFormValues) => void
  /** Pháp nhân của hợp đồng — CHỈ ĐỌC (snapshot lúc lập, không đổi được). */
  companyName: string
  /** Câu báo «chưa có mẫu» / gợi ý mẫu, nằm dưới ô Loại. */
  templateHint: ReactNode
  footer: ReactNode
}

/**
 * Ô nhập của hộp lập/sửa hợp đồng. Thuần trình bày.
 *
 * ⚠️ BẪY 1+4: hộp nằm TRONG `<form>` của trang hồ sơ nên `stopPropagation` ở `onSubmit`
 * — không thì bấm Lưu (hay Enter) ở đây lưu đè luôn hồ sơ nhân sự.
 */
export function LaborContractFormDialogFields({
  form,
  onSubmit,
  companyName,
  templateHint,
  footer,
}: LaborContractFormDialogFieldsProps) {
  const contractType = form.watch('contract_type')
  const rule = endDateRule(contractType)
  return (
    <Form {...form}>
      <form
        onSubmit={(event) => {
          event.stopPropagation()
          void form.handleSubmit(onSubmit)(event)
        }}
        className="space-y-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <FormItem>
            <FormLabel>Pháp nhân</FormLabel>
            <ReadOnlyValue>{companyName || '—'}</ReadOnlyValue>
          </FormItem>
          <FormField control={form.control} name="contract_type" render={({ field }) => (
            <FormItem>
              <FormLabel>Loại hợp đồng *</FormLabel>
              <Select value={field.value ? String(field.value) : ''}
                onValueChange={(v) => {
                  const next = Number(v)
                  field.onChange(next)
                  //  Đổi sang loại cấm ngày kết thúc thì xóa luôn ngày cũ, kẻo gửi đi ăn 422.
                  if (endDateRule(next) === 'forbidden') form.setValue('end_date', '')
                }}>
                <FormControl>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Chọn loại" /></SelectTrigger>
                </FormControl>
                <SelectContent>
                  {LABOR_CONTRACT_TYPE.map((o) => (
                    <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )} />
        </div>
        {templateHint}

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField control={form.control} name="contract_no" render={({ field }) => (
            <FormItem>
              <FormLabel>Số hợp đồng</FormLabel>
              <FormControl><Input {...field} placeholder="Để trống = lấy mã hệ thống" maxLength={50} /></FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="start_date" render={({ field }) => (
            <FormItem>
              <FormLabel>Ngày bắt đầu *</FormLabel>
              <DatePicker value={field.value} onChange={field.onChange} clearable={false} />
              <FormMessage />
            </FormItem>
          )} />
        </div>

        {rule !== 'forbidden' && (
          <FormField control={form.control} name="end_date" render={({ field }) => (
            <FormItem>
              <FormLabel>Ngày kết thúc{rule === 'required' ? ' *' : ''}</FormLabel>
              <DatePicker value={field.value} onChange={field.onChange} clearable={rule !== 'required'} />
              <LaborContractTermPresets
                contractType={contractType}
                startDate={form.watch('start_date')}
                endDate={field.value}
                //  `shouldValidate`: đang đỏ «Chọn ngày kết thúc» thì bấm nút phải xóa lỗi ngay.
                onPick={(value) => form.setValue('end_date', value, { shouldValidate: true, shouldDirty: true })}
              />
              <FormMessage />
            </FormItem>
          )} />
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField control={form.control} name="job_title" render={({ field }) => (
            <FormItem>
              <FormLabel>Chức danh</FormLabel>
              <FormControl><Input {...field} maxLength={100} /></FormControl>
              <FormMessage />
            </FormItem>
          )} />
          <FormField control={form.control} name="work_location" render={({ field }) => (
            <FormItem>
              <FormLabel>Địa điểm làm việc</FormLabel>
              <FormControl><Input {...field} maxLength={255} /></FormControl>
              <FormMessage />
            </FormItem>
          )} />
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {(['base_salary', 'insurance_salary', 'allowance'] as const).map((name) => (
            <FormField key={name} control={form.control} name={name} render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {name === 'base_salary' ? 'Lương cơ bản (đ)' : name === 'insurance_salary' ? 'Lương đóng BH (đ)' : 'Phụ cấp (đ)'}
                </FormLabel>
                <FormControl>
                  <NumberInput decimals={false} value={field.value} onChange={field.onChange} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )} />
          ))}
        </div>
        <FormField control={form.control} name="allowance_note" render={({ field }) => (
          <FormItem>
            <FormLabel>Ghi chú phụ cấp</FormLabel>
            <FormControl><Input {...field} maxLength={500} placeholder="Vd: ăn trưa, xăng xe, điện thoại" /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        <FormField control={form.control} name="note" render={({ field }) => (
          <FormItem>
            <FormLabel>Ghi chú</FormLabel>
            <FormControl><Textarea {...field} rows={2} maxLength={500} /></FormControl>
            <FormMessage />
          </FormItem>
        )} />
        {footer}
      </form>
    </Form>
  )
}
