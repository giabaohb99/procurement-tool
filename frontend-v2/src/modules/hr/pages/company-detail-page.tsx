import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, CircleCheck, CircleX, Hash, Loader2, ReceiptText, Save, UserRoundCog } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { AvatarUploader } from '@/shared/ui/avatar-uploader'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { FormSection } from '@/shared/ui/form-section'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { ActiveStatusSelect } from '../components/active-status-select'
import { LookupSelect } from '../components/lookup-select'
import {
  useCompanies,
  useCompany,
  useDeleteCompany,
  useSaveCompany,
  useUploadCompanyLogo,
} from '../hooks/use-companies'
import { useEmployees } from '../hooks/use-employees'
import { EMPTY_COMPANY_FORM, companySchema, type CompanyFormValues } from '../schemas/company-schema'
import { companyInitial, type Company } from '../types/company'

/**
 * Chi tiết pháp nhân — form SỬA TRỰC TIẾP, không phải thẻ chỉ-đọc.
 *
 * Mở ra là đã ở trạng thái sửa được, Lưu/Xóa nằm ngay đầu trang; giữ đúng cách
 * bản `frontend` cũ làm để người dùng không phải học lại thao tác. Logo đổi
 * riêng ngay trên ảnh (endpoint upload riêng, không nằm trong payload form).
 */
export function CompanyDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const companyId = Number(id)

  const { can } = usePermission()
  const canWrite = can('company', 'write')

  const { data: company, isLoading, isError } = useCompany(companyId)
  const saveCompany = useSaveCompany()
  const deleteCompany = useDeleteCompany()
  const uploadLogo = useUploadCompanyLogo(companyId)

  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: allCompanies } = useCompanies({ page_size: 1000 })

  const form = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: EMPTY_COMPANY_FORM,
  })

  // Dữ liệu về sau khi form đã mount -> nạp lại giá trị.
  useEffect(() => {
    if (company) form.reset({ ...EMPTY_COMPANY_FORM, ...company })
  }, [company, form])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-28 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError || !company) {
    return (
      <ErrorState
        title="Không tìm thấy công ty"
        description="Pháp nhân có thể đã bị xóa, hoặc bạn không có quyền xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.hr.companies)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  async function onSubmit(values: CompanyFormValues) {
    await saveCompany.mutateAsync({ id: companyId, values })
  }

  async function handleDelete() {
    await deleteCompany.mutateAsync(companyId)
    navigate(appRoutes.hr.companies)
  }

  // Chính nó không được làm công ty mẹ của nó.
  const parentOptions = (allCompanies?.items ?? [])
    .filter((item) => item.id !== companyId)
    .map((item) => ({ id: item.id, label: `${item.code} — ${item.name}` }))

  return (
    <PageContainer>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link to={appRoutes.hr.companies}>
                <ArrowLeft />
                Danh sách công ty
              </Link>
            </Button>

            <div className="flex items-center gap-2">
              <PermissionGate entity="company" action="write">
                <Button type="submit" disabled={saveCompany.isPending}>
                  {saveCompany.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                  Lưu
                </Button>
              </PermissionGate>

              <PermissionGate entity="company" action="delete">
                <DeleteConfirmButton
                  recordName={company.name}
                  pending={deleteCompany.isPending}
                  onConfirm={handleDelete}
                  warning="Chứng từ cũ gắn với pháp nhân này sẽ mất tham chiếu."
                />
              </PermissionGate>
            </div>
          </div>

          <RecordIdentityCard
            media={
              <AvatarUploader
                src={company.logo}
                fallback={companyInitial(company)}
                alt={company.name}
                fit="contain"
                onUpload={canWrite ? (file) => uploadLogo.mutateAsync(file) : undefined}
                disabledHint="Logo công ty"
              />
            }
            title={company.name}
            chips={identityChips(company)}
          />

          <Card className="gap-4 p-5">
            <FormSection title="Định danh">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã</FormLabel>
                    <FormControl>
                      {/* Mã là định danh dùng khắp hệ — đổi sau khi tạo sẽ vỡ tham chiếu. */}
                      <Input disabled {...field} />
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
                    <FormLabel>Tên pháp nhân</FormLabel>
                    <FormControl>
                      <Input disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="tax_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>MST</FormLabel>
                    <FormControl>
                      <Input disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Hóa đơn & Liên hệ">
              <FormField
                control={form.control}
                name="invoice_email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email nhận hóa đơn</FormLabel>
                    <FormControl>
                      <Input type="email" disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormDescription>
                      Nơi nhận hóa đơn điện tử của pháp nhân này.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Địa chỉ</FormLabel>
                    <FormControl>
                      <Textarea rows={3} disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Đại diện pháp lý">
              <FormField
                control={form.control}
                name="legal_representative_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Người đại diện pháp lý</FormLabel>
                    <LookupSelect
                      value={field.value}
                      // LookupSelect trả 0 cho mục bỏ chọn; backend nhận NULL.
                      onChange={(v) => field.onChange(v === 0 ? null : v)}
                      disabled={!canWrite}
                      placeholder="Chọn nhân sự"
                      emptyLabel="— Chưa chỉ định —"
                      items={(employees?.items ?? []).map((e) => ({
                        id: e.id,
                        label: e.full_name,
                      }))}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="legal_rep_title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Chức danh</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Giám đốc" disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormDescription>In trên hợp đồng / chứng từ.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Tổ chức">
              <FormField
                control={form.control}
                name="parent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Công ty mẹ</FormLabel>
                    {/* Bản cũ bắt gõ ID; chọn theo tên đỡ phải đi tra id ở nơi khác. */}
                    <LookupSelect
                      value={field.value}
                      onChange={field.onChange}
                      disabled={!canWrite}
                      placeholder="Chọn pháp nhân cấp trên"
                      emptyLabel="— Đây là công ty gốc —"
                      items={parentOptions}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trạng thái</FormLabel>
                    <ActiveStatusSelect
                      value={field.value}
                      onChange={field.onChange}
                      disabled={!canWrite}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>
          </Card>
        </form>
      </Form>

      <div className="mt-5">
        <AuditTimeline entity="company" entityId={companyId} />
      </div>
    </PageContainer>
  )
}

function identityChips(company: Company): IdentityChip[] {
  const chips: IdentityChip[] = []
  if (company.code) chips.push({ icon: Hash, text: company.code, tone: 'code' })
  if (company.tax_code) {
    chips.push({ icon: ReceiptText, text: `MST ${company.tax_code}` })
  }
  if (company.legal_rep_name) {
    chips.push({ icon: UserRoundCog, text: company.legal_rep_name })
  }
  chips.push(
    company.is_active
      ? { icon: CircleCheck, text: 'Đang dùng', tone: 'ok' }
      : { icon: CircleX, text: 'Ngừng', tone: 'muted' },
  )
  return chips
}
