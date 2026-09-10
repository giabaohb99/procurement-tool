import { Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SearchSelect } from '@/shared/ui/search-select'
import { Switch } from '@/shared/ui/switch'
import { CompanyChips } from '../components/company-chips'
import { ClerkStatusBadge } from '../components/status-pill'
import { useSealClerks, useSyncSealClerks } from '../hooks/use-seal-clerks'
import type { SealClerkGroup } from '../types/seal-clerk'

const ALL = 'all'

export function SealClerkListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  //  Quản lý phân công dùng chung khóa quyền `seal_type` (cấu hình Duyệt dấu).
  const canManage = can('seal_type', 'create')
  const canReadCompany = can('company', 'read')
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true }, { enabled: canReadCompany })

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (companyId !== ALL) p.company_id = Number(companyId)
    return p
  }, [page, pageSize, debouncedValue, companyId])
  const { data, isLoading, isError } = useSealClerks(params)
  //  Bật/tắt "văn thư tổng" ngay tại dòng. (Xóa phân công đã chuyển sang trang chi tiết.)
  const sync = useSyncSealClerks()

  const columns = useMemo<DataTableColumn<SealClerkGroup>[]>(
    () => [
      {
        key: 'id',
        header: 'ID',
        width: 80,
        cell: (r) => <span className="tabular-nums text-muted-foreground">{r.employee_id}</span>,
      },
      {
        key: 'employee',
        header: 'Văn thư',
        minWidth: 220,
        cell: (r) => (
          <span className="font-medium">
            {r.employee_name || `#${r.employee_id}`}
            {r.employee_code ? (
              <span className="text-muted-foreground"> · {r.employee_code}</span>
            ) : null}
          </span>
        ),
      },
      {
        key: 'companies',
        header: 'Công ty phụ trách',
        minWidth: 360,
        wrap: true,
        cell: (r) => <CompanyChips companies={r.companies} />,
      },
      {
        key: 'is_head',
        header: 'Đa pháp nhân',
        width: 130,
        align: 'center',
        //  Công tắc bật/tắt "văn thư tổng" (phụ trách phiếu ĐA pháp nhân) ngay tại
        //  dòng — giữ nguyên danh sách công ty, chỉ lật cờ. Chặn nổi bọt kẻo mở chi tiết.
        cell: (r) => (
          <div className="flex justify-center" onClick={(e) => e.stopPropagation()}>
            <Switch
              checked={r.is_head}
              disabled={!canManage || sync.isPending}
              aria-label="Đa pháp nhân"
              onCheckedChange={(checked) =>
                sync.mutate({
                  employee_id: r.employee_id,
                  company_ids: r.companies.map((c) => c.id),
                  is_head: checked,
                })
              }
            />
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        align: 'center',
        cell: (r) => <ClerkStatusBadge status={r.status} label={r.status_label ?? undefined} />,
      },
    ],
    [canManage, sync],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Phân công văn thư"
        description="Mỗi văn thư một dòng. Chỉ định công ty họ phụ trách đóng dấu; phiếu cần dấu nhiều công ty do văn thư tổng phụ trách."
        actions={
          canManage ? (
            <Button onClick={() => navigate(appRoutes.approvalSeal.clerksNew)}>
              <Plus className="size-4" />
              Thêm phân công
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.employee_id}
          onRowClick={(r) => navigate(appRoutes.approvalSeal.clerkDetail(r.anchor_id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa phân công văn thư nào."
          storageKey="approval-seal.clerks"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'văn thư',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9 h-9 text-xs"
                  placeholder="Tìm theo tên/mã văn thư, công ty…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
              {canReadCompany && (
                <SearchSelect
                  value={companyId}
                  onChange={(v) => {
                    setCompanyId(v || ALL)
                    setPage(1)
                  }}
                  options={[
                    { value: ALL, label: 'Tất cả công ty' },
                    ...(companies?.items ?? []).map((c) => ({ value: String(c.id), label: c.name })),
                  ]}
                  placeholder="Lọc theo công ty"
                  searchPlaceholder="Tìm công ty…"
                  searchInTrigger
                  size="sm"
                  className="w-full md:w-56"
                />
              )}
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
