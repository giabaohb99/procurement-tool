import { useState } from 'react'
import type { UseFormReturn } from 'react-hook-form'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { LEAVE_SESSION, LEAVE_TYPE } from '@/shared/constants/statuses'
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
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { suggestedDayCount } from '../helpers/so-ngay-nghi-phep'

interface DocumentLeaveFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
}

/**
 * TÁM Ô CỦA GIẤY NGHỈ PHÉP. Chỉ hiện khi loại văn bản đang chọn là `GNP`.
 *
 * Giá trị gom vào `metadata` của văn bản, không đẻ thêm cột — mỗi loại một cụm
 * cột thì bảng phình ra và 90% cột luôn NULL với 90% văn bản.
 *
 * **Bố cục 12 cột, xếp theo CÂU HỎI chứ không theo thứ tự cột trong CSDL:**
 *
 *     ai nghỉ ─────────────┐  nghỉ kiểu gì ──────┐
 *     từ ngày ─┐ buổi ─┐ đến ngày ─┐ buổi ─┐  ← cả khoảng thời gian trên MỘT hàng
 *     mấy ngày ─┐ ai gánh việc ────┐ gọi số nào ─┐
 *     vì sao ──────────────────────────────────┘
 *
 * Bản đầu xếp hai cột đều nhau nên «Số liên lạc» đứng trơ một mình chiếm nửa
 * hàng, còn «Từ ngày» và «Đến ngày» nằm hai hàng khác nhau — mắt phải nhảy qua
 * lại mới ghép được thành một khoảng.
 *
 * Danh sách *loại nghỉ* và *buổi* lấy từ `@/shared/constants/statuses` — tệp
 * SINH TỰ ĐỘNG từ `backend/app/core/leave_codes.py`. Đừng gõ tay danh sách thứ
 * hai ở đây.
 */
export function DocumentLeaveFields({ form }: DocumentLeaveFieldsProps) {
  const { data: employees } = useEmployees({ page_size: 2000 })
  const employee = employees?.items ?? []

  const fromDate = form.watch('leave.from_date')
  const toDate = form.watch('leave.to_date')
  const suggestion = suggestedDayCount(fromDate, toDate, form.watch('leave.from_session'),
                          form.watch('leave.to_session'))

  //  NGHỈ TRONG MỘT NGÀY là ca hay gặp nhất — «chiều thứ Sáu», «sáng mai».
  //
  //  Bắt khai đủ bốn ô (từ ngày · buổi · đến ngày · buổi) cho một buổi nghỉ là
  //  bốn thao tác cho việc nhỏ nhất, và hai ô «Buổi» lúc đó nói về CÙNG một
  //  buổi nên đặt lệch nhau là ra dữ liệu vô nghĩa. Nên: chọn ngày bắt đầu thì
  //  ngày kết thúc bám theo, và khi hai ngày trùng nhau thì gộp còn MỘT ô buổi.
  if (useHasChanged(fromDate) && fromDate && (!toDate || toDate < fromDate)) {
    form.setValue('leave.to_date', fromDate)
  }
  const sameDayLeave = !!fromDate && fromDate === toDate

  //  ĐIỀN SẴN số ngày, không để trống chờ người dùng gõ.
  //
  //  Bỏ trống KHÔNG làm con số biến mất: backend tự tính đúng công thức này rồi
  //  lưu xuống (`type_metadata.lam_sach`). Nên ô rỗng chỉ GIẤU đi một con số có
  //  thể sai — nghỉ thứ Sáu đến thứ Hai ra 4 ngày vì công thức đếm cả cuối tuần
  //  (hệ chưa có bảng lịch làm việc). Điền sẵn thì người lập đơn nhìn thấy ngay
  //  và sửa được; để trống thì họ gửi đi mà không biết mình vừa khai 4 ngày phép.
  const [tuSuaSoNgay, setTuSuaSoNgay] = useState(false)
  if (useHasChanged(suggestion) && !tuSuaSoNgay) {
    form.setValue('leave.total_days', suggestion > 0 ? suggestion : '')
  }

  /** Ô chọn buổi. `gopCaHai` = nghỉ trong một ngày, một ô nói cho cả hai đầu. */
  const oBuoi = (ten: 'leave.from_session' | 'leave.to_session', gopCaHai = false) => (
    <FormField
      control={form.control}
      name={ten}
      render={({ field }) => (
        <FormItem className="md:col-span-2">
          <FormLabel>Buổi</FormLabel>
          <Select
            value={field.value}
            onValueChange={(value) => {
              field.onChange(value)
              //  Giữ hai đầu bằng nhau: backend tính ngày công theo buổi ĐI khi
              //  cùng ngày, nhưng để lệch thì metadata lưu ra một khoảng vô
              //  nghĩa («sáng → chiều» của cùng một ngày).
              if (gopCaHai) form.setValue('leave.to_session', value)
            }}
          >
            <FormControl>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              {LEAVE_SESSION.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormMessage />
        </FormItem>
      )}
    />
  )

  /** Ô chọn nhân sự — người nghỉ và người bàn giao dùng chung khuôn. */
  const employeeField = (
    ten: 'leave.employee_id' | 'leave.handover_employee_id',
    nhan: string,
    nhanRong: string,
  ) => (
    <FormField
      control={form.control}
      name={ten}
      render={({ field }) => (
        <FormItem className="md:col-span-6">
          <FormLabel>{nhan}</FormLabel>
          <Select
            value={String(field.value || 0)}
            onValueChange={(value) => field.onChange(Number(value))}
          >
            <FormControl>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
            </FormControl>
            <SelectContent>
              <SelectItem value="0">{nhanRong}</SelectItem>
              {employee.map((item) => (
                <SelectItem key={item.id} value={String(item.id)}>
                  {item.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FormMessage />
        </FormItem>
      )}
    />
  )

  return (
    // `items-start`: ô nào có dòng chú thích thì cao hơn, không có nó là cả hàng
    // bị kéo giãn theo ô cao nhất và nhãn lệch nhau.
    <div className="grid items-start gap-x-4 gap-y-3 md:grid-cols-12">
      {/* ── Hàng 1: ai nghỉ, nghỉ kiểu gì ─────────────────────────────── */}
      {employeeField('leave.employee_id', 'Người nghỉ', '— Theo người chịu trách nhiệm —')}

      <FormField
        control={form.control}
        name="leave.leave_type"
        render={({ field }) => (
          <FormItem className="md:col-span-6">
            <FormLabel>Loại nghỉ</FormLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {LEAVE_TYPE.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* ── Hàng 2: cả khoảng thời gian trên MỘT hàng ──────────────────── */}
      <FormField
        control={form.control}
        name="leave.from_date"
        render={({ field }) => (
          <FormItem className={sameDayLeave ? 'md:col-span-5' : 'md:col-span-4'}>
            <FormLabel>
              Từ ngày
              <RequiredMark />
            </FormLabel>
            <FormControl>
              {/*  `DatePicker` chứ không phải `<input type="date">`: ô nguyên bản
                   hiện theo locale của MÁY, nên máy đặt tiếng Anh ra
                   «mm/dd/yyyy» — lệch hẳn với các ô ngày khác của chính form
                   này (Ngày hiệu lực, Ngày hết hiệu lực). */}
              <DatePicker value={field.value ?? ''} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      {!sameDayLeave && oBuoi('leave.from_session')}

      <FormField
        control={form.control}
        name="leave.to_date"
        render={({ field }) => (
          <FormItem className={sameDayLeave ? 'md:col-span-5' : 'md:col-span-4'}>
            <FormLabel>
              Đến ngày
              <RequiredMark />
            </FormLabel>
            <FormControl>
              <DatePicker value={field.value ?? ''} onChange={field.onChange} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      {/*  Cùng ngày → MỘT ô buổi, gắn vào đầu ĐI và tự đồng bộ đầu VỀ. */}
      {sameDayLeave ? oBuoi('leave.from_session', true) : oBuoi('leave.to_session')}

      {/* ── Hàng 3: mấy ngày · ai gánh việc · gọi số nào ───────────────── */}
      <FormField
        control={form.control}
        name="leave.total_days"
        render={({ field }) => (
          <FormItem className="md:col-span-3">
            <FormLabel>Tổng số ngày</FormLabel>
            <FormControl>
              <Input
                type="number"
                step="0.5"
                min="0"
                {...field}
                onChange={(event) => {
                  //  Người dùng đã tự gõ thì thôi đừng ghi đè nữa — đổi ngày sau
                  //  đó không được xóa con số họ vừa chỉnh.
                  setTuSuaSoNgay(true)
                  field.onChange(event)
                }}
              />
            </FormControl>
            <FormDescription>Đếm cả cuối tuần — sửa lại nếu cần</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {employeeField('leave.handover_employee_id', 'Người bàn giao công việc', '— Không bàn giao —')}

      <FormField
        control={form.control}
        name="leave.contact_phone"
        render={({ field }) => (
          <FormItem className="md:col-span-3">
            <FormLabel>Số liên lạc khi nghỉ</FormLabel>
            <FormControl>
              <Input placeholder="Số gọi được khi nghỉ" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* ── Hàng 4: vì sao ─────────────────────────────────────────────── */}
      <FormField
        control={form.control}
        name="leave.reason"
        render={({ field }) => (
          <FormItem className="md:col-span-12">
            <FormLabel>
              Lý do nghỉ
              <RequiredMark />
            </FormLabel>
            <FormControl>
              <Textarea rows={2} placeholder="Nêu rõ lý do để người duyệt quyết được" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
