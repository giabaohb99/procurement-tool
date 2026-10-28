import { Banknote, CalendarDays, Users } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig, CrudOption } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { HEADCOUNT_PLAN_API_PATH } from '../api/headcount-plan-api'
import { HeadcountPlanCsvActions } from '../components/headcount-plan-csv-actions'
import { PLAN_PERIOD_TYPE } from '@/shared/constants/statuses'
import { WHOLE_COMPANY_LABEL, type HeadcountPlanListItem } from '../types/headcount-plan'
import { formatPeriodLabel } from '../utils/headcount-plan-periods'

export interface HeadcountPlanCrudOptions {
  /** `can('labor_contract','read')` — có thì mới dựng cột «Tổng chi phí». */
  canSeePayroll: boolean
  yearOptions: CrudOption[]
  companyOptions: CrudOption[]
  departmentOptions: CrudOption[]
}

const COST_HEADER = 'Tổng chi phí'

const periodOf = (r: HeadcountPlanListItem) => formatPeriodLabel(r.period_type, r.period_no, r.year)
const basisOf = (r: HeadcountPlanListItem) =>
  [r.basis_no, r.basis_date ? formatDate(r.basis_date) : ''].filter(Boolean).join(' · ')

/**
 * Cột của danh sách kế hoạch — tách ra để bài kiểm canh cột tiền. Cột «Tổng chi phí» chỉ dựng khi
 * người xem có `labor_contract.read`; có quyền mà bị che ở pháp nhân này thì ô hiện gạch (backend
 * trả `null`), KHÔNG hiện 0 — 0 đọc ra «kế hoạch không tốn đồng nào».
 */
export function buildHeadcountPlanColumns(canSeePayroll: boolean): DataTableColumn<HeadcountPlanListItem>[] {
  return [
    {
      key: 'period',
      header: 'Kỳ',
      width: 110,
      hideable: false,
      cell: (r) => <span className="font-semibold tabular-nums text-primary">{periodOf(r)}</span>,
    },
    { key: 'company_name', header: 'Pháp nhân', width: 240, wrap: true, cell: (r) => r.company_name || `#${r.company_id}` },
    {
      key: 'department_name',
      header: 'Phòng ban',
      width: 220,
      wrap: true,
      hideable: false,
      cell: (r) =>
        r.department_id ? (
          r.department_name || `#${r.department_id}`
        ) : (
          <span className="font-medium">{r.department_name || WHOLE_COMPANY_LABEL}</span>
        ),
    },
    {
      key: 'headcount_end',
      header: 'Số người cuối kỳ',
      width: 140,
      align: 'right',
      cell: (r) => <span className="tabular-nums">{r.headcount_end ?? 0}</span>,
    },
    ...(canSeePayroll
      ? [
          {
            key: 'total_cost',
            header: COST_HEADER,
            width: 170,
            align: 'right' as const,
            cell: (r: HeadcountPlanListItem) =>
              r.total_cost == null ? (
                <span className="text-muted-foreground/50" title="Bạn không được xem lương của pháp nhân này">
                  —
                </span>
              ) : (
                <span className="tabular-nums">{formatMoney(r.total_cost)}</span>
              ),
          },
        ]
      : []),
    { key: 'basis', header: 'Căn cứ', width: 200, wrap: true, cell: basisOf },
    { key: 'note', header: 'Lý do / ghi chú', width: 260, minWidth: 160, wrap: true, defaultHidden: true, cell: (r) => r.note || '' },
  ]
}

/**
 * KẾ HOẠCH NHÂN SỰ THEO KỲ (duoc-CR-690) — danh sách lọc Năm · Loại kỳ · Pháp nhân · Phòng. Thêm /
 * mở là TRANG RIÊNG (`createRoute` + `detailRoute`): kế hoạch có bốn khối, hộp thoại không chứa nổi.
 * Báo cáo «Số người kế hoạch so với thực tế» và «Quỹ lương theo pháp nhân» đọc từ đây.
 *
 * Dựng bằng HÀM vì hai thứ chỉ biết lúc chạy: quyền xem lương và danh mục pháp nhân / phòng.
 */
export function buildHeadcountPlanCrudConfig(opts: HeadcountPlanCrudOptions): CrudConfig<HeadcountPlanListItem> {
  return {
    entity: 'headcount_plan',
    title: 'Kế hoạch nhân sự',
    description:
      'Số người kế hoạch theo vị trí và chi phí nhân sự theo kỳ (năm, bán niên, quý, tháng) của từng pháp nhân, phòng ban.',
    unitLabel: 'kế hoạch',
    apiPath: HEADCOUNT_PLAN_API_PATH,
    storageKey: 'hr.headcount-plans.v2',
    listRoute: appRoutes.hr.headcountPlans,
    createRoute: appRoutes.hr.headcountPlanNew,
    detailRoute: (id) => appRoutes.hr.headcountPlanDetail(id),
    //  API chỉ lọc năm / loại kỳ / pháp nhân / phòng và tự sắp: không có ô tìm chữ.
    hideSearch: true,
    quickFilters: [
      { key: 'year', label: 'Năm', type: 'select', options: opts.yearOptions },
      {
        key: 'period_type',
        label: 'Loại kỳ',
        type: 'select',
        options: PLAN_PERIOD_TYPE.map((o) => ({ value: o.value, label: o.label })),
      },
      { key: 'company_id', label: 'Pháp nhân', type: 'select', options: opts.companyOptions },
      { key: 'department_id', label: 'Phòng ban', type: 'select', options: opts.departmentOptions },
    ],
    getItemName: (r) => `${periodOf(r)} · ${r.company_name} · ${r.department_name}`,
    deleteWarning: 'Xóa rồi thì báo cáo số người kế hoạch và quỹ lương coi pháp nhân × phòng này là «chưa có kế hoạch» cho kỳ đó.',
    renderToolbarExtra: () => <HeadcountPlanCsvActions />,
    mobileCard: (r) => (
      <CrudRecordCard
        title={r.department_name || WHOLE_COMPANY_LABEL}
        subtitle={<span className="block truncate">{r.company_name}</span>}
        chips={[
          { icon: CalendarDays, text: periodOf(r), tone: 'code' },
          { icon: Users, text: `${r.headcount_end ?? 0} người`, tone: 'ok' },
          ...(opts.canSeePayroll && r.total_cost
            ? [{ icon: Banknote, text: `${formatMoney(r.total_cost)} đ`, tone: 'muted' as const }]
            : []),
        ]}
      />
    ),
    columns: buildHeadcountPlanColumns(opts.canSeePayroll),
    //  Thêm / sửa ở trang riêng — khung CRUD không dựng hộp thoại nào cho màn này.
    formFields: [],
  }
}
