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
  useSecurityLevel,
  useSecurityLevelActions,
  useSecurityLevelHistory,
} from '../hooks/use-document-catalogs'
import {
  securityLevelSchema,
  type SecurityLevelFormValues,
} from '../schemas/document-catalog-schemas'
import {
  SECURITY_LEVEL_KIND_LABELS,
  type SecurityLevelKind,
} from '../types/security-level'

const FORM_ID = 'security-level-form'

const EMPTY_FORM: SecurityLevelFormValues = {
  code: '',
  name: '',
  kind: 'confidential',
  rank: 0,
  description: '',
  is_active: true,
}

/** Trang thêm / sửa một mức mật hoặc khẩn. */
export function SecurityLevelDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const recordId = Number(id)
  const isCreating = !Number.isFinite(recordId)

  const record = useSecurityLevel(isCreating ? undefined : recordId)
  const history = useSecurityLevelHistory(isCreating ? undefined : recordId)
  const { save, remove } = useSecurityLevelActions()

  const form = useForm<SecurityLevelFormValues>({
    resolver: zodResolver(securityLevelSchema),
    defaultValues: record ? { ...EMPTY_FORM, ...record } : EMPTY_FORM,
  })

  return (
    <DetailPageShell
      title={isCreating ? 'Thêm mức mật / khẩn' : (record?.name ?? '')}
      description={
        isCreating
          ? 'Khai báo một mức mới cho thang mật hoặc thang khẩn.'
          : `${SECURITY_LEVEL_KIND_LABELS[record?.kind ?? 'confidential']} · thứ bậc ${record?.rank}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={appRoutes.document.settingsTab('security-levels')}
      isMissing={!isCreating && !record}
      missingTitle="Không tìm thấy mức mật / khẩn"
      history={history}
      onDelete={
        record
          ? () => {
              remove(record.id)
              toast.success(`Đã xóa mức "${record.name}"`)
              navigate(appRoutes.document.settingsTab('security-levels'))
            }
          : undefined
      }
    >
      <Form {...form}>
        <form
          id={FORM_ID}
          onSubmit={form.handleSubmit((values) => {
            const savedId = save(values, record?.id)
            toast.success(isCreating ? 'Đã thêm mức' : 'Đã cập nhật mức')
            if (isCreating) {
              navigate(appRoutes.document.securityLevelDetail(savedId), { replace: true })
            }
          })}
        >
          <Card>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-3">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mã</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="VD: MAT"
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
                      <FormLabel>Thang đo</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={(value) => field.onChange(value as SecurityLevelKind)}
                      >
                        <FormControl>
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Object.entries(SECURITY_LEVEL_KIND_LABELS).map(
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
                  name="rank"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Thứ bậc</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} max={9} {...field} />
                      </FormControl>
                      <FormDescription>Càng lớn càng nghiêm / càng gấp.</FormDescription>
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
                    <FormLabel>Tên mức</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Tối mật" {...field} />
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
                      <Textarea rows={3} {...field} />
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
