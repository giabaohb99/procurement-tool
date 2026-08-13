import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Form,
  FormControl,
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
  useDocumentPartner,
  useDocumentPartnerActions,
  useDocumentPartnerHistory,
} from '../hooks/use-document-catalogs'
import {
  documentPartnerSchema,
  type DocumentPartnerFormValues,
} from '../schemas/document-catalog-schemas'
import { PARTNER_KIND_LABELS, type PartnerKind } from '../types/document-partner'

const FORM_ID = 'document-partner-form'

const EMPTY_FORM: DocumentPartnerFormValues = {
  code: '',
  name: '',
  kind: 'agency',
  contact_person: '',
  phone: '',
  email: '',
  address: '',
  is_active: true,
}

/** Trang thêm / sửa một đối tác văn bản. */
export function DocumentPartnerDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const recordId = Number(id)
  const isCreating = !Number.isFinite(recordId)

  const record = useDocumentPartner(isCreating ? undefined : recordId)
  const history = useDocumentPartnerHistory(isCreating ? undefined : recordId)
  const { save, remove } = useDocumentPartnerActions()

  const form = useForm<DocumentPartnerFormValues>({
    resolver: zodResolver(documentPartnerSchema),
    defaultValues: record ? { ...EMPTY_FORM, ...record } : EMPTY_FORM,
  })

  return (
    <DetailPageShell
      title={isCreating ? 'Thêm đối tác' : (record?.name ?? '')}
      description={
        isCreating
          ? 'Khai báo một cơ quan / doanh nghiệp / cá nhân trao đổi văn bản.'
          : `Mã ${record?.code} · ${PARTNER_KIND_LABELS[record?.kind ?? 'agency']}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={appRoutes.document.settingsTab('partners')}
      isMissing={!isCreating && !record}
      missingTitle="Không tìm thấy đối tác"
      history={history}
      onDelete={
        record
          ? () => {
              remove(record.id)
              toast.success(`Đã xóa đối tác "${record.name}"`)
              navigate(appRoutes.document.settingsTab('partners'))
            }
          : undefined
      }
    >
      <Form {...form}>
        <form
          id={FORM_ID}
          onSubmit={form.handleSubmit((values) => {
            const savedId = save(values, record?.id)
            toast.success(isCreating ? 'Đã thêm đối tác' : 'Đã cập nhật đối tác')
            if (isCreating) {
              navigate(appRoutes.document.partnerDetail(savedId), { replace: true })
            }
          })}
        >
          <Card>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mã đối tác</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="VD: CUCTHUE"
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
                  name="kind"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nhóm</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={(value) => field.onChange(value as PartnerKind)}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Object.entries(PARTNER_KIND_LABELS).map(([value, label]) => (
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
              </div>

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tên đối tác</FormLabel>
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
            </CardContent>
          </Card>
        </form>
      </Form>
    </DetailPageShell>
  )
}
