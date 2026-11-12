import type { UseFormReturn } from 'react-hook-form'

import { DatePicker } from '@/shared/ui/date-picker'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import type { EmployeeConcurrentFormValues } from '../schemas/employee-concurrent-schema'
import { LookupSelect, type LookupItem } from './lookup-select'

interface EmployeeConcurrentFormFieldsProps {
  form: UseFormReturn<EmployeeConcurrentFormValues>
  companies: LookupItem[]
  /** Đã lọc theo công ty đang chọn (`buildConcurrentDepartmentOptions`). */
  departments: LookupItem[]
  positions: LookupItem[]
  /** Nhãn dự phòng khi giá trị đang lưu không còn trong danh mục (sửa dòng cũ). */
  fallback?: { company?: string; department?: string; position?: string }
  /** Đổi công ty — nơi gọi dọn ô phòng nếu phòng không phục vụ công ty mới. */
  onCompanyChange: (companyId: number) => void
}

/** Ô nhập của hộp kiêm nhiệm — thuần trình bày, không gọi API. */
export function EmployeeConcurrentFormFields({
  form,
  companies,
  departments,
  positions,
  fallback,
  onCompanyChange,
}: EmployeeConcurrentFormFieldsProps) {
  const companyId = form.watch('company_id')

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        <FormField
          control={form.control}
          name="company_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Công ty <RequiredMark hint="Bắt buộc" /></FormLabel>
              <LookupSelect
                value={field.value}
                onChange={onCompanyChange}
                items={companies}
                placeholder="Chọn công ty"
                fallbackLabel={fallback?.company}
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
              <FormLabel>Phòng ban <RequiredMark hint="Bắt buộc" /></FormLabel>
              <LookupSelect
                value={field.value}
                onChange={field.onChange}
                items={departments}
                placeholder={companyId ? 'Chọn phòng ban' : 'Chọn công ty trước'}
                fallbackLabel={fallback?.department}
                disabled={!companyId}
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
                fallbackLabel={fallback?.position}
              />
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          control={form.control}
          name="from_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Từ ngày <RequiredMark hint="Bắt buộc" /></FormLabel>
              <DatePicker value={field.value} onChange={field.onChange} clearable={false} />
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="to_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Đến ngày</FormLabel>
              <DatePicker value={field.value} onChange={field.onChange} placeholder="Chưa kết thúc" />
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
              <FormLabel>Số QĐ</FormLabel>
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
              <FormLabel>Ngày QĐ</FormLabel>
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

      <FormField
        control={form.control}
        name="counts_scope"
        render={({ field }) => (
          <FormItem className="flex flex-row items-start gap-3 rounded-md border p-3">
            <FormControl>
              <Switch checked={field.value} onCheckedChange={field.onChange} className="mt-0.5" />
            </FormControl>
            <div className="space-y-1">
              <FormLabel className="font-medium">Tính vào phạm vi quyền</FormLabel>
              <p className="text-xs text-muted-foreground">
                Bật: người này thấy dữ liệu đúng phòng này ở công ty này theo vai trò đang có, trong thời gian dòng còn
                hiệu lực. Tắt: chỉ ghi nhận kiêm nhiệm, không mở thêm dữ liệu.
              </p>
            </div>
          </FormItem>
        )}
      />
    </>
  )
}
