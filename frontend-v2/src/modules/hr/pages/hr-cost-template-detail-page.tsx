import { ArrowLeft, Copy, FileText, ListChecks, Save } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { HrCostItemsEditor } from '../components/hr-cost-items-editor'
import { PlanLabeledField } from '../components/plan-labeled-field'
import { useHrCostGroups, useDeleteHrCostTemplate, useDuplicateHrCostTemplate, useHrCostTemplate, useSaveHrCostTemplate } from '../hooks/use-hr-cost-templates'
import { useJobPositions } from '../hooks/use-job-positions'
import type { HrCostTemplate, HrCostTemplatePayload } from '../types/hr-cost'
import { normalizeCostItem } from '../utils/headcount-plan-draft'
import { toCostItemPayload } from '../utils/headcount-plan-payload'

const toForm = (t?: HrCostTemplate): HrCostTemplatePayload => ({
  name: t?.name ?? '',
  note: t?.note ?? '',
  is_active: t?.is_active ?? true,
  items: (t?.items ?? []).map(normalizeCostItem),
})

/**
 * TRANG MẪU KHOẢN CHI PHÍ `/hr/hr-cost-templates/new` · `/:id` (duoc-CR-690): tên, ghi chú, đang dùng
 * và bảng khoản sửa tại chỗ (dùng chung với khối 2 của trang kế hoạch). Mẫu không chứa lương ai nên
 * mọi ô tiền (trần, số tiền) luôn hiện. Nhân bản = tạo bản sao rồi mở luôn bản sao.
 */
export function HrCostTemplateDetailPage() {
  const { id } = useParams<{ id: string }>()
  const templateId = Number(id) || 0
  const isNew = templateId <= 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()
  const { data: template, isLoading } = useHrCostTemplate(templateId)
  const groups = useHrCostGroups().data?.items ?? []
  const positions = (useJobPositions(can('job_position', 'read')).data?.items ?? []).map((p) => ({ id: p.id, name: p.name }))
  const save = useSaveHrCostTemplate()
  const duplicate = useDuplicateHrCostTemplate()
  const remove = useDeleteHrCostTemplate()
  const once = useSingleFlight()
  const readOnly = !can('headcount_plan', isNew ? 'create' : 'write')

  const [form, setForm] = useState<HrCostTemplatePayload>(() => toForm(isNew ? undefined : template))
  if (useHasChanged(template?.id ?? 0) && template && !isNew) setForm(toForm(template))

  const goBack = () => (location.key === 'default' ? navigate(appRoutes.hr.hrCostTemplates) : navigate(-1))

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải mẫu…</p>
      </PageContainer>
    )
  }
  if (!isNew && !template) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Không tìm thấy mẫu khoản chi phí này.</p>
      </PageContainer>
    )
  }

  const submit = () =>
    void once(async () => {
      if (!form.name.trim()) return void toast.error('Đặt tên mẫu trước khi lưu.')
      const saved = await save.mutateAsync({
        id: templateId,
        payload: {
          name: form.name.trim(),
          note: form.note.trim(),
          is_active: form.is_active,
          //  Mẫu không chứa lương ai: ô tiền luôn gửi số thật. Bỏ `id` của khoản — schema `extra="forbid"`.
          items: form.items.map((i) => toCostItemPayload(i, true)),
        },
      })
      if (isNew) navigate(appRoutes.hr.hrCostTemplateDetail(saved.id), { replace: true })
    })
  const cloneTemplate = () =>
    void once(async () => {
      const copy = await duplicate.mutateAsync(templateId)
      navigate(appRoutes.hr.hrCostTemplateDetail(copy.id))
    })

  return (
    <PageContainer>
      <PageHeader
        sticky
        leading={
          <Button variant="outline" size="icon" title="Về danh sách" aria-label="Về danh sách" onClick={goBack}>
            <ArrowLeft className="size-4" />
          </Button>
        }
        title={isNew ? 'Thêm mẫu khoản chi phí' : template?.name}
        description="Kế hoạch lập từ mẫu này được CHÉP bộ khoản lúc tạo; sửa mẫu không làm đổi kế hoạch đã lập."
        actions={
          <>
            {!isNew && can('headcount_plan', 'create') && (
              <Button type="button" variant="outline" onClick={cloneTemplate} disabled={duplicate.isPending}>
                <Copy className="size-4" />
                Nhân bản mẫu
              </Button>
            )}
            {!isNew && can('headcount_plan', 'delete') && (
              <DeleteConfirmButton
                recordName={`mẫu «${template?.name ?? ''}»`}
                warning="Kế hoạch đã lập từ mẫu này vẫn giữ nguyên bộ khoản đã chép."
                pending={remove.isPending}
                onConfirm={async () => {
                  await remove.mutateAsync(templateId)
                  navigate(appRoutes.hr.hrCostTemplates, { replace: true })
                }}
              />
            )}
            {!readOnly && (
              <Button type="button" onClick={submit} disabled={save.isPending}>
                <Save className="size-4" />
                {isNew ? 'Tạo mẫu' : 'Lưu'}
              </Button>
            )}
          </>
        }
      />
      <div className="space-y-4">
        <FormCard title="Thông tin mẫu" icon={FileText} contentClassName="grid items-start gap-x-4 gap-y-3 sm:grid-cols-2">
          <PlanLabeledField label="Tên mẫu" htmlFor="tpl-name" required>
            {readOnly ? (
              <ReadOnlyValue>{form.name}</ReadOnlyValue>
            ) : (
              <Input id="tpl-name" value={form.name} maxLength={150} placeholder="Ví dụ: Mẫu văn phòng" onChange={(e) => setForm({ ...form, name: e.target.value })} />
            )}
          </PlanLabeledField>
          <PlanLabeledField label="Đang dùng" htmlFor="tpl-active" hint="Mẫu ngừng dùng không hiện ở ô chọn mẫu khi lập kế hoạch.">
            <Switch id="tpl-active" checked={form.is_active} disabled={readOnly} onCheckedChange={(is_active) => setForm({ ...form, is_active })} />
          </PlanLabeledField>
          <PlanLabeledField label="Ghi chú" htmlFor="tpl-note" fullWidth>
            {readOnly ? (
              <ReadOnlyValue multiline>{form.note}</ReadOnlyValue>
            ) : (
              <Textarea id="tpl-note" value={form.note} maxLength={500} onChange={(e) => setForm({ ...form, note: e.target.value })} />
            )}
          </PlanLabeledField>
        </FormCard>
        <FormCard title="Khoản chi phí của mẫu" icon={ListChecks}>
          <HrCostItemsEditor
            items={form.items}
            onChange={({ items }) => setForm({ ...form, items })}
            groups={groups}
            positions={positions}
            showMoney
            readOnly={readOnly}
            storageKey="hr.hr-cost-template.items"
          />
        </FormCard>
      </div>
    </PageContainer>
  )
}
