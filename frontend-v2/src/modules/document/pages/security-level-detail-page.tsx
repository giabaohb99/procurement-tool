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
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
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
  useDeleteSecurityLevel,
  useSaveSecurityLevel,
  useSecurityLevel,
} from '../hooks/use-document-catalogs'
import {
  securityLevelSchema,
  type SecurityLevelFormValues,
} from '../schemas/document-catalog-schemas'
import {
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  SECURITY_LEVEL_KIND_LABELS,
  SECURITY_LEVEL_KIND_URGENCY,
  type SecurityLevelKind,
} from '../types/security-level'

const FORM_ID = 'security-level-form'

const EMPTY_FORM: SecurityLevelFormValues = {
  kind: SECURITY_LEVEL_KIND_CONFIDENTIAL,
  value: 1,
  code: '',
  name: '',
  description: '',
  is_active: true,
}

/**
 * Trang thêm / sửa MỘT bậc mức mật hoặc độ khẩn.
 *
 * `kind` (thang) và `value` (con số lưu trên văn bản, đồng thời là thứ bậc)
 * chỉ nhập được lúc TẠO MỚI. Sửa thì hai ô này khóa cứng (`ReadOnlyValue`,
 * không phải `<Input disabled>` — xem `docs/ui`): đổi thang là số đang nằm
 * trên hàng nghìn văn bản đọc sang nghĩa khác, đổi bậc là mọi điều kiện luồng
 * duyệt đã cấu hình trỏ vào một mức khác mà không báo gì. Cần một bậc khác
 * thì thêm dòng mới rồi ngừng dòng cũ — xem đầu `types/security-level.ts`.
 */
export function SecurityLevelDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const recordId = Number(id)
  const isCreating = !Number.isFinite(recordId)

  const { data: record, isLoading } = useSecurityLevel(isCreating ? undefined : recordId)
  const save = useSaveSecurityLevel()
  const remove = useDeleteSecurityLevel()

  const form = useForm<SecurityLevelFormValues>({
    resolver: zodResolver(securityLevelSchema),
    // `values` chứ không phải `defaultValues`: bản ghi về sau lượt render đầu
    // (đang tải API), `defaultValues` chỉ đọc một lần nên form sẽ trống trơn.
    defaultValues: EMPTY_FORM,
    values: record ? { ...EMPTY_FORM, ...record } : undefined,
  })

  const kind = form.watch('kind')
  const backTo = appRoutes.document.settingsTab('security-levels')

  return (
    <DetailPageShell
      title={isCreating ? 'Thêm bậc mức mật / độ khẩn' : (record?.name ?? '')}
      description={
        isCreating
          ? 'Khai một bậc mới cho thang Mức mật hoặc Độ khẩn.'
          : `Mã ${record?.code} · ${record ? SECURITY_LEVEL_KIND_LABELS[record.kind] : ''} · bậc ${record?.value}`
      }
      formId={FORM_ID}
      isCreating={isCreating}
      backTo={backTo}
      isMissing={!isCreating && !isLoading && !record}
      missingTitle="Không tìm thấy bậc này"
      audit={record ? { entity: 'security_level', id: record.id } : undefined}
      deleteConfirmDescription="Không xóa được nếu đang có văn bản hoặc điều kiện luồng duyệt dùng bậc này — hệ thống sẽ báo rõ chỗ vướng."
      onDelete={
        record
          ? () => remove.mutate(record.id, { onSuccess: () => navigate(backTo) })
          : undefined
      }
    >
      <Form {...form}>
        <form
          id={FORM_ID}
          onSubmit={form.handleSubmit((values) => {
            if (isCreating) {
              save.mutate(
                { values },
                {
                  onSuccess: (saved) =>
                    navigate(appRoutes.document.securityLevelDetail(saved.id), { replace: true }),
                },
              )
              return
            }

            // Chỉ gửi bốn trường sửa được — KHÔNG kèm `kind`/`value` dù form vẫn
            // giữ chúng để hiện ô khóa (xem `SECURITY_LEVEL_KIND_LABELS` ở trên).
            save.mutate({
              id: recordId,
              values: {
                code: values.code,
                name: values.name,
                description: values.description,
                is_active: values.is_active,
              },
            })
          })}
        >
          <Card>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="kind"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Thang</FormLabel>
                      {isCreating ? (
                        <>
                          <Select
                            value={String(field.value)}
                            onValueChange={(value) =>
                              field.onChange(Number(value) as SecurityLevelKind)
                            }
                          >
                            <FormControl>
                              <SelectTrigger className="w-full">
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value={String(SECURITY_LEVEL_KIND_CONFIDENTIAL)}>
                                {SECURITY_LEVEL_KIND_LABELS[SECURITY_LEVEL_KIND_CONFIDENTIAL]}
                              </SelectItem>
                              <SelectItem value={String(SECURITY_LEVEL_KIND_URGENCY)}>
                                {SECURITY_LEVEL_KIND_LABELS[SECURITY_LEVEL_KIND_URGENCY]}
                              </SelectItem>
                            </SelectContent>
                          </Select>
                          <FormDescription>Không đổi được sau khi tạo.</FormDescription>
                        </>
                      ) : (
                        <ReadOnlyValue>{SECURITY_LEVEL_KIND_LABELS[kind]}</ReadOnlyValue>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="value"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Bậc</FormLabel>
                      {isCreating ? (
                        <>
                          <FormControl>
                            <Input type="number" min={1} max={99} {...field} />
                          </FormControl>
                          <FormDescription>
                            Con số này lưu thẳng lên văn bản và không đổi được sau khi tạo. Càng
                            lớn càng nghiêm (mức mật) / càng gấp (độ khẩn).
                          </FormDescription>
                        </>
                      ) : (
                        <ReadOnlyValue>{field.value}</ReadOnlyValue>
                      )}
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {!isCreating && (
                <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                  Khóa Thang và Bậc: đổi thang là số đang nằm trên văn bản đọc sang nghĩa khác,
                  đổi bậc là điều kiện luồng duyệt đã cấu hình trỏ vào một mức khác mà không báo
                  gì. Cần một bậc khác thì thêm dòng mới rồi ngừng dùng dòng này.
                </p>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mã bậc</FormLabel>
                      <FormControl>
                        {/* Tự viết hoa: mã luôn là chữ HOA. */}
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
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tên bậc</FormLabel>
                      <FormControl>
                        <Input placeholder="VD: Mật" {...field} />
                      </FormControl>
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
                      <Textarea
                        rows={3}
                        placeholder="Đóng dấu mức này thì ai đọc được, bị chặn cái gì…"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Câu này hiện lại ở ô chọn mức mật / độ khẩn lúc soạn văn bản — viết sao cho
                      người soạn CHỌN được, không phải mô tả quyền của người đọc.
                    </FormDescription>
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
                        Tắt thì bậc này không còn hiện khi chọn mức mật / độ khẩn cho văn bản mới.
                        Văn bản cũ đã mang bậc này vẫn tra ra đúng tên.
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
