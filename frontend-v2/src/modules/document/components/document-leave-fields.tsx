import type { UseFormReturn } from 'react-hook-form'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { LEAVE_SESSION, LEAVE_TYPE } from '@/shared/constants/statuses'
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
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'
import { soNgayGoiY } from '../helpers/so-ngay-nghi-phep'

interface DocumentLeaveFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
}

/**
 * TÁM Ô CỦA GIẤY NGHỈ PHÉP. Chỉ hiện khi loại văn bản đang chọn là `GNP`.
 *
 * Giá trị gom vào `metadata` của văn bản (`tab_document.metadata`), không đẻ
 * thêm cột: mỗi loại một cụm cột thì bảng phình ra và 90% cột luôn NULL với 90%
 * văn bản. Module Nghỉ phép sau này đọc thẳng từ đó.
 *
 * Danh sách *loại nghỉ* và *buổi* lấy từ `@/shared/constants/statuses` — tệp
 * SINH TỰ ĐỘNG từ `backend/app/core/leave_codes.py`. Đừng gõ tay danh sách thứ
 * hai ở đây, hai đầu lệch nhau là ô chọn hiện mã lạ mà không ai biết vì sao.
 */
export function DocumentLeaveFields({ form }: DocumentLeaveFieldsProps) {
  const { data: employees } = useEmployees({ page_size: 2000 })
  const nhanSu = employees?.items ?? []

  const tuNgay = form.watch('leave.from_date')
  const denNgay = form.watch('leave.to_date')
  const buoiDi = form.watch('leave.from_session')
  const buoiVe = form.watch('leave.to_session')
  const goiY = soNgayGoiY(tuNgay, denNgay, buoiDi, buoiVe)

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <FormField
        control={form.control}
        name="leave.employee_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người nghỉ</FormLabel>
            <Select
              value={String(field.value || 0)}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Mặc định: người chịu trách nhiệm" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="0">— Theo người chịu trách nhiệm —</SelectItem>
                {nhanSu.map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormDescription>
              Hành chính lập hộ thì chọn đúng người nghỉ — đơn sẽ hiện trong danh sách
              của họ.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="leave.leave_type"
        render={({ field }) => (
          <FormItem>
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

      {/*  Ngày và BUỔI đi liền nhau: nửa ngày phép là chuyện thường, tách ra hai
           chỗ thì người ta khai một ngày cho một buổi. */}
      <div className="grid grid-cols-[1fr_auto] gap-2">
        <FormField
          control={form.control}
          name="leave.from_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Từ ngày
                <RequiredMark />
              </FormLabel>
              <FormControl>
                <Input type="date" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="leave.from_session"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Buổi</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-32">
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
      </div>

      <div className="grid grid-cols-[1fr_auto] gap-2">
        <FormField
          control={form.control}
          name="leave.to_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                Đến ngày
                <RequiredMark />
              </FormLabel>
              <FormControl>
                <Input type="date" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="leave.to_session"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Buổi</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <FormControl>
                  <SelectTrigger className="w-32">
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
      </div>

      <FormField
        control={form.control}
        name="leave.total_days"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Tổng số ngày</FormLabel>
            <FormControl>
              <Input
                type="number"
                step="0.5"
                min="0"
                placeholder={goiY ? String(goiY) : ''}
                {...field}
              />
            </FormControl>
            <FormDescription>
              {goiY
                ? `Gợi ý ${goiY} ngày — đếm cả cuối tuần và ngày lễ vì hệ chưa có lịch làm việc. Bỏ trống thì lấy số này.`
                : 'Bỏ trống thì hệ tự tính theo khoảng ngày ở trên.'}
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="leave.handover_employee_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người bàn giao công việc</FormLabel>
            <Select
              value={String(field.value || 0)}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chưa chọn" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="0">— Không bàn giao —</SelectItem>
                {nhanSu.map((item) => (
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

      <FormField
        control={form.control}
        name="leave.contact_phone"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Số liên lạc khi nghỉ</FormLabel>
            <FormControl>
              <Input placeholder="Số gọi được trong thời gian nghỉ" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="leave.reason"
        render={({ field }) => (
          <FormItem className="md:col-span-2">
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
