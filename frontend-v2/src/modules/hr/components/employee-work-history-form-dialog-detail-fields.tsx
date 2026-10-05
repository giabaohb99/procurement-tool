import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import type { EmployeeWorkHistoryFormValues } from '../schemas/employee-work-history-schema'
import { LookupSelect, type LookupItem } from './lookup-select'

interface EmployeeWorkHistoryDetailFieldsProps {
  form: UseFormReturn<EmployeeWorkHistoryFormValues>
  companies: LookupItem[]
  departments: LookupItem[]
  positions: LookupItem[]
  /** Nút «+ Thêm quyết định» (mục 3, 03/10/2026) — Số QĐ bắt buộc, thêm dấu `*`. */
  requireDecisionNo?: boolean
}

/**
 * Phần "chi tiết" của hộp thêm/sửa «Quá trình công tác» — Pháp nhân / Phòng
 * ban / Chức vụ, Số QĐ / Ngày ký QĐ, Ghi chú. Tách khỏi
 * `employee-work-history-form-dialog-fields.tsx` để tệp đó giữ dưới ~200 dòng
 * (CLAUDE.md §"File Size Management"). Thuần trình bày.
 */
export function EmployeeWorkHistoryDetailFields({
  form,
  companies,
  departments,
  positions,
  requireDecisionNo = false,
}: EmployeeWorkHistoryDetailFieldsProps) {
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          control={form.control}
          name="company_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Pháp nhân</FormLabel>
              <LookupSelect
                value={field.value}
                onChange={field.onChange}
                items={companies}
                placeholder="Chọn pháp nhân"
                emptyLabel="— Chưa chọn —"
              />
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="department_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Phòng ban</FormLabel>
              <LookupSelect
                value={field.value}
                onChange={field.onChange}
                items={departments}
                placeholder="Chọn phòng ban"
                emptyLabel="— Chưa chọn —"
              />
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="position_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Chức vụ</FormLabel>
              <LookupSelect
                value={field.value}
                onChange={field.onChange}
                items={positions}
                placeholder="Chọn chức vụ"
                emptyLabel="— Chưa chọn —"
              />
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          control={form.control}
          name="decision_no"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{requireDecisionNo ? 'Số QĐ *' : 'Số QĐ'}</FormLabel>
              <FormControl>
                <Input {...field} maxLength={50} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="decision_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Ngày ký QĐ</FormLabel>
              <DatePicker value={field.value} onChange={field.onChange} />
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={form.control}
        name="note"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Ghi chú</FormLabel>
            <FormControl>
              <Textarea {...field} maxLength={500} rows={2} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
