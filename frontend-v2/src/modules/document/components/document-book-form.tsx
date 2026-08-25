import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { Card, CardContent } from '@/shared/ui/card'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Form,
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
import {
  documentBookSchema,
  type DocumentBookFormValues,
} from '../schemas/document-book-schema'
import { BOOK_KIND_OPTIONS, type BookKind, type DocumentBook } from '../types/document-book'

interface DocumentBookFormProps {
  formId: string
  book?: DocumentBook
  onSubmit: (values: DocumentBookFormValues) => void
}

const EMPTY_FORM: DocumentBookFormValues = {
  code: '',
  name: '',
  kind: 1,
  description: '',
  company_id: 0,
  number_prefix: '',
  reset_yearly: true,
  start_no: 1,
  manager_ids: [],
  viewer_ids: [],
  is_active: true,
}

/** Danh mục nạp một lần: pháp nhân chỉ vài chục dòng. */
const LOOKUP_PAGE_SIZE = 200

/**
 * Khai báo một quyển sổ — **một card duy nhất**, đọc từ trên xuống là hết:
 * sổ là gì → của ai → đánh số ra sao.
 *
 * Người quản lý và người xem để ngay trong card này chứ không tách xuống dưới:
 * hai thứ đó là một phần của việc "mở sổ", tách ra thì người khai lướt qua và
 * để trống, mà sổ không có người quản lý là sổ không ai sửa hay đóng được.
 */
export function DocumentBookForm({ formId, book, onSubmit }: DocumentBookFormProps) {
  const form = useForm<DocumentBookFormValues>({
    resolver: zodResolver(documentBookSchema),
    defaultValues: EMPTY_FORM,
    // `values` chứ không chỉ `defaultValues`: bản ghi về sau lượt render đầu.
    values: book ? { ...EMPTY_FORM, ...book } : undefined,
  })

  const { data: companies } = useCompanies({ page_size: LOOKUP_PAGE_SIZE })
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })

  const isEditing = Boolean(book)
  //  Sổ đã cấp số thì khóa số bắt đầu — kéo về là lệch cả sổ đã phát ra ngoài.
  const hasIssued = (book?.issued_count ?? 0) > 0
  const employeeList = employees?.items ?? []

  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <Card>
          <CardContent className="space-y-4">
            {/*  MỘT LƯỚI 2 CỘT CHO CẢ THẺ, và `items-start` ở mọi hàng.
                 Trước 25/08/2026 hàng đầu là `grid-cols-3` (Mã sổ 1 cột, Tên sổ
                 2 cột) còn các hàng dưới là `grid-cols-2`, nên đường chia cột
                 chạy zíc zắc dọc form: đo được 666 → 855 → 855 → 666.
                 Thiếu `items-start` còn hỏng theo chiều dọc: ô lưới mặc định
                 CĂNG ra cho bằng hàng, mà `FormItem` là `grid` với hàng `auto`
                 nên phần dư bị chia đều cho các hàng con — ô nào ít dòng hơn
                 (Tên sổ không có câu mô tả) thì nhãn và ô nhập bị đẩy giãn ra.
                 Đo được: ô nhập «Tên sổ» thấp hơn «Mã sổ» đúng 14px. */}
            <div className="grid items-start gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã sổ</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Tự sinh nếu bỏ trống"
                        disabled={isEditing}
                        {...field}
                        onChange={(event) =>
                          field.onChange(event.target.value.toUpperCase())
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      {isEditing
                        ? 'Mã sổ là khóa của bộ đếm, không sửa được.'
                        : 'Bỏ trống thì hệ thống tự sinh theo loại sổ.'}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Tên sổ <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Sổ công văn đến 2026" {...field} />
                    </FormControl>
                    {/*  Có câu mô tả để hàng này cân với ô «Mã sổ» bên trái, và
                         cũng để nói rõ tên sổ là thứ người dùng NHÌN THẤY khắp
                         nơi — khác mã sổ vốn chỉ là khóa của bộ đếm. */}
                    <FormDescription>Tên hiện trong ô chọn sổ khi soạn văn bản.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid items-start gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="kind"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loại sổ</FormLabel>
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => field.onChange(Number(value) as BookKind)}
                      disabled={isEditing && hasIssued}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {BOOK_KIND_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={String(option.value)}>
                            {option.label}
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
                name="company_id"
                render={({ field }) => (
                  <FormItem>
                    {/*  Có dấu sao vì `company_id` bị chặn ở `min(1)` trong
                         `document-book-schema.ts` — trước đây bắt buộc thật mà
                         không vẽ sao, người khai chỉ biết lúc bấm Lưu. */}
                    <FormLabel>
                      Pháp nhân <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      value={field.value ? String(field.value) : ''}
                      onValueChange={(value) => field.onChange(Number(value))}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Chọn pháp nhân" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {(companies?.items ?? []).map((company) => (
                          <SelectItem key={company.id} value={String(company.id)}>
                            {company.name}
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
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mô tả</FormLabel>
                  <FormControl>
                    <Textarea rows={2} placeholder="Sổ này dùng cho việc gì…" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* ===== Người dùng sổ — chỉ định đích danh, không theo phòng ban ===== */}
            <div className="grid items-start gap-4 border-t pt-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="manager_ids"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Người quản lý <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <EmployeeMultiSelect
                        value={field.value}
                        onChange={field.onChange}
                        employees={employeeList}
                        placeholder="Chọn người quản lý…"
                      />
                    </FormControl>
                    <FormDescription>Sửa, đóng và xóa được sổ.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="viewer_ids"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Người xem sổ</FormLabel>
                    <FormControl>
                      <EmployeeMultiSelect
                        value={field.value}
                        onChange={field.onChange}
                        employees={employeeList}
                        placeholder="Chọn người được xem…"
                      />
                    </FormControl>
                    <FormDescription>
                      Chỉ đọc. Chọn từng người, không cấp theo phòng ban.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Cách đánh số</p>
              <p className="text-sm text-muted-foreground">
                Mỗi sổ một bộ đếm riêng. Số thật do hệ thống cấp lúc vào sổ, không gõ tay.
              </p>
            </div>

            <div className="grid items-start gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="number_prefix"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tiền tố</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: VBĐ" {...field} />
                    </FormControl>
                    <FormDescription>
                      Số sẽ có dạng{' '}
                      <span className="font-mono">
                        {`${form.watch('number_prefix') || ''} 08/${new Date().getFullYear()}`.trim()}
                      </span>
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="start_no"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Số bắt đầu</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} disabled={hasIssued} {...field} />
                    </FormControl>
                    <FormDescription>
                      {hasIssued
                        ? 'Sổ đã cấp số nên không đổi được.'
                        : 'Chuyển từ sổ giấy đang dở thì nhập số kế tiếp của sổ giấy.'}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

            </div>

            {/*  Ô tick xuống HÀNG RIÊNG, không chen làm cột thứ ba. Bản cũ phải
                 chèn `pt-8` để đẩy nó xuống cho ngang hàng ô nhập bên cạnh —
                 một con số phỏng chừng theo chiều cao nhãn, mà nhãn xuống dòng
                 (màn hẹp, hoặc đổi chữ) là lệch ngay. */}
            <FormField
              control={form.control}
              name="reset_yearly"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-3">
                  <FormControl>
                    <Checkbox
                      className="mt-0.5"
                      checked={field.value}
                      onCheckedChange={(checked) => field.onChange(checked === true)}
                    />
                  </FormControl>
                  <div className="space-y-1">
                    <FormLabel>Đếm lại mỗi năm</FormLabel>
                    <FormDescription>Đúng lệ hành chính, nên để bật.</FormDescription>
                  </div>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-start gap-3 border-t pt-4">
                  <FormControl>
                    <Checkbox
                      className="mt-0.5"
                      checked={field.value}
                      onCheckedChange={(checked) => field.onChange(checked === true)}
                    />
                  </FormControl>
                  <div className="space-y-1">
                    <FormLabel>Đang dùng</FormLabel>
                    <FormDescription>
                      Tắt thì sổ không còn nhận văn bản mới, số đã cấp vẫn giữ nguyên.
                    </FormDescription>
                  </div>
                </FormItem>
              )}
            />
          </CardContent>
        </Card>
      </form>
    </Form>
  )
}
