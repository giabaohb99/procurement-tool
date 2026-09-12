import { Plus, Search } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { useUrlSort } from '@/shared/hooks/use-url-sort'
import type { ListParams } from '@/shared/types/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PaymentRequestCard } from '../components/payment-request-card'
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
  // bao-CR-304 (ticket 26) — lọc theo mã MISA của ĐMH: phiếu không lưu mã nên
  // backend lọc subquery ba nhịp dòng phiếu -> mã PO -> ĐMH (filter_by_misa_code).
  const {
    value: misaKeyword,
    setValue: setMisaKeyword,
    debouncedValue: debouncedMisa,
  } = useUrlSearchParam('misa_code')
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [source, setSource] = useUrlParamState('source_type', ALL)
  const [method, setMethod] = useUrlParamState('payment_method', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  //  Mốc bóng đổ cho thanh công cụ ghim — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    debouncedMisa,
    companyId,
    status,
    source,
    method,
    sortBy,
    sortDir,
  ])

  const filterParams: ListParams = {}
  if (debouncedValue) filterParams.code = debouncedValue
  if (debouncedMisa) filterParams.misa_code = debouncedMisa
  if (companyId !== ALL) filterParams.company_id = Number(companyId)
  if (status !== ALL) filterParams.status = status
  if (source !== ALL) filterParams.source_type = source
  if (method !== ALL) filterParams.payment_method = method
  if (sortBy) {
    filterParams.sort_by = sortBy
    filterParams.sort_dir = sortDir
  }

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
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (r) => <span className="font-medium">{r.code || '—'}</span>,
      },
      {
        key: 'request_date',
        header: 'Ngày lập',
        width: 120,
        sortable: true,
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
      {
        // bao-CR-304 (ticket 26) — phiếu gồm nhiều PO nên mã MISA hiển thị gộp "MS1, MS2".
        key: 'misa_code',
        header: 'Mã MISA',
        width: 150,
        cell: (r) => r.misa_code || '—',
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
        sortable: true,
        cell: (r) => <PaymentRequestStatusBadge status={r.status} />,
      },
      {
        // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
        key: 'updated_at',
        header: 'Ngày cập nhật',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (r) => formatDateTime(r.updated_at) || '',
      },
    ],
    [companyName],
  )

  //  Năm ô lọc dọn vào tờ trượt ở khổ hẹp — khai MỘT LẦN rồi dùng cho cả hai
  //  khổ màn. Chép hai bản là hai khổ màn lọc ra hai kết quả khác nhau mà không
  //  chỗ nào báo.
  const misaInput = (
    <Input
      className="w-40 max-md:w-full"
      placeholder="Mã MISA…"
      value={misaKeyword}
      onChange={(e) => setMisaKeyword(e.target.value)}
    />
  )

  const companySelect = (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="w-48 max-md:w-full">
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
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-44 max-md:w-full">
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
  )

  const sourceSelect = (
    <Select value={source} onValueChange={setSource}>
      <SelectTrigger className="w-40 max-md:w-full">
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
  )

  const methodSelect = (
    <Select value={method} onValueChange={setMethod}>
      <SelectTrigger className="w-40 max-md:w-full">
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
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Yêu cầu thanh toán"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem. Cùng luật đã áp cho `CrudListPage` và các màn viết tay khác.
          <span className="max-md:hidden">
            Đề nghị chi trả công nợ nhà cung cấp và đơn vị vận chuyển.
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp — không có lớp này thì nó co theo chữ và
        //  dán mép phải sau một khoảng trống dài.
        actionsClassName="max-md:[&>a]:flex-1"
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

      {/*  `group` + `data-scrolled`: mốc để thanh công cụ ghim biết đã có nội
           dung trôi bên dưới chưa (bóng đổ). Thiếu thì dải vẫn ghim, chỉ là
           không bao giờ đổ bóng — và lỗi đó im lặng. */}
      <Card
        ref={stickyRef}
        className="group flex min-h-0 flex-1 flex-col p-4"
        data-scrolled={scrolled ? '' : undefined}
      >
        <DataTable
          fillHeight
          columns={columns}
          rows={data?.items}
          getRowId={(r) => r.id}
          onRowClick={(r) => navigate(appRoutes.finance.paymentRequestDetail(r.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Chưa có yêu cầu thanh toán nào khớp bộ lọc."
          //  Khổ hẹp: THẺ thay bảng — xem `PaymentRequestCard`.
          mobileCard={(r) => <PaymentRequestCard row={r} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="finance.payment-requests"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phiếu',
          }}
          toolbar={
            //  ⚠️ **Khổ điện thoại: năm ô lọc dọn vào TỜ TRƯỢT**, thanh công cụ
            //  còn một hàng. Sáu ô khai bề rộng cứng (`w-56`…`w-40`) nên ở
            //  358px mỗi ô rơi xuống một hàng riêng: **bảy hàng ≈ 300px** chắn
            //  trên đầu danh sách, mà thanh này còn được GHIM — mỗi pixel là
            //  một pixel che mất thẻ. Gom lại: một hàng 52px, mở tờ trượt ra
            //  thì mỗi ô có trọn bề ngang kèm nhãn.
            <>
              <div className="relative min-w-56 flex-1 max-md:min-w-0 md:max-w-xs">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm theo mã phiếu…"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>

              {/*  `QuickFilterSheet` tự mang `md:hidden`, khối bên dưới tự mang
                   `hidden md:flex` — hai vế loại trừ nhau nên không bao giờ có
                   hai bản ô lọc cùng lúc trong cây DOM. */}
              <QuickFilterSheet
                activeCount={
                  (debouncedMisa ? 1 : 0) +
                  (companyId !== ALL ? 1 : 0) +
                  (status !== ALL ? 1 : 0) +
                  (source !== ALL ? 1 : 0) +
                  (method !== ALL ? 1 : 0)
                }
                onClearAll={() => {
                  setMisaKeyword('')
                  setCompanyId(ALL)
                  setStatus(ALL)
                  setSource(ALL)
                  setMethod(ALL)
                }}
              >
                <QuickFilterField label="Mã MISA">{misaInput}</QuickFilterField>
                <QuickFilterField label="Công ty">{companySelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Loại nợ">{sourceSelect}</QuickFilterField>
                <QuickFilterField label="Hình thức thanh toán">{methodSelect}</QuickFilterField>
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex md:flex-wrap">
                {misaInput}
                {companySelect}
                {statusSelect}
                {sourceSelect}
                {methodSelect}
              </div>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
