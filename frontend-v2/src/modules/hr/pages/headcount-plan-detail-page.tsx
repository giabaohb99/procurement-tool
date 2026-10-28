import { ArrowLeft, CalendarRange, Calculator, ListChecks, Save, Users } from 'lucide-react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { FormCard } from '@/shared/ui/form-card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { HeadcountPlanAttachments } from '../components/headcount-plan-attachments'
import { HeadcountPlanBasisFields } from '../components/headcount-plan-basis-fields'
import { HeadcountPlanComputedTable } from '../components/headcount-plan-computed-table'
import { HeadcountPlanFileActions } from '../components/headcount-plan-file-actions'
import { HeadcountPlanLinesEditor } from '../components/headcount-plan-lines-editor'
import { HeadcountPlanPeriodFields } from '../components/headcount-plan-period-fields'
import { HrCostItemsEditor } from '../components/hr-cost-items-editor'
import { PayrollHiddenNotice } from '../components/payroll-hidden-notice'
import { useHeadcountPlanEditor } from '../hooks/use-headcount-plan-editor'
import { useHeadcountPlanLookups } from '../hooks/use-headcount-plan-lookups'
import { useDeleteHeadcountPlan } from '../hooks/use-headcount-plans'
import { formatPeriodLabel } from '../utils/headcount-plan-periods'

/**
 * TRANG KẾ HOẠCH NHÂN SỰ `/hr/headcount-plans/new` · `/:id` (duoc-CR-690) — bốn khối theo §2 tài
 * liệu 06: Kỳ & căn cứ · Khoản chi phí · Định biên theo vị trí · Hệ thống tự tính. Form dài nên là
 * TRANG RIÊNG, không hộp thoại. Mọi trạng thái nằm ở `useHeadcountPlanEditor`.
 */
export function HeadcountPlanDetailPage() {
  const { id } = useParams<{ id: string }>()
  const planId = Number(id) || 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()
  const year = new Date().getFullYear()
  const ed = useHeadcountPlanEditor(planId, year)
  const lookups = useHeadcountPlanLookups(ed.isNew, year)
  const remove = useDeleteHeadcountPlan()
  const { draft } = ed
  const periodLabel = formatPeriodLabel(draft.period_type, draft.period_no, draft.year)

  //  «Về danh sách» lùi theo lịch sử để giữ bộ lọc; vào thẳng từ link thì về danh sách.
  const goBack = () => (location.key === 'default' ? navigate(appRoutes.hr.headcountPlans) : navigate(-1))

  if (ed.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải kế hoạch…</p>
      </PageContainer>
    )
  }
  if (ed.notFound) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">
          Không tìm thấy kế hoạch này, hoặc nó nằm ngoài phạm vi dữ liệu của bạn.
        </p>
      </PageContainer>
    )
  }

  const costReadOnly = ed.readOnly || !ed.canSeeMoney
  const save = () =>
    void ed.submit((savedId) => {
      if (ed.isNew) navigate(appRoutes.hr.headcountPlanDetail(savedId), { replace: true })
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
        title={ed.isNew ? 'Lập kế hoạch nhân sự' : `Kế hoạch ${periodLabel}`}
        description={
          ed.isNew
            ? 'Chọn kỳ, pháp nhân, phòng và mẫu khoản chi phí; nhập định biên theo vị trí — bảng chi phí tự tính bên dưới.'
            : [ed.detail?.company_name, ed.detail?.department_name].filter(Boolean).join(' · ')
        }
        actions={
          <>
            {!ed.isNew && (
              <HeadcountPlanFileActions
                planId={planId}
                exportName={`ke-hoach-nhan-su-${periodLabel.replace('/', '-')}.xlsx`}
                onImported={() => void ed.reload()}
              />
            )}
            {!ed.isNew && can('headcount_plan', 'delete') && (
              <DeleteConfirmButton
                recordName={`kế hoạch ${periodLabel}`}
                warning="Xóa rồi thì báo cáo định biên và quỹ lương coi pháp nhân × phòng này là «chưa có kế hoạch» cho kỳ đó."
                pending={remove.isPending}
                onConfirm={async () => {
                  await remove.mutateAsync(planId)
                  navigate(appRoutes.hr.headcountPlans, { replace: true })
                }}
              />
            )}
            {!ed.readOnly && (
              <Button type="button" onClick={save} disabled={ed.saving}>
                <Save className="size-4" />
                {ed.isNew ? 'Tạo kế hoạch' : 'Lưu'}
              </Button>
            )}
          </>
        }
      />

      <div className="space-y-4">
        <FormCard title="Kỳ và căn cứ" icon={CalendarRange} contentClassName="grid items-start gap-x-4 gap-y-3 sm:grid-cols-2">
          <HeadcountPlanPeriodFields
            draft={draft}
            isNew={ed.isNew}
            readOnly={ed.readOnly}
            yearOptions={lookups.yearOptions}
            companyOptions={lookups.companyOptions}
            departmentOptions={lookups.departmentOptions}
            templateOptions={lookups.templateOptions}
            savedNames={{ company: ed.detail?.company_name, department: ed.detail?.department_name }}
            onPatch={ed.patch}
            onPeriodChange={ed.changePeriod}
            onTemplateChange={(tid) => void ed.chooseTemplate(tid)}
          />
          <HeadcountPlanBasisFields
            draft={draft}
            readOnly={ed.readOnly}
            approverOptions={lookups.approverOptions}
            approverName={ed.detail?.approver_name}
            canSearchDocuments={can('document', 'read')}
            onPatch={ed.patch}
            onDocumentsChange={(documents) => ed.patch({ documents })}
          />
        </FormCard>

        <HeadcountPlanAttachments planId={planId} hidden={Boolean(ed.detail?.files_hidden)} canManage={!ed.readOnly} />

        {!ed.canSeeMoney && <PayrollHiddenNotice />}

        <FormCard title="Khoản chi phí của kế hoạch này" icon={ListChecks}>
          <p className="mb-2 text-xs text-muted-foreground">
            Bộ khoản đã chép từ mẫu. Thêm, bớt khoản hay đổi tỷ lệ ở đây chỉ áp cho kế hoạch này — mẫu và kế hoạch
            khác không đổi.
          </p>
          {draft.skipped_items.length > 0 && (
            <p className="mb-2 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
              Không chép từ mẫu vì mọi tháng rơi vào nằm ngoài kỳ {periodLabel}: {draft.skipped_items.join(', ')}.
            </p>
          )}
          <HrCostItemsEditor
            items={draft.cost_items}
            lines={draft.lines}
            onChange={({ items, lines }) => ed.changeCostItems(items, lines)}
            groups={lookups.groups}
            positions={lookups.positions}
            periodMonths={ed.periodMonths}
            showMoney={ed.canSeeMoney}
            readOnly={costReadOnly}
            storageKey="hr.headcount-plan.cost-items"
            serverError={ed.computeError}
          />
        </FormCard>

        <FormCard title="Định biên theo vị trí" icon={Users}>
          <HeadcountPlanLinesEditor
            lines={draft.lines}
            periods={ed.periods}
            periodType={draft.period_type}
            items={draft.cost_items}
            stats={ed.stats}
            positions={lookups.positions}
            showMoney={ed.canSeeMoney}
            readOnly={ed.readOnly}
            onChange={(lines) => ed.patch({ lines })}
            onAdd={ed.addLine}
          />
        </FormCard>

        <FormCard title="Hệ thống tự tính" icon={Calculator}>
          {!draft.company_id ? (
            <p className="text-sm text-muted-foreground">Chọn pháp nhân để hệ thống tính chi phí theo kỳ.</p>
          ) : (
            <HeadcountPlanComputedTable
              computed={ed.compute.data ?? ed.detail?.computed}
              periods={ed.periods}
              showMoney={ed.canSeeMoney}
              isFetching={ed.compute.isFetching}
              actual={ed.actual}
              notes={ed.actualNotes}
            />
          )}
        </FormCard>
      </div>
    </PageContainer>
  )
}
