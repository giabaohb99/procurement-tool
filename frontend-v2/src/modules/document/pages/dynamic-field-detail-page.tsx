import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
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
import { DetailPageShell } from '../components/detail-page-shell'
import {
  useDynamicField,
  useDynamicFieldActions,
  useDynamicFieldHistory,
} from '../hooks/use-document-catalogs'
import { useDocumentTypes } from '../hooks/use-document-types'
import {
  dynamicFieldSchema,
  type DynamicFieldFormValues,
} from '../schemas/document-catalog-schemas'
import {
  DYNAMIC_FIELD_TYPE_LABELS,
  type DynamicFieldType,
} from '../types/dynamic-field'

const FORM_ID = 'dynamic-field-form'

const EMPTY_FORM: DynamicFieldFormValues = {
  code: '',
  label: '',
  field_type: 'text',
  options_text: '',
  is_required: false,
  document_type_ids: [],
  help_text: '',
  sort_order: 1,
  is_active: true,
}

/** Trang thêm / sửa một trường thông tin động. */
export function DynamicFieldDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const recordId = Number(id)
  const isCreating = !Number.isFinite(recordId)

  const record = useDynamicField(isCreating ? undefined : recordId)
  const history = useDynamicFieldHistory(isCreating ? undefined : recordId)
  const { save, remove } = useDynamicFieldActions()
  const { items: documentTypes } = useDocumentTypes()

  const form = useForm<DynamicFieldFormValues>({
    resolver: zodResolver(dynamicFieldSchema),
    // `options` lưu dạng mảng nhưng nhập bằng textarea mỗi dòng một lựa chọn.
    defaultValues: record
      ? { ...EMPTY_FORM, ...record, options_text: record.options.join('\n') }
      : EMPTY_FORM,
  })

  const fieldType = form.watch('field_type')

  return (
    <DetailPageShell
      title={isCreating ? 'Thêm trường thông tin' : (record?.label ?? '')}
      description={
        isCreating
          ? 'Khai một ô nhập bổ sung cho văn bản.'
          : `Khóa ${record?.code} · ${DYNAMIC_FIELD_TYPE_LABELS[record?.field_type ?? 'text']}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={appRoutes.document.settingsTab('fields')}
      isMissing={!isCreating && !record}
      missingTitle="Không tìm thấy trường thông tin"
      history={history}
      onDelete={
        record
          ? () => {
              remove(record.id)
              toast.success(`Đã xóa trường "${record.label}"`)
              navigate(appRoutes.document.settingsTab('fields'))
            }
          : undefined
      }
    >
      <Form {...form}>
        <form
          id={FORM_ID}
          onSubmit={form.handleSubmit(({ options_text, ...values }) => {
            const savedId = save(
              {
                ...values,
                options: options_text
                  .split('\n')
                  .map((line) => line.trim())
                  .filter(Boolean),
              },
              record?.id,
            )
            toast.success(isCreating ? 'Đã thêm trường' : 'Đã cập nhật trường')
            if (isCreating) {
              navigate(appRoutes.document.fieldDetail(savedId), { replace: true })
            }
          })}
        >
          <Card>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="label"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nhãn hiển thị</FormLabel>
                      <FormControl>
                        <Input placeholder="VD: Giá trị hợp đồng" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Khóa lưu dữ liệu</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="vd: contract_value"
                          {...field}
                          onChange={(event) =>
                            field.onChange(event.target.value.toLowerCase())
                          }
                        />
                      </FormControl>
                      <FormDescription>
                        Đổi khóa sau khi đã có văn bản dùng nó sẽ làm mất dữ liệu cũ.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="field_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Kiểu dữ liệu</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={(value) =>
                          field.onChange(value as DynamicFieldType)
                        }
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Object.entries(DYNAMIC_FIELD_TYPE_LABELS).map(
                            ([value, label]) => (
                              <SelectItem key={value} value={value}>
                                {label}
                              </SelectItem>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="sort_order"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Thứ tự hiện</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} max={999} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* Chỉ kiểu "chọn từ danh sách" mới cần khai lựa chọn. */}
              {fieldType === 'select' && (
                <FormField
                  control={form.control}
                  name="options_text"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Danh sách lựa chọn</FormLabel>
                      <FormControl>
                        <Textarea rows={4} placeholder={'Mỗi dòng một lựa chọn'} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="document_type_ids"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Áp dụng cho loại văn bản</FormLabel>
                    <FormDescription>
                      Không chọn loại nào = áp dụng cho mọi loại.
                    </FormDescription>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {documentTypes.map((type) => {
                        const checked = field.value.includes(type.id)
                        return (
                          <Button
                            key={type.id}
                            type="button"
                            variant="outline"
                            onClick={() =>
                              field.onChange(
                                checked
                                  ? field.value.filter((value) => value !== type.id)
                                  : [...field.value, type.id],
                              )
                            }
                            aria-pressed={checked}
                            className={cn(
                              checked && 'border-primary bg-primary/5 text-primary',
                            )}
                          >
                            {type.name}
                          </Button>
                        )
                      })}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="help_text"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Chú thích dưới ô nhập</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex flex-wrap gap-6">
                <FormField
                  control={form.control}
                  name="is_required"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-3">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(checked) => field.onChange(checked === true)}
                        />
                      </FormControl>
                      <FormLabel>Bắt buộc nhập</FormLabel>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="is_active"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center gap-3">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={(checked) => field.onChange(checked === true)}
                        />
                      </FormControl>
                      <FormLabel>Đang dùng</FormLabel>
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>
        </form>
      </Form>
    </DetailPageShell>
  )
}
