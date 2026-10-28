import { Banknote, CalendarDays, Users } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig, CrudFormField, CrudOption } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import type { DataTableColumn } from '@/shared/data-table'
import { formatMoney } from '@/shared/utils/format-money'
import { HeadcountPlanCsvActions } from '../components/headcount-plan-csv-actions'
import { HEADCOUNT_PLAN_API_PATH } from '../api/headcount-plan-api'
import type { HeadcountPlan } from '../types/headcount-plan'
import { buildHeadcountPlanDepartmentOptions, normalizeHeadcountPlanPayload } from '../utils/headcount-plan-options'

interface DepartmentLike {
  id: number
  name: string
}

export interface HeadcountPlanCrudOptions {
  /** `can('labor_contract','read')` — có thì mới có cột + ô «Quỹ lương kế hoạch / tháng». */
  canSeePayroll: boolean
  yearOptions: CrudOption[]
  companyOptions: CrudOption[]
  departments: readonly DepartmentLike[]
  /** Năm mặc định khi THÊM mới. */
  defaultYear: number
}

const PAYROLL_HEADER = 'Quỹ lương KH / tháng'

/**
 * Cột của bảng — tách ra để có bài kiểm canh cột lương. Cột tiền chỉ dựng khi người xem có
 * `labor_contract.read`; backend đã che số (`null`) cho người thiếu quyền, nhưng một cột toàn
 * «—» thì người đọc tưởng chưa ai khai quỹ lương.
 */
export function buildHeadcountPlanColumns(canSeePayroll: boolean): DataTableColumn<HeadcountPlan>[] {
  return [
    {
      key: 'year',
      header: 'Năm',
      width: 80,
      hideable: false,
      cell: (r) => <span className="font-semibold tabular-nums text-primary">{r.year}</span>,
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
          <span className="font-medium">{r.department_name || 'Toàn pháp nhân'}</span>
        ),
    },
    {
      key: 'planned_headcount',
      header: 'Định biên kế hoạch',
      width: 150,
      align: 'right',
      cell: (r) => <span className="tabular-nums">{r.planned_headcount}</span>,
    },
    ...(canSeePayroll
      ? [
          {
            key: 'planned_payroll_monthly',
            header: PAYROLL_HEADER,
            width: 180,
            align: 'right' as const,
            cell: (r: HeadcountPlan) =>
              r.planned_payroll_monthly == null ? (
                <span className="text-muted-foreground/50">—</span>
              ) : (
                <span className="tabular-nums">{formatMoney(r.planned_payroll_monthly)}</span>
              ),
          },
        ]
      : []),
    { key: 'note', header: 'Ghi chú', width: 260, minWidth: 160, wrap: true, cell: (r) => r.note || '' },
  ]
}

/** Ô nhập — ô tiền chỉ có khi người xem đọc được hợp đồng lao động. */
export function buildHeadcountPlanFormFields(
  opts: Pick<HeadcountPlanCrudOptions, 'canSeePayroll' | 'yearOptions' | 'companyOptions' | 'departments' | 'defaultYear'>,
): CrudFormField[] {
  const fields: CrudFormField[] = [
    {
      name: 'year',
      label: 'Năm',
      type: 'select',
      required: true,
      readonlyOnEdit: true,
      options: opts.yearOptions,
      defaultValue: String(opts.defaultYear),
    },
    {
      name: 'company_id',
      label: 'Pháp nhân',
      type: 'select',
      required: true,
      readonlyOnEdit: true,
      options: opts.companyOptions,
    },
    {
      name: 'department_id',
      label: 'Phòng ban',
      type: 'select',
      readonlyOnEdit: true,
      options: buildHeadcountPlanDepartmentOptions(opts.departments),
      defaultValue: '0',
      hint: '«Toàn pháp nhân» = định biên của cả pháp nhân, so với tổng người của pháp nhân (không cộng với các dòng phòng). Phòng ban dùng chung cho mọi pháp nhân.',
    },
    {
      name: 'planned_headcount',
      label: 'Định biên kế hoạch (người)',
      type: 'number',
      required: true,
    },
  ]
  if (opts.canSeePayroll) {
    fields.push({
      name: 'planned_payroll_monthly',
      label: 'Quỹ lương kế hoạch / tháng (đồng)',
      type: 'number',
      hint: 'Lương + phụ cấp của cả nhóm trong một tháng. Để 0 nếu chưa lập.',
    })
  }
  fields.push({ name: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true })
  return fields
}

/**
 * KẾ HOẠCH NHÂN SỰ theo năm (duoc-CR-689) — mỗi dòng là định biên + quỹ lương kế hoạch / tháng
 * của một pháp nhân × phòng trong một năm. Báo cáo «Định biên kế hoạch so với thực tế» (khóa 25)
 * và cột kế hoạch của «Quỹ lương theo pháp nhân» đọc từ đây.
 *
 * Dựng bằng HÀM (không phải hằng) vì hai thứ chỉ biết lúc chạy: quyền xem lương (cột + ô tiền) và
 * danh mục pháp nhân / phòng (ô chọn và ô lọc). Sửa bằng hộp thoại ngay trên
 * danh sách — form sáu ô, không đáng một trang riêng.
 *
 * ⚠️ Năm / pháp nhân / phòng là KHÓA của dòng (backend UNIQUE) nên khóa lại khi sửa: đổi khóa
 * của một dòng là chuyển kế hoạch sang phòng khác mà lịch sử vẫn ghi «sửa».
 */
export function buildHeadcountPlanCrudConfig(opts: HeadcountPlanCrudOptions): CrudConfig<HeadcountPlan> {
  const departmentOptions = buildHeadcountPlanDepartmentOptions(opts.departments)
  return {
    entity: 'headcount_plan',
    title: 'Kế hoạch nhân sự',
    description:
      'Định biên và quỹ lương kế hoạch theo năm của từng pháp nhân, phòng ban — nguồn của báo cáo «Định biên kế hoạch so với thực tế».',
    unitLabel: 'dòng kế hoạch',
    apiPath: HEADCOUNT_PLAN_API_PATH,
    storageKey: 'hr.headcount-plans',
    listRoute: appRoutes.hr.headcountPlans,
    openFormOnRowClick: true,
    deleteInForm: true,
    dialogMaxWidth: 'sm:max-w-xl',
    //  API chỉ lọc năm / pháp nhân / phòng và tự sắp (năm mới trước → pháp nhân → phòng): không
    //  có ô tìm chữ, cột không bấm sắp xếp được — bày ra thì bấm mà bảng đứng im.
    hideSearch: true,
    quickFilters: [
      { key: 'year', label: 'Năm', type: 'select', options: opts.yearOptions },
      { key: 'company_id', label: 'Pháp nhân', type: 'select', options: opts.companyOptions },
      { key: 'department_id', label: 'Phòng ban', type: 'select', options: departmentOptions },
    ],
    getItemName: (r) => `${r.year} · ${r.company_name} · ${r.department_name}`,
    deleteWarning: 'Xóa rồi thì báo cáo định biên năm đó coi phòng này là «chưa có kế hoạch».',
    renderToolbarExtra: () => <HeadcountPlanCsvActions />,
    mobileCard: (r) => (
      <CrudRecordCard
        title={r.department_name || 'Toàn pháp nhân'}
        subtitle={<span className="block truncate">{r.company_name}</span>}
        chips={[
          { icon: CalendarDays, text: String(r.year), tone: 'code' },
          { icon: Users, text: `${r.planned_headcount} người`, tone: 'ok' },
          ...(opts.canSeePayroll && r.planned_payroll_monthly
            ? [{ icon: Banknote, text: `${formatMoney(r.planned_payroll_monthly)} đ/tháng`, tone: 'muted' as const }]
            : []),
        ]}
      />
    ),
    columns: buildHeadcountPlanColumns(opts.canSeePayroll),
    formFields: buildHeadcountPlanFormFields(opts),
    buildPayload: (payload) => normalizeHeadcountPlanPayload(payload),
  }
}

