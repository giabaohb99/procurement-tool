import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
// Danh mục công ty do phân hệ Nhân sự quản lý nhưng dùng chung toàn hệ.
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { StatusBadge } from '../components/document-status-badge'
import { PURCHASE_REQUEST_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseRequests } from '../hooks/use-purchase-documents'
import {
  PR_STATUS_LABELS,
  statusOptions,
  type PurchaseRequest,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: PURCHASE_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  // Thiếu tên nào ở đây thì bấm "Áp dụng" bộ lọc nâng cao sẽ xóa mất select đó.
  preserveParams: ['company_id', 'status'],
}

export function PurchaseRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseRequestListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách Yêu cầu mua hàng (PYC).
 *
 * Thanh công cụ giữ ba thứ dùng hằng ngày: tìm theo mã, pháp nhân và trạng
 * thái. Người yêu cầu / bộ phận / ngày tháng / đơn gấp nằm trong "Bộ lọc".
 */
function PurchaseRequestListContent() {
  const navigate = useNavigate()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  useEffect(() => setPage(1), [queryKey, debouncedValue, companyId, status])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (status !== ALL) params.status = status

  const { data, isLoading, isError } = usePurchaseRequests(params)

  const columns = useMemo<DataTableColumn<PurchaseRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã PYC',
        // Rộng hơn các cột mã khác vì còn phải chứa huy hiệu "Có dòng hủy".
        width: 220,
        hideable: false,
        cell: (pr) => (
          <div className="flex items-center gap-1.5">
            <span className="truncate font-medium">{pr.code}</span>
            {/* Bản cũ tô đỏ cả dòng; ở đây dùng huy hiệu để không phá sọc bảng. */}
            {pr.has_cancelled_line && (
              <Badge
                variant="secondary"
                className="shrink-0 border-0 bg-destructive/10 text-destructive"
                title="Phiếu có ít nhất một dòng đã hủy"
              >
                Có dòng hủy
              </Badge>
            )}
          </div>
        ),
      },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 150,
        cell: (pr) => formatDateTime(pr.created_at) || '—',
      },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (pr) => pr.requester || '—' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (pr) => pr.department || '—' },
      {
        key: 'need_date',
        header: 'Cần hàng',
        width: 120,
        cell: (pr) => formatDate(pr.need_date) || '—',
      },
      {
        key: 'total',
        header: 'Tổng tiền',
        width: 140,
        align: 'right',
        cell: (pr) => <span className="tabular-nums">{formatMoney(pr.total) || 0} đ</span>,
      },
      {
        key: 'is_urgent',
        header: 'Gấp',
        width: 80,
        cell: (pr) =>
          pr.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        cell: (pr) => <StatusBadge status={pr.status} labels={PR_STATUS_LABELS} />,
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu mua hàng"
        description="Phiếu yêu cầu mua hàng (PYC) của các bộ phận."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(pr) => pr.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu mua hàng nào."
          storageKey="procurement.purchase-requests"
          onRowClick={(pr) => navigate(appRoutes.procurement.purchaseRequestDetail(pr.id))}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phiếu',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã PYC…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Công ty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả công ty</SelectItem>
                  {(companies?.items ?? []).map((company) => (
                    <SelectItem key={company.id} value={String(company.id)}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {statusOptions(PR_STATUS_LABELS).map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
