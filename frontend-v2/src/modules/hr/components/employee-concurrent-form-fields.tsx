import type { ReactNode } from 'react'
import type { UseFormReturn } from 'react-hook-form'

import { CONCURRENT_KIND } from '@/shared/constants/statuses'
import { DatePicker } from '@/shared/ui/date-picker'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { HelpHint } from '@/shared/ui/help-hint'
import { Input } from '@/shared/ui/input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'
import { cn } from '@/shared/utils/cn'
import type { EmployeeConcurrentFormValues } from '../schemas/employee-concurrent-schema'
import { CONCURRENT_KIND_COMPANY } from '../types/employee-concurrent'
import { LookupSelect, type LookupItem } from './lookup-select'

interface EmployeeConcurrentFormFieldsProps {
  form: UseFormReturn<EmployeeConcurrentFormValues>
  /** Sửa dòng có sẵn: Loại chỉ đọc (backend không cho đổi loại — đổi = xóa rồi thêm). */
  kindLocked: boolean
  /** Tên công ty HIỆN TẠI của hồ sơ — dòng loại Phòng ban luôn ở công ty này (máy chủ điền, không có ô chọn). */
  primaryCompanyName: string
  /** Đã TRỪ công ty hiện tại (`buildConcurrentCompanyOptions`). */
  companies: LookupItem[]
  /** Phòng phục vụ công ty hiện tại (`buildConcurrentDepartmentOptions`). */
  departments: LookupItem[]
  positions: LookupItem[]
  /** Nhãn dự phòng khi giá trị đang lưu không còn trong danh mục (sửa dòng cũ). */
  fallback?: { company?: string; department?: string; position?: string }
  /** Đổi loại — nơi gọi dọn ô nơi kiêm nhiệm của loại kia. */
  onKindChange: (kind: number) => void
  /** Ô Tệp QĐ (`EmployeeConcurrentFileField`), đặt ngay dưới Số QĐ / Ngày QĐ. */
  fileField?: ReactNode
}

const SCOPE_DETAIL_DEPARTMENT =
  'Bật: người này thấy thêm dữ liệu của phòng này theo vai trò đang có, trong thời gian dòng còn hiệu lực. ' +
  'Tắt: chỉ ghi nhận kiêm nhiệm, không mở thêm dữ liệu.'
const SCOPE_DETAIL_COMPANY =
  'Bật: người này được tính như người của công ty này theo bậc vai trò đang có (bậc Công ty thấy cả công ty; bậc ' +
  'Phòng ban thấy phòng của họ ở công ty này), trong thời gian dòng còn hiệu lực. Tắt: chỉ ghi nhận kiêm nhiệm, ' +
  'không mở thêm dữ liệu.'

/**
 * Ô nhập của hộp kiêm nhiệm — thuần trình bày, không gọi API. Bố cục người chủ chốt 13/11/2026 (lượt 2): KHÔNG tiêu đề
 * nhóm (form ngắn, tiêu đề chỉ lặp lại nhãn ô), phân nhịp bằng khoảng cách; thanh Loại đứng đầu; mọi hàng hai ô chia ĐỀU
 * 1:1, điện thoại một cột; giải thích dài của công tắc thu vào (i). Sửa dòng thì thanh Loại tắt (backend không cho đổi
 * loại — đổi = xóa rồi thêm).
 */
export function EmployeeConcurrentFormFields({
  form,
  kindLocked,
  primaryCompanyName,
  companies,
  departments,
  positions,
  fallback,
  onKindChange,
  fileField,
}: EmployeeConcurrentFormFieldsProps) {
  const kind = form.watch('kind')
  const isCompany = kind === CONCURRENT_KIND_COMPANY

  return (
    <div className="grid items-start gap-x-4 gap-y-4 sm:grid-cols-2 [&_[data-slot=form-item]]:gap-1.5">
      <FormField
        control={form.control}
        name="kind"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <ToggleGroup
              type="single"
              variant="outline"
              value={String(field.value)}
              //  Bấm lại lựa chọn đang bật thì Radix trả chuỗi rỗng (bỏ chọn) — Loại bắt buộc nên bỏ qua.
              onValueChange={(next) => next && onKindChange(Number(next))}
              disabled={kindLocked}
              aria-label="Loại kiêm nhiệm"
              title={kindLocked ? 'Không đổi được loại của dòng đã lưu — xóa dòng rồi thêm lại' : undefined}
              className="w-full sm:w-1/2"
            >
              {CONCURRENT_KIND.map((option) => (
                <ToggleGroupItem
                  key={option.value}
                  value={option.value}
                  //  Khóa khi sửa: lựa chọn đang giữ vẫn rõ nét (mặc định `disabled` làm mờ cả hai, khó biết đang là loại nào).
                  className={cn('flex-1', kindLocked && 'data-[state=on]:font-semibold data-[state=on]:disabled:opacity-100')}
                >
                  {option.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
            <FormMessage />
          </FormItem>
        )}
      />

      {isCompany ? (
        <FormField
          control={form.control}
          name="company_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Công ty kiêm nhiệm <RequiredMark hint="Bắt buộc" /></FormLabel>
              <LookupSelect
                value={field.value}
                onChange={field.onChange}
                items={companies}
                placeholder="Chọn công ty"
                fallbackLabel={fallback?.company}
              />
              <FormMessage />
            </FormItem>
          )}
        />
      ) : (
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
                //  Ô chỉ liệt kê phòng của công ty hiện tại — nói luôn trong chữ gợi ý, khỏi thêm một dòng phụ.
                placeholder={primaryCompanyName ? `Chọn phòng của ${primaryCompanyName}` : 'Chọn phòng ban'}
                fallbackLabel={fallback?.department}
              />
              <FormMessage />
            </FormItem>
          )}
        />
      )}
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
      {fileField}

      <FormField
        control={form.control}
        name="counts_scope"
        render={({ field }) => (
          <FormItem className="flex flex-row items-center gap-3 sm:col-span-2">
            <FormControl>
              <Switch checked={field.value} onCheckedChange={field.onChange} />
            </FormControl>
            <FormLabel className="font-medium">Tính vào phạm vi quyền</FormLabel>
            <HelpHint label="Giải thích công tắc phạm vi quyền">
              {isCompany ? SCOPE_DETAIL_COMPANY : SCOPE_DETAIL_DEPARTMENT}
            </HelpHint>
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="note"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Ghi chú</FormLabel>
            <FormControl>
              <Textarea {...field} maxLength={500} rows={2} className="min-h-0" />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
