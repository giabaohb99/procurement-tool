import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
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
import { cn } from '@/shared/utils/cn'
import {
  documentTypeSchema,
  type DocumentTypeFormValues,
} from '../schemas/document-type-schema'
import { useSecurityLevelOptions } from '../hooks/use-document-catalogs'
import { SECURITY_LEVEL_KIND_CONFIDENTIAL } from '../types/security-level'
import {
  DOCUMENT_TYPE_FLAGS,
  DOC_GROUP_LABELS,
  EMPTY_DOCUMENT_TYPE_FLAGS,
  ID_SCHEME_HINTS,
  ID_SCHEME_LABELS,
  NUMBER_WHEN_LABELS,
  documentCodeSample,
  type DocumentType,
  type IdScheme,
} from '../types/document-type'

interface DocumentTypeFormProps {
  /**
   * Id của thẻ `<form>`. Nút Lưu nằm TRÊN ĐẦU TRANG (cạnh tiêu đề) nên nó phải
   * trỏ về đây bằng thuộc tính `form={...}` thay vì nằm trong form.
   */
  formId: string
  /** Có = sửa, không có = thêm mới. */
  documentType?: DocumentType
  onSubmit: (values: DocumentTypeFormValues) => void
}

const EMPTY_FORM: DocumentTypeFormValues = {
  code: '',
  name: '',
  group_code: '',
  description: '',
  id_scheme: 2,
  number_when: 2,
  default_secrecy: 2,
  review_cycle_months: 0,
  retention_months: 0,
  is_active: true,
  ...EMPTY_DOCUMENT_TYPE_FLAGS,
}

/** Khối nhập thông tin của một loại văn bản (dùng cho cả thêm mới lẫn sửa). */
export function DocumentTypeForm({
  formId,
  documentType,
  onSubmit,
}: DocumentTypeFormProps) {
  const form = useForm<DocumentTypeFormValues>({
    resolver: zodResolver(documentTypeSchema),
    defaultValues: documentType ? { ...EMPTY_FORM, ...documentType } : EMPTY_FORM,
  })

  const idScheme = form.watch('id_scheme')
  const code = form.watch('code')
  const confidentialLevels = useSecurityLevelOptions(SECURITY_LEVEL_KIND_CONFIDENTIAL)

  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <Card>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã loại</FormLabel>
                    <FormControl>
                      {/* Tự viết hoa: mã luôn là chữ HOA, bắt người dùng giữ
                          Shift chỉ để rồi báo lỗi là vô ích. */}
                      <Input
                        placeholder="VD: CV"
                        {...field}
                        onChange={(event) =>
                          field.onChange(event.target.value.toUpperCase())
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Mã này đi thẳng vào số hiệu, không đổi được sau khi đã cấp số.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem className="sm:col-span-2">
                    <FormLabel>Tên loại văn bản</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Công văn" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="group_code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nhóm</FormLabel>
                  <Select value={field.value || 'none'} onValueChange={(value) => field.onChange(value === 'none' ? '' : value)}>
                    <FormControl>
                      <SelectTrigger className="w-full sm:w-72">
                        <SelectValue placeholder="Chưa xếp nhóm" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="none">Chưa xếp nhóm</SelectItem>
                      {Object.entries(DOC_GROUP_LABELS).map(([value, label]) => (
                        <SelectItem key={value} value={value}>
                          {label}
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
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mô tả</FormLabel>
                  <FormControl>
                    <Textarea rows={3} placeholder="Dùng trong trường hợp nào…" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Số hiệu</p>
              <p className="text-sm text-muted-foreground">
                Hai kiểu định danh dùng cho hai loại việc khác nhau, không thay nhau được.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="id_scheme"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Kiểu định danh</FormLabel>
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => field.onChange(Number(value) as IdScheme)}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(ID_SCHEME_LABELS).map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>{ID_SCHEME_HINTS[idScheme]}</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="number_when"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cấp số lúc nào</FormLabel>
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => field.onChange(Number(value) as 1 | 2)}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {Object.entries(NUMBER_WHEN_LABELS).map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Nên để "khi được duyệt": bản nháp bỏ dở mà đã chiếm số thì sổ thủng lỗ.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <p className="rounded-md bg-muted px-3 py-2 text-sm">
              Số hiệu sẽ có dạng{' '}
              <span className="font-mono font-medium">
                {documentCodeSample(code, idScheme)}
              </span>
              <span className="text-muted-foreground"> — số thật do hệ thống cấp.</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Quy tắc áp dụng cho loại này</p>
              <p className="text-sm text-muted-foreground">
                Bấm để bật/tắt. Mỗi cờ quyết định một bước trong vòng đời văn bản.
              </p>
            </div>

            {/*
              Dạng CHIP bật/tắt thay vì một cột checkbox: bốn lựa chọn xếp dọc
              chiếm nửa trang, mà chúng lại ngang hàng nhau nên hàng chip đọc
              nhanh hơn nhiều.
            */}
            <div className="flex flex-wrap gap-2">
              {DOCUMENT_TYPE_FLAGS.map((flag) => (
                <FormField
                  key={flag.key}
                  control={form.control}
                  name={flag.key}
                  render={({ field }) => (
                    <Button
                      type="button"
                      variant="outline"
                      title={flag.hint}
                      aria-pressed={field.value}
                      onClick={() => field.onChange(!field.value)}
                      className={cn(
                        field.value && 'border-primary bg-primary/5 text-primary',
                      )}
                    >
                      {flag.label}
                    </Button>
                  )}
                />
              ))}
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <FormField
                control={form.control}
                name="default_secrecy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mức mật mặc định</FormLabel>
                    <Select
                      value={String(field.value)}
                      onValueChange={(value) => field.onChange(Number(value))}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {confidentialLevels.map((level) => (
                          <SelectItem
                            key={level.id}
                            value={String(level.value)}
                            description={level.description}
                          >
                            {level.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>Sửa lại được trên từng văn bản.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="review_cycle_months"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Chu kỳ rà soát (tháng)</FormLabel>
                    <FormControl>
                      <Input type="number" min={0} {...field} />
                    </FormControl>
                    <FormDescription>0 = không rà định kỳ.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="retention_months"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Thời hạn lưu trữ (tháng)</FormLabel>
                    <FormControl>
                      <Input type="number" min={0} {...field} />
                    </FormControl>
                    <FormDescription>0 = lưu vĩnh viễn.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

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
                      Tắt thì loại này không còn hiện khi tạo văn bản mới, văn bản cũ vẫn
                      giữ nguyên.
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
