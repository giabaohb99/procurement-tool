import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { appConfig } from '@/core/config/app-config'
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
import { formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { DocumentStatusBadge, StatusBadge } from '../components/document-status-badge'
import { PURCHASE_ORDER_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseOrders } from '../hooks/use-purchase-documents'
import {
  PO_STATUS_LABELS,
  statusOptions,
  type PurchaseOrder,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: PURCHASE_ORDER_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['company_id', 'status', 'invoice_no'],
}

export function PurchaseOrderListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseOrderListContent />
    </FilterProvider>
  )
}

/**
 * Danh sách Đơn mua hàng (ĐMH).
 *
 * "Số hóa đơn" nằm ở thanh công cụ chứ không phải bộ lọc nâng cao: backend lọc
 * nó QUA BẢNG CON (dòng đơn hàng) nên không đi qua `apply_filters`.
 */
function PurchaseOrderListContent() {
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

  const { data, isLoading, isError } = usePurchaseOrders(params)

  const columns = useMemo<DataTableColumn<PurchaseOrder>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã ĐMH',
        width: 160,
        hideable: false,
        // 11 cột, cuộn ngang trên màn hẹp -> ghim mã đơn cho khỏi lạc dòng.
        defaultPinned: true,
        cell: (po) => <span className="truncate font-medium">{po.code}</span>,
      },
      {
        key: 'misa_code',
        header: 'Mã MISA',
        width: 130,
        defaultHidden: true,
        cell: (po) => po.misa_code || '—',
      },
      {
        key: 'created_at',
        header: 'Ngày đặt',
        width: 150,
        cell: (po) => formatDateTime(po.created_at) || '—',
      },
      {
        key: 'supplier',
        header: 'Nhà cung cấp',
        width: 240,
        cell: (po) => (
          <span className="truncate" title={po.supplier_name}>
            {po.supplier_name || po.supplier_code || '—'}
          </span>
        ),
      },
      { key: 'pr_code', header: 'Mã PYC', width: 140, cell: (po) => po.pr_code || '—' },
      { key: 'nspt', header: 'NSPT', width: 170, defaultHidden: true, cell: (po) => po.nspt || '—' },
      {
        key: 'amount',
        header: 'Tiền hàng',
        width: 150,
        align: 'right',
        cell: (po) => <span className="tabular-nums">{formatMoney(po.amount) || 0} đ</span>,
      },
      {
        key: 'is_urgent',
        header: 'Gấp',
        width: 80,
        cell: (po) =>
          po.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : (
            <span className="text-muted-foreground">—</span>
          ),
      },
      {
        key: 'document_status',
        header: 'Hồ sơ chứng từ',
        width: 200,
        cell: (po) => <DocumentStatusBadge status={po.document_status} />,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 170,
        cell: (po) => <StatusBadge status={po.status} labels={PO_STATUS_LABELS} />,
      },
      {
        key: 'note',
        header: 'Ghi chú',
        width: 220,
        defaultHidden: true,
        cell: (po) => (
          <span className="truncate" title={po.note}>
            {po.note || '—'}
          </span>
        ),
      },
    ],
    [],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Đơn mua hàng"
        description="Đơn đặt hàng gửi nhà cung cấp và tình trạng hồ sơ chứng từ."
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(po) => po.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy đơn mua hàng nào."
          storageKey="procurement.purchase-orders"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'đơn',
          }}
          toolbar={
            <>
              <div className="relative min-w-56 flex-1 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã ĐMH…"
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
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                  {statusOptions(PO_STATUS_LABELS).map((option) => (
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
