import { ArrowLeft, CalendarRange, Calculator, Gift, Save, Users } from 'lucide-react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { PLAN_PERIOD_TYPE_CODE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { FormCard } from '@/shared/ui/form-card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { HeadcountPlanBasisFields } from '../components/headcount-plan-basis-fields'
import { HeadcountPlanComputedTable } from '../components/headcount-plan-computed-table'
import { HeadcountPlanFileActions } from '../components/headcount-plan-file-actions'
import { HeadcountPlanLinesEditor } from '../components/headcount-plan-lines-editor'
import { HeadcountPlanPeriodFields } from '../components/headcount-plan-period-fields'
import { HeadcountPlanOtherCosts } from '../components/headcount-plan-other-costs'
import { PayrollHiddenNotice } from '../components/payroll-hidden-notice'
import { useHeadcountPlanEditor } from '../hooks/use-headcount-plan-editor'
import { useHeadcountPlanLookups } from '../hooks/use-headcount-plan-lookups'
import { useDeleteHeadcountPlan } from '../hooks/use-headcount-plans'
import { sumLineHeadcounts } from '../utils/headcount-plan-cost-buckets'
import { formatPeriodLabel } from '../utils/headcount-plan-periods'

/**
 * TRANG KẾ HOẠCH NHÂN SỰ `/hr/headcount-plans/new` · `/:id` (duoc-CR-690) — bố cục đại ca chốt
 * 28/10/2026: Kỳ và căn cứ · ① Người và lương · ② Chi phí khác · ③ Tổng (tự tính). Không còn khái niệm
 * «khoản chi phí / cách tính / mẫu / mã / nhóm» trên form. Form dài nên là TRANG RIÊNG, không hộp thoại.
 * Mọi trạng thái nằm ở `useHeadcountPlanEditor`.
 */
export function HeadcountPlanDetailPage() {
  const { id } = useParams<{ id: string }>()
  const planId = Number(id) || 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()
  const year = new Date().getFullYear()
  const ed = useHeadcountPlanEditor(planId, year)
  const lookups = useHeadcountPlanLookups(year)
  const remove = useDeleteHeadcountPlan()
  const { draft } = ed
  const periodLabel = formatPeriodLabel(draft.period_type, draft.period_no, draft.year)
  const isYear = draft.period_type === PLAN_PERIOD_TYPE_CODE.YEAR

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
            ? 'Chọn kỳ, pháp nhân và phòng; nhập số người và lương theo vị trí — bảng Tổng tự tính bên dưới.'
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
                warning="Xóa rồi thì báo cáo số người kế hoạch và quỹ lương coi pháp nhân × phòng này là «chưa có kế hoạch» cho kỳ đó."
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
            savedNames={{ company: ed.detail?.company_name, department: ed.detail?.department_name }}
            onPatch={ed.patch}
            onPeriodChange={ed.changePeriod}
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

        {!ed.canSeeMoney && <PayrollHiddenNotice />}

        <FormCard title="Người và lương" icon={Users}>
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

        <FormCard title="Chi phí khác" icon={Gift}>
          <HeadcountPlanOtherCosts
            items={draft.cost_items}
            onChange={ed.changeCostItems}
            groups={lookups.groups}
            positions={lookups.positions}
            periodMonths={ed.periodMonths}
            periodLabel={periodLabel}
            skipped={draft.skipped_items}
            showMoney={ed.canSeeMoney}
            readOnly={ed.readOnly}
            //  Backend chặn 403 khi người không xem được lương đổi chi phí — nói lý do thay vì để họ sửa rồi ăn lỗi.
            lockedReason={ed.canSeeMoney ? undefined : 'Cần quyền xem lương của pháp nhân này để sửa chi phí.'}
            serverError={ed.computeError}
          />
        </FormCard>

        <FormCard title="Tổng (tự tính)" icon={Calculator}>
          {!draft.company_id && (
            <p className="mb-2 text-sm text-muted-foreground">Chọn pháp nhân để hệ thống tính tiền theo kỳ.</p>
          )}
          <HeadcountPlanComputedTable
            computed={draft.company_id ? (ed.compute.data ?? ed.detail?.computed) : null}
            periods={ed.periods}
            totalLabel={isYear ? 'Cả năm' : 'Tổng kỳ'}
            costItems={draft.cost_items}
            headcounts={sumLineHeadcounts(draft.lines, ed.periods.length)}
            showMoney={ed.canSeeMoney}
            isFetching={ed.compute.isFetching}
            actual={ed.actual}
            notes={ed.actualNotes}
          />
        </FormCard>
      </div>
    </PageContainer>
  )
}
