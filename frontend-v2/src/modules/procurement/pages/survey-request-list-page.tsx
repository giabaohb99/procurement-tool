import { Copy, Download, Plus } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import { downloadFile } from '@/core/api/download-file'
import { httpClient } from '@/core/api/http-client'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDateTime } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { SurveyRequestCard } from '../components/survey-request-card'
import { SURVEY_REQUEST_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { useSurveyRequests } from '../hooks/use-purchase-documents'
import {
  SR_STATUS_LABELS,
  statusOptions,
  type SurveyRequest,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: SURVEY_REQUEST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['company_id', 'department_id', 'status', 'request_date_from', 'request_date_to', 'sort_by', 'sort_dir'],
}

export function SurveyRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyRequestListContent />
    </FilterProvider>
  )
}

function SurveyRequestListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canExport = can('survey_request', 'export')
  const canCreate = can('survey_request', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [reqDateFrom, setReqDateFrom] = useUrlParamState('request_date_from', '')
  const [reqDateTo, setReqDateTo] = useUrlParamState('request_date_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  const { queryParams, queryKey } = useFilterQuery()

  //  Bộ lọc nâng cao: khổ rộng mở bằng nút riêng + popover, khổ hẹp nhúng thẳng
  //  phần ruột vào tờ trượt. Cần `apply`/`reset`/`activeCount` nên phải lấy
  //  context, không chỉ query.
  const filter = useFilterContext()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    departmentId,
    status,
    reqDateFrom,
    reqDateTo,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (status !== ALL) params.status = status
  if (reqDateFrom) params.request_date_from = reqDateFrom
  if (reqDateTo) params.request_date_to = reqDateTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useSurveyRequests(params)

  const handleExportExcel = async () => {
    await downloadFile('/api/survey-requests/export/xlsx', 'yeu-cau-bao-gia.xlsx')
  }

  const handleClone = useCallback(
    async (sr: SurveyRequest, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/survey-requests/${sr.id}/clone`)
        toast.success('Đã nhân bản phiếu yêu cầu báo giá')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.surveyRequestDetail(newId))
      } catch {
        toast.error('Nhân bản phiếu thất bại')
      }
    },
    [navigate],
  )

  //  Huy hiệu trên nút «Bộ lọc» của khổ hẹp đếm CẢ HAI tầng — ô lọc nhanh và
  //  điều kiện nâng cao — vì cả hai nay nằm sau đúng một nút đó. Đếm thiếu một
  //  tầng thì người dùng thấy nút không dấu gì mà danh sách vẫn đang bị lọc.
  const activeCount =
    [
      companyId !== ALL,
      departmentId !== ALL,
      status !== ALL,
      Boolean(reqDateFrom || reqDateTo),
    ].filter(Boolean).length + filter.activeCount

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setReqDateFrom('')
    setReqDateTo('')
    filter.reset()
  }

  const handleSortChange = (newSortBy: string, newSortDir: 'asc' | 'desc') => {
    const next = new URLSearchParams(searchParams)
    //  Khóa cột rỗng = nhịp thứ ba của tiêu đề cột: thôi sắp xếp. Phải XÓA tham
    //  số chứ đừng ghi chuỗi rỗng, kẻo đường dẫn gửi cho nhau còn dính
    //  `?sort_by=&sort_dir=asc`, đọc như đang sắp xếp theo một cột không tên.
    if (newSortBy) {
      next.set('sort_by', newSortBy)
      next.set('sort_dir', newSortDir)
    } else {
      next.delete('sort_by')
      next.delete('sort_dir')
    }
    setSearchParams(next)
  }

  const columns = useMemo<DataTableColumn<SurveyRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        sortable: true,
        hideable: false,
        cell: (sr) => <span className="truncate font-medium">{sr.code}</span>,
      },
      { key: 'purpose', header: 'Mục đích', width: 280, cell: (sr) => sr.purpose || '' },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (sr) => sr.requester || '' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (sr) => sr.department || '' },
      {
        key: 'request_date',
        header: 'Ngày tạo',
        width: 150,
        sortable: true,
        cell: (sr) => formatDateTime(sr.created_at) || '',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (sr) => <StatusBadge status={sr.status} labels={SR_STATUS_LABELS} />,
      },
      {
        // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
        key: 'updated_at',
        header: 'Ngày cập nhật',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (sr) => formatDateTime(sr.updated_at) || '',
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (sr) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản phiếu yêu cầu báo giá"
              onClick={(e) => handleClone(sr, e)}
            >
              <Copy className="size-4 text-muted-foreground" />
            </Button>
          ) : null,
      },
    ],
    [canCreate, handleClone],
  )

  //  Cùng một ô chọn dựng HAI lần (hàng ngang ở khổ rộng · tờ trượt ở khổ hẹp).
  //  State nằm ở đây nên hai bản luôn nói cùng một giá trị — khuôn của
  //  `survey-list-page`, không phải trùng lặp cần dọn.
  const companySelect = (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="h-9 w-full text-xs md:w-44" aria-label="Lọc theo công ty">
        <SelectValue placeholder="Công ty" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả công ty</SelectItem>
        {(companies?.items ?? []).map((company: { id: number; name: string }) => (
          <SelectItem key={company.id} value={String(company.id)}>
            {company.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const departmentSelect = (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="h-9 w-full text-xs md:w-44" aria-label="Lọc theo bộ phận">
        <SelectValue placeholder="Bộ phận yêu cầu" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
        {(departments?.items ?? []).map((dept: { id: number; name: string }) => (
          <SelectItem key={dept.id} value={String(dept.id)}>
            {dept.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="h-9 w-full text-xs md:w-40" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        {statusOptions(SR_STATUS_LABELS).map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const dateRangeInput = (
    <DateRangePicker
      from={reqDateFrom}
      to={reqDateTo}
      placeholder="Ngày tạo..."
      className="w-full md:w-auto"
      onChange={(f, t) => {
        setReqDateFrom(f)
        setReqDateTo(t)
      }}
    />
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật `survey-list-page`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Yêu cầu báo giá"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">
            Phiếu yêu cầu khảo sát giá (YCBG) trước khi lên yêu cầu mua hàng.
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp — cụm nút bọc thêm một lớp `div` nên phải
        //  nhắm `[&>div]`, `[&>button]` không chạm tới.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          <div className="flex items-center gap-2">
            {canExport && (
              <Button variant="outline" className="max-md:flex-1" onClick={handleExportExcel}>
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            )}
            <PermissionGate entity="survey_request" action="create">
              <Button
                className="max-md:flex-1"
                onClick={() => navigate(appRoutes.procurement.surveyRequestNew)}
              >
                <Plus className="mr-1.5 size-4" />
                Thêm mới
              </Button>
            </PermissionGate>
          </div>
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
          getRowId={(sr) => sr.id}
          onRowClick={(sr) => navigate(appRoutes.procurement.surveyRequestDetail(sr.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu báo giá nào."
          //  Khổ hẹp: THẺ thay bảng — xem `SurveyRequestCard`.
          //
          //  ⚠️ Nút *Nhân bản* của cột thao tác KHÔNG theo sang thẻ: bảng khai
          //  `onRowClick` nên thẻ bị bọc trong một `<button>`, lồng nút vào là
          //  HTML sai. Nhân bản là việc hiếm và vẫn làm được ở khổ rộng.
          mobileCard={(sr) => <SurveyRequestCard row={sr} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.survey-requests"
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
            <>
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: bản đầy đủ liệt kê ba thứ tìm
                   được nên bị xén giữa chừng, mất đúng phần đuôi — thứ người
                   đọc chưa đoán được.

                   ⚠️ **Đo rồi hãy viết.** Ô tìm ở khổ hẹp chia hàng với nút *Bộ
                   lọc* và nút *Tải lại*, nên chỉ còn **~134px** — đo ngày
                   14/09/2026 trên máy 390px. Hai vế (~100px) là vừa; ba vế
                   (~137px) vẫn bị xén, tức bản "rút gọn" không giải quyết được
                   gì so với bản đầy đủ. Câu đủ vẫn còn ở khổ rộng và ở
                   `aria-label`. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã phiếu, người yêu cầu, mã/tên sản phẩm…"
                placeholderShort="Tìm phiếu, SP…"
                aria-label="Tìm yêu cầu báo giá"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  `md:contents` chứ KHÔNG phải `md:flex`: bọc cụm lọc trong một thẻ
                   flex riêng thì với thanh công cụ nó là MỘT ô, không đủ chỗ là
                   rớt nguyên khối xuống dòng dưới và chừa khoảng trống dài bên
                   phải ô tìm kiếm. Màn Đơn mua hàng đã vỡ đúng kiểu đó khi thêm
                   ô lọc thứ sáu (bao-CR-319). */}
              <div className="hidden md:contents">
                {companySelect}
                {departmentSelect}
                {statusSelect}
                {dateRangeInput}
                <ConditionalFilter />
              </div>

              {/*  ⚠️ Ô trong tờ trượt phải có NHÃN. Trên thanh công cụ, ô chọn tự
                   giải nghĩa bằng giá trị đang chọn («Tất cả công ty»); xếp dọc
                   mấy ô như vậy trong một tờ trắng thì thành danh sách chữ trôi
                   nổi, người đọc không biết ô nào lọc cái gì cho tới khi bấm
                   thử. */}
              <QuickFilterSheet
                activeCount={activeCount}
                onClearAll={clearAllFilters}
                onApply={filter.apply}
              >
                <QuickFilterField label="Công ty">{companySelect}</QuickFilterField>
                <QuickFilterField label="Bộ phận yêu cầu">{departmentSelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Ngày tạo">{dateRangeInput}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
