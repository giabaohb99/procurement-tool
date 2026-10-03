import type { UseFormReturn } from 'react-hook-form'

import { labelOf, WORK_EVENT_TYPE } from '@/shared/constants/statuses'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import type { EmployeeWorkHistoryFormValues } from '../schemas/employee-work-history-schema'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { RESIGN_TYPE } from '../utils/employee-work-history-apply'
import { EmployeeWorkHistoryDetailFields } from './employee-work-history-form-dialog-detail-fields'
import { EmployeeWorkHistoryFileField } from './employee-work-history-form-dialog-file-field'
import type { LookupItem } from './lookup-select'

interface EmployeeWorkHistoryFormDialogFieldsProps {
  form: UseFormReturn<EmployeeWorkHistoryFormValues>
  onSubmit: (values: EmployeeWorkHistoryFormValues) => void
  companies: LookupItem[]
  departments: LookupItem[]
  positions: LookupItem[]
  /** Dòng chính đang mở, sớm hơn dòng mới — hiện tick «Đóng dòng». `null` = ẩn ô tick. */
  openMainRow: EmployeeWorkHistory | null
  eventType: number
  fromDate: string
  today: string
  /** Đang SỬA (`true`) hay tạo mới (`false`) — quyết định ô Tệp QĐ hiện dạng nào. */
  editingRow: EmployeeWorkHistory | null
  /** A9 (Q4) — `false` thì ẨN cả vùng thả tệp lẫn nút «Quản lý tệp» (M4). */
  canOpenFiles: boolean
  queuedFileCount: number
  onQueueFiles: (files: File[]) => void
  onOpenFilesDialog: () => void
  footer: React.ReactNode
}

/**
 * Toàn bộ Ô NHẬP của hộp thêm/sửa — tách khỏi `employee-work-history-form-dialog.tsx`
 * (điều phối state/mutation) để mỗi tệp giữ dưới ~200 dòng (CLAUDE.md §"File Size
 * Management"). Pháp nhân/Phòng ban/Chức vụ + Số QĐ/Ngày ký QĐ/Ghi chú và ô Tệp
 * QĐ tách tiếp sang `-detail-fields.tsx` / `-file-field.tsx` cùng lý do. Thuần
 * trình bày, không tự gọi API/mutation nào.
 */
export function EmployeeWorkHistoryFormDialogFields({
  form,
  onSubmit,
  companies,
  departments,
  positions,
  openMainRow,
  eventType,
  fromDate,
  today,
  editingRow,
  canOpenFiles,
  queuedFileCount,
  onQueueFiles,
  onOpenFilesDialog,
  footer,
}: EmployeeWorkHistoryFormDialogFieldsProps) {
  return (
    <Form {...form}>
      <form
        onSubmit={(event) => {
          //  ⚠️ BẪY 1 — xem docstring của `employee-work-history-form-dialog.tsx`.
          event.stopPropagation()
          void form.handleSubmit(onSubmit)(event)
        }}
        className="space-y-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="event_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Loại *</FormLabel>
                <Select value={field.value ? String(field.value) : ''} onValueChange={(v) => field.onChange(Number(v))}>
                  <FormControl>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Chọn loại" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {WORK_EVENT_TYPE.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="from_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Từ ngày (hiệu lực) *</FormLabel>
                <DatePicker value={field.value} onChange={field.onChange} clearable={false} />
                {eventType === RESIGN_TYPE && fromDate > today && (
                  <p className="text-xs text-muted-foreground">
                    Tới ngày này quay lại bấm «Áp vào hồ sơ» để chuyển nghỉ việc.
                  </p>
                )}
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="to_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Đến ngày</FormLabel>
                <DatePicker value={field.value} onChange={field.onChange} />
                <FormMessage />
              </FormItem>
            )}
          />
          {openMainRow && (
            <FormField
              control={form.control}
              name="close_open_main"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-2 space-y-0 pt-7">
                  <FormControl>
                    <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                  <FormLabel className="font-normal">
                    Đóng dòng đang hiệu lực «{labelOf(WORK_EVENT_TYPE, String(openMainRow.event_type))}»
                    vào ngày trước đó
                  </FormLabel>
                </FormItem>
              )}
            />
          )}
        </div>

        <EmployeeWorkHistoryDetailFields
          form={form}
          companies={companies}
          departments={departments}
          positions={positions}
        />

        <EmployeeWorkHistoryFileField
          editingRow={editingRow}
          canOpenFiles={canOpenFiles}
          queuedFileCount={queuedFileCount}
          onQueueFiles={onQueueFiles}
          onOpenFilesDialog={onOpenFilesDialog}
        />

        {footer}
      </form>
    </Form>
  )
}
