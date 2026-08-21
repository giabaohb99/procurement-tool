import type { UseFormReturn } from 'react-hook-form'

import { useEmployees } from '@/modules/hr/hooks/use-employees'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useSecurityLevelOptions } from '../hooks/use-document-catalogs'
import { useStorageLocations } from '../hooks/use-documents'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

const NONE = 'none'

/** Id của `<datalist>` gợi ý ngăn tủ — ô nhập trỏ vào bằng thuộc tính `list`. */
const STORAGE_LOCATION_LIST_ID = 'document-storage-locations'

interface DocumentExtraInfoFieldsProps {
  form: UseFormReturn<DocumentRecordFormValues>
}

/**
 * THÔNG TIN BỔ SUNG: mức mật, độ khẩn, người ký, hiệu lực, số hiệu cũ, từ khóa.
 *
 * Đều là thứ bổ sung được sau nên xếp ở bước cuối — người soạn tạo được cái vỏ
 * văn bản rồi vào gõ nội dung ngay, không phải khai đủ hai mươi ô mới lưu được.
 *
 * **Mức mật và độ khẩn là hai thang ĐỘC LẬP**: một thông báo hỏa tốc vẫn có thể
 * công khai. Đặt cạnh nhau nhưng không bao giờ gộp.
 */
export function DocumentExtraInfoFields({ form }: DocumentExtraInfoFieldsProps) {
  const confidentialLevels = useSecurityLevelOptions('confidential')
  const urgencyLevels = useSecurityLevelOptions('urgent')
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: storageLocations = [] } = useStorageLocations()

  return (
    <div className="grid items-start gap-x-5 gap-y-3 sm:grid-cols-2">
      <FormField
        control={form.control}
        name="secrecy_level"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Mức mật</FormLabel>
            <Select
              value={String(field.value)}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {confidentialLevels.map((level) => (
                  <SelectItem key={level.id} value={String(level.id)}>
                    {level.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {/* Nói thẳng giới hạn hiện tại: cột đã ghi xuống nhưng lớp kiểm mức
                mật là việc của P5, chưa có. */}
            <FormDescription>
              Mặc định theo loại văn bản. Lớp kiểm mức mật chưa bật — chưa đưa
              văn bản mật thật vào hệ thống.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="urgency"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Độ khẩn</FormLabel>
            <Select
              value={String(field.value)}
              onValueChange={(value) => field.onChange(Number(value))}
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {urgencyLevels.map((level) => (
                  <SelectItem key={level.id} value={String(level.id)}>
                    {level.name}
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
        name="signer_employee_id"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Người ký</FormLabel>
            <Select
              value={field.value ? String(field.value) : NONE}
              onValueChange={(value) =>
                field.onChange(value === NONE ? null : Number(value))
              }
            >
              <FormControl>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn người ký" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value={NONE}>-- Chưa chọn --</SelectItem>
                {(employees?.items ?? []).map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.full_name}
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
        name="legacy_code"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Số hiệu cũ (bản giấy)</FormLabel>
            <FormControl>
              <Input placeholder="VD: 145/QĐ-DEGO" {...field} />
            </FormControl>
            {/* C12 — người dùng lâu năm vẫn tra theo số họ đã thuộc. */}
            <FormDescription>Tìm kiếm chấp nhận cả số này.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="storage_location"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Nơi lưu trữ cứng</FormLabel>
            <FormControl>
              {/*  Ô CHỮ TỰ DO có gợi ý, không phải ô chọn: mỗi pháp nhân sắp kho
                   một kiểu, ép vào danh mục là đẻ thêm một màn khai báo mà
                   không ai duy trì. `<datalist>` cho gõ gì cũng được nhưng vẫn
                   bày ra chỗ người khác đã dùng — đủ để không có "Tủ A2" và
                   "tu a2" nằm cạnh nhau trong cùng một kho. */}
              <Input
                list={STORAGE_LOCATION_LIST_ID}
                placeholder="VD: Tủ A2 · Kệ 3 · Bìa 12"
                {...field}
              />
            </FormControl>
            <datalist id={STORAGE_LOCATION_LIST_ID}>
              {storageLocations.map((noi) => (
                <option key={noi} value={noi} />
              ))}
            </datalist>
            {/* Nói rõ ô này để làm gì, không thì người nhập bỏ trống cho nhanh. */}
            <FormDescription>
              Bản giấy có chữ ký tươi đang cất ở đâu — để sau này còn tìm lại.
              Tìm kiếm chấp nhận cả ô này.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="effective_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Ngày hiệu lực</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormDescription>
              Để trống = có hiệu lực ngay khi được duyệt.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="expire_date"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Hết hiệu lực</FormLabel>
            <FormControl>
              <DatePicker value={field.value} onChange={field.onChange} />
            </FormControl>
            <FormDescription>Trống = không đặt hạn.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="keywords"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Từ khóa</FormLabel>
            <FormControl>
              <Input placeholder="Ngăn cách bằng dấu phẩy" {...field} />
            </FormControl>
            <FormDescription>
              Từ người khác sẽ gõ khi đi tìm văn bản này, không phải từ trong tiêu đề.
            </FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="summary"
        render={({ field }) => (
          <FormItem className="sm:col-span-2">
            <FormLabel>Trích yếu nội dung</FormLabel>
            <FormControl>
              <Textarea rows={5} placeholder="Tóm tắt nội dung văn bản…" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  )
}
