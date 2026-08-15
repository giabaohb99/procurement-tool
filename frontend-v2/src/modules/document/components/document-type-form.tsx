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
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import {
  documentTypeSchema,
  type DocumentTypeFormValues,
} from '../schemas/document-type-schema'
import {
  DOCUMENT_TYPE_OPTIONS,
  EMPTY_DOCUMENT_TYPE_OPTIONS,
  type DocumentType,
} from '../types/document-type'

interface DocumentTypeFormProps {
  /**
   * Id của thẻ `<form>`. Nút Lưu nằm TRÊN ĐẦU TRANG (cạnh tiêu đề) nên nó phải
   * trỏ về đây bằng thuộc tính `form={...}` thay vì nằm trong form.
   */
  formId: string
  /** Có = sửa, không có = thêm mới. */
  documentType?: DocumentType
  /** Mã đã được loại KHÁC dùng chưa — mã phải duy nhất vì nó đi vào số hiệu. */
  isCodeTaken: (code: string, id?: number) => boolean
  onSubmit: (values: DocumentTypeFormValues) => void
}

const EMPTY_FORM: DocumentTypeFormValues = {
  code: '',
  name: '',
  prefix: '',
  description: '',
  is_active: true,
  ...EMPTY_DOCUMENT_TYPE_OPTIONS,
}

/** Khối nhập thông tin của một loại văn bản (dùng cho cả thêm mới lẫn sửa). */
export function DocumentTypeForm({
  formId,
  documentType,
  isCodeTaken,
  onSubmit,
}: DocumentTypeFormProps) {
  const form = useForm<DocumentTypeFormValues>({
    resolver: zodResolver(documentTypeSchema),
    defaultValues: documentType ? { ...EMPTY_FORM, ...documentType } : EMPTY_FORM,
  })

  function handleSubmit(values: DocumentTypeFormValues) {
    // Trùng mã phải báo NGAY TRÊN Ô nhập, không phải toast: người dùng cần biết
    // sửa ở đâu.
    if (isCodeTaken(values.code, documentType?.id)) {
      form.setError('code', { message: 'Mã này đã có loại văn bản khác dùng' })
      return
    }
    onSubmit(values)
  }

  return (
    <Form {...form}>
      <form id={formId} onSubmit={form.handleSubmit(handleSubmit)}>
        <Card>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
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
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="prefix"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tiền tố số hiệu</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="VD: CV"
                        {...field}
                        onChange={(event) =>
                          field.onChange(event.target.value.toUpperCase())
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Số hiệu sẽ có dạng {form.watch('prefix') || '{tiền tố}'}-2026-001.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tên loại văn bản</FormLabel>
                  <FormControl>
                    <Input placeholder="VD: Công văn" {...field} />
                  </FormControl>
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
                    <Textarea
                      rows={3}
                      placeholder="Dùng trong trường hợp nào…"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/*
              Tùy chọn khác — dạng CHIP bật/tắt thay vì một cột checkbox: sáu
              lựa chọn xếp dọc chiếm nửa trang, mà chúng lại ngang hàng nhau nên
              hàng chip đọc nhanh hơn nhiều.
            */}
            <div className="space-y-2 border-t pt-4">
              <p className="text-sm font-medium">Tùy chọn khác</p>
              <div className="flex flex-wrap gap-2">
                {DOCUMENT_TYPE_OPTIONS.map((option) => (
                  <FormField
                    key={option.key}
                    control={form.control}
                    name={option.key}
                    render={({ field }) => (
                      <Button
                        type="button"
                        variant="outline"
                        title={option.hint}
                        aria-pressed={field.value}
                        onClick={() => field.onChange(!field.value)}
                        className={cn(
                          field.value && 'border-primary bg-primary/5 text-primary',
                        )}
                      >
                        {option.label}
                      </Button>
                    )}
                  />
                ))}
              </div>
            </div>

            <FormField
              control={form.control}
              name="is_active"
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
                    <FormLabel>Đang dùng</FormLabel>
                    <FormDescription>
                      Tắt thì loại này không còn hiện khi tạo văn bản mới, văn bản cũ
                      vẫn giữ nguyên.
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
