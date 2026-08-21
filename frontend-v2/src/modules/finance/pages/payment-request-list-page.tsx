import { Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
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
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PaymentRequestStatusBadge } from '../components/payment-request-status-badge'
import { usePaymentRequests } from '../hooks/use-payment-requests'
import {
  PAYMENT_METHOD_LABELS,
  PAYMENT_SOURCE_LABELS,
  paymentRequestStatusOptions,
  type PaymentRequestSummary,
} from '../types/payment-request'

const ALL = 'all'

/**
 * Danh sách Yêu cầu thanh toán (YCTT).
 *
 * Lối vào chính để LÊN phiếu là cột tick ở màn Công nợ (chọn nhiều khoản rồi
 * "Tạo đề nghị thanh toán"). Nút ở đây là lối phụ: mở FORM TRẮNG cho các khoản
 * chi không đi từ công nợ (CR-066).
 */
export function PaymentRequestListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [source, setSource] = useUrlParamState('source_type', ALL)
  const [method, setMethod] = useUrlParamState('payment_method', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    companyId,
    status,
    source,
    method,
  ])

  const filterParams: ListParams = {}
  if (debouncedValue) filterParams.code = debouncedValue
  if (companyId !== ALL) filterParams.company_id = Number(companyId)
  if (status !== ALL) filterParams.status = status
  if (source !== ALL) filterParams.source_type = source
  if (method !== ALL) filterParams.payment_method = method

  const { data, isLoading, isError } = usePaymentRequests({
    page,
    page_size: pageSize,
    ...filterParams,
  })

  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '—',
    [companies],
  )

  const columns = useMemo<DataTableColumn<PaymentRequestSummary>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 150,
        hideable: false,
        defaultPinned: true,
        cell: (r) => <span className="font-medium">{r.code || '—'}</span>,
      },
      {
        key: 'request_date',
        header: 'Ngày lập',
        width: 120,
        cell: (r) => formatDate(r.request_date) || '—',
      },
      {
        key: 'created_by_name',
        header: 'Người yêu cầu',
        width: 180,
        cell: (r) => r.created_by_name || '—',
      },
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 240,
        cell: (r) => (
          <span className="truncate" title={r.supplier_name || r.supplier_code}>
            {r.supplier_name || r.supplier_code || '—'}
          </span>
        ),
      },
      {
        key: 'source_type',
        header: 'Loại nợ',
        width: 120,
        cell: (r) => PAYMENT_SOURCE_LABELS[r.source_type] ?? r.source_type,
      },
      { key: 'company', header: 'Công ty', width: 200, cell: (r) => companyName(r.company_id) },
      {
        key: 'payment_method',
        header: 'Hình thức TT',
        width: 140,
        cell: (r) => PAYMENT_METHOD_LABELS[r.payment_method] ?? r.payment_method,
      },
      {
        key: 'total',
        header: 'Số tiền',
        width: 160,
        align: 'right',
        cell: (r) => <span className="font-semibold tabular-nums">{formatMoney(r.total)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 140,
        cell: (r) => <PaymentRequestStatusBadge status={r.status} />,
      },
    ],
    [companyName],
  )

  return (
    <PageContainer fill>
      <PageHeader
        title="Yêu cầu thanh toán"
        description="Đề nghị chi trả công nợ nhà cung cấp và đơn vị vận chuyển."
        actions={
          can('payment_request', 'create') ? (
            <Button asChild>
              <Link to={appRoutes.finance.paymentRequestNew}>
                <Plus />
                Tạo đề nghị thanh toán
              </Link>
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => navigate(appRoutes.finance.paymentRequestDetail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu thanh toán nào khớp bộ lọc."
          storageKey="finance.payment-requests"
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
                  placeholder="Tìm theo mã phiếu…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger className="w-48">
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
                  {paymentRequestStatusOptions().map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={source} onValueChange={setSource}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Loại nợ" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi loại nợ</SelectItem>
                  {Object.entries(PAYMENT_SOURCE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={method} onValueChange={setMethod}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Hình thức TT" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Mọi hình thức</SelectItem>
                  {Object.entries(PAYMENT_METHOD_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
