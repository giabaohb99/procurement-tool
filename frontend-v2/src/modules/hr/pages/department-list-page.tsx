import { Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { ConditionalFilter, FilterProvider, useFilterQuery } from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { DepartmentFormDialog } from '../components/department-form-dialog'
import { DEPARTMENT_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import {
  DEPARTMENT_KIND_LABELS,
  DEPARTMENT_KIND_OPTIONS,
  type Department,
} from '../types/department'

const ALL = 'all'

/** `preserveParams`: giữ ba select của thanh công cụ trên URL khi áp bộ lọc nâng cao. */
const FILTER_CONFIG = {
  fields: DEPARTMENT_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['is_active', 'kind', 'company_id'],
}

export function DepartmentListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <DepartmentListContent />
    </FilterProvider>
  )
}

/**
 * Danh mục phòng ban.
 *
 * Thanh công cụ giữ ô tìm chung + select Trạng thái. Mã / Tên phòng ban với đầy
 * đủ phép so sánh nằm ở "Bộ lọc" nâng cao.
 */
function DepartmentListContent() {
  const navigate = useNavigate()

  const { can } = usePermission()
  //  Ô chọn Pháp nhân mượn danh mục của phân hệ khác (`company.read`). Thiếu
  //  quyền là cứ mount lên gọi API rồi ăn toast 403 chẳng liên quan gì tới việc
  //  đang làm — nên vừa tắt query vừa giấu luôn ô chọn.
  const canReadCompany = can('company', 'read')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [kind, setKind] = useUrlParamState('kind', ALL)
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isFormOpen, setFormOpen] = useState(false)

  const { data: companies } = useCompanies({ page_size: 500 }, { enabled: canReadCompany })
  const { queryParams, queryKey } = useFilterQuery()

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    active,
    kind,
    companyId,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  // `q` là tham số RIÊNG của endpoint này: khớp tên phòng ban HOẶC tên trưởng
  // bộ phận (join sang bảng nhân sự). Không phải cột trong whitelist filter.
  if (debouncedValue) params.q = debouncedValue
  if (active !== ALL) params.is_active = active === 'true'
  if (kind !== ALL) params.kind = Number(kind)
  if (companyId !== ALL) params.company_id = Number(companyId)

  const { data, isLoading, isError } = useDepartments(params)

  const columns = useMemo<DataTableColumn<Department>[]>(
    () => [
      { key: 'code', header: 'Mã', width: 150, cell: (d) => d.code },
      {
        key: 'issue_code',
        header: 'Mã số hiệu',
        width: 140,
        cell: (d) => d.issue_code || '—',
      },
      {
        key: 'name',
        header: 'Phòng ban',
        width: 300,
        hideable: false,
        cell: (d) => <span className="truncate">{d.name}</span>,
      },
      {
        key: 'kind',
        header: 'Loại đơn vị',
        width: 230,
        cell: (d) => DEPARTMENT_KIND_LABELS[d.kind],
      },
      {
        key: 'manager_name',
        header: 'Trưởng bộ phận',
        width: 260,
        cell: (d) => d.manager_name || '—',
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 140,
        cell: (d) => (
          <Badge variant={d.is_active ? 'default' : 'secondary'}>
            {d.is_active ? 'Hoạt động' : 'Đã ẩn'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phòng ban"
        description="Cơ cấu tổ chức và trưởng bộ phận của từng phòng."
        actions={
          <PermissionGate entity="department" action="create">
            <Button onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(department) => department.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy phòng ban nào."
          storageKey="hr.departments"
          onRowClick={(d) => navigate(appRoutes.hr.departmentDetail(d.id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phòng ban',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-sm">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo tên phòng ban hoặc trưởng bộ phận…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={kind} onValueChange={setKind}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Loại đơn vị" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả loại đơn vị</SelectItem>
                  {DEPARTMENT_KIND_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {canReadCompany && (
                <Select value={companyId} onValueChange={setCompanyId}>
                  <SelectTrigger className="w-52">
                    <SelectValue placeholder="Pháp nhân" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Tất cả pháp nhân</SelectItem>
                    {(companies?.items ?? []).map((company) => (
                      <SelectItem key={company.id} value={String(company.id)}>
                        {company.short_name || company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <Select value={active} onValueChange={setActive}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  <SelectItem value="true">Hoạt động</SelectItem>
                  <SelectItem value="false">Đã ẩn</SelectItem>
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>

      <DepartmentFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
