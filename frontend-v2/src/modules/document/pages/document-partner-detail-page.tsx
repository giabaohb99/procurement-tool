import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
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
import { DetailPageShell } from '../components/detail-page-shell'
import {
  useDeleteDocumentPartner,
  useDocumentPartner,
  useSaveDocumentPartner,
} from '../hooks/use-document-catalogs'
import {
  documentPartnerSchema,
  type DocumentPartnerFormValues,
} from '../schemas/document-catalog-schemas'
import {
  PARTNER_KIND_LABELS,
  PARTNER_KIND_OPTIONS,
  type PartnerKind,
} from '../types/document-partner'

const FORM_ID = 'document-partner-form'

const EMPTY_FORM: DocumentPartnerFormValues = {
  code: '',
  name: '',
  kind: 1,
  contact_person: '',
  phone: '',
  email: '',
  address: '',
  is_active: true,
}

/** Trang thêm / sửa một đơn vị gửi nhận bên ngoài. */
export function DocumentPartnerDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const recordId = Number(id)
  const isCreating = !Number.isFinite(recordId)

  const { data: record, isLoading } = useDocumentPartner(
    isCreating ? undefined : recordId,
  )
  const save = useSaveDocumentPartner()
  const remove = useDeleteDocumentPartner()

  const form = useForm<DocumentPartnerFormValues>({
    resolver: zodResolver(documentPartnerSchema),
    // `values` chứ không phải `defaultValues`: bản ghi về sau lượt render đầu
    // (đang tải API), `defaultValues` chỉ đọc một lần nên form sẽ trống trơn.
    defaultValues: EMPTY_FORM,
    values: record ? { ...EMPTY_FORM, ...record } : undefined,
  })

  const backTo = appRoutes.document.settingsTab('partners')

  return (
    <DetailPageShell
      title={isCreating ? 'Thêm đơn vị gửi nhận' : (record?.name ?? '')}
      description={
        isCreating
          ? 'Khai báo một cơ quan / doanh nghiệp / cá nhân trao đổi văn bản.'
          : `Mã ${record?.code} · ${PARTNER_KIND_LABELS[record?.kind ?? 1]}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !record}
      missingTitle="Không tìm thấy đơn vị"
      audit={record ? { entity: 'external_party', id: record.id } : undefined}
      onDelete={
        record
          ? () => remove.mutate(record.id, { onSuccess: () => navigate(backTo) })
          : undefined
      }
    >
      <Form {...form}>
        <form
          id={FORM_ID}
          onSubmit={form.handleSubmit((values) =>
            save.mutate(
              { id: record?.id, values },
              {
                onSuccess: (saved) => {
                  if (isCreating) {
                    navigate(appRoutes.document.partnerDetail(saved.id), {
                      replace: true,
                    })
                  }
                },
              },
            ),
          )}
        >
          <Card>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mã đơn vị</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="VD: CUCTHUE"
                          {...field}
                          onChange={(event) =>
                            field.onChange(event.target.value.toUpperCase())
                          }
                        />
                      </FormControl>
                      <FormDescription>Bỏ trống thì hệ thống tự sinh mã.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="kind"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nhóm</FormLabel>
                      <Select
                        value={String(field.value)}
                        onValueChange={(value) =>
                          field.onChange(Number(value) as PartnerKind)
                        }
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {PARTNER_KIND_OPTIONS.map((option) => (
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
              </div>

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tên đơn vị</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Cục Thuế TP.HCM" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid gap-4 sm:grid-cols-3">
                <FormField
                  control={form.control}
                  name="contact_person"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Người liên hệ</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="phone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Điện thoại</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input type="email" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Địa chỉ</FormLabel>
                    <FormControl>
                      <Textarea rows={2} {...field} />
                    </FormControl>
                    <FormMessage />
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
                        Tắt thì đơn vị này không còn hiện khi chọn nơi gửi / nơi nhận.
                      </FormDescription>
                    </div>
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>
        </form>
      </Form>
    </DetailPageShell>
  )
}
