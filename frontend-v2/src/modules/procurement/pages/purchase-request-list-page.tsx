import { Copy, Download, Plus } from 'lucide-react'
import { useCallback, useMemo, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { httpClient } from '@/core/api/http-client'
import { downloadFile } from '@/core/api/download-file'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PurchaseRequestCard } from '../components/purchase-request-card'
import { StatusBadge } from '../components/document-status-badge'
import { PURCHASE_REQUEST_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
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
  preserveParams: [
    'company_id',
    'department_id',
    'status',
    'is_urgent',
    'item_group',
    'assignee',
    'need_date_from',
    'need_date_to',
    'request_date_from',
    'request_date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function PurchaseRequestListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseRequestListContent />
    </FilterProvider>
  )
}

function PurchaseRequestListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canExport = can('purchase_request', 'export')
  const canCreate = can('purchase_request', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [isUrgent, setIsUrgent] = useUrlParamState('is_urgent', ALL)
  //  Hai ô lọc chạy trên BẢNG DÒNG chứ không trên đầu phiếu, nên chúng không nằm
  //  trong `FILTERABLE` của backend và không đưa xuống "Bộ lọc điều kiện" được —
  //  phải đứng ngoài đây (`purchase_request/controller.py`).
  //
  //  ⚠️ `assignee` gửi **MÃ** nhân sự, `item_group` gửi **TÊN** phân loại: dòng
  //  phiếu chép chữ xuống chứ không giữ khóa. Gửi id thì backend so khớp không
  //  trúng gì cả và danh sách rỗng trong im lặng.
  const [itemGroup, setItemGroup] = useUrlParamState('item_group', ALL)
  const [assignee, setAssignee] = useUrlParamState('assignee', ALL)
  const [needDateFrom, setNeedDateFrom] = useUrlParamState('need_date_from', '')
  const [needDateTo, setNeedDateTo] = useUrlParamState('need_date_to', '')
  const [reqDateFrom, setReqDateFrom] = useUrlParamState('request_date_from', '')
  const [reqDateTo, setReqDateTo] = useUrlParamState('request_date_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  //  Hai danh mục MƯỢN của phân hệ khác — tắt hẳn khi thiếu quyền, kẻo cứ mở màn
  //  là ăn một toast 403 cho thứ chỉ là nguồn của ô lọc.
  const { data: itemGroups } = usePurchaseRequestItemGroups(can('item_group', 'read'))
  const { data: employees } = useEmployees(
    { page_size: 500, is_active: true },
    { enabled: can('employee', 'read') },
  )
  const { queryParams, queryKey } = useFilterQuery()

  //  Bộ lọc nâng cao: khổ rộng mở bằng popover, khổ hẹp nhúng ruột vào tờ trượt.
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
    isUrgent,
    itemGroup,
    assignee,
    needDateFrom,
    needDateTo,
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
  if (isUrgent !== ALL) params.is_urgent = isUrgent === 'true'
  if (itemGroup !== ALL) params.item_group = itemGroup
  if (assignee !== ALL) params.assignee = assignee
  if (needDateFrom) params.need_date_from = needDateFrom
  if (needDateTo) params.need_date_to = needDateTo
  if (reqDateFrom) params.request_date_from = reqDateFrom
  if (reqDateTo) params.request_date_to = reqDateTo
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = usePurchaseRequests(params)

  const handleExportExcel = async () => {
    await downloadFile('/api/purchase-requests/export/xlsx', 'yeu-cau-mua-hang.xlsx')
  }

  const handleClone = useCallback(
    async (pr: PurchaseRequest, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/purchase-requests/${pr.id}/clone`)
        toast.success('Đã nhân bản phiếu yêu cầu mua hàng')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.purchaseRequestDetail(newId))
      } catch {
        toast.error('Nhân bản phiếu thất bại')
      }
    },
    [navigate],
  )

  const activeCount = [
    companyId !== ALL,
    departmentId !== ALL,
    status !== ALL,
    isUrgent === 'true',
    itemGroup !== ALL,
    assignee !== ALL,
    Boolean(needDateFrom || needDateTo),
    Boolean(reqDateFrom || reqDateTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setDepartmentId(ALL)
    setStatus(ALL)
    setIsUrgent(ALL)
    setItemGroup(ALL)
    setAssignee(ALL)
    setNeedDateFrom('')
    setNeedDateTo('')
    setReqDateFrom('')
    setReqDateTo('')
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

  const columns = useMemo<DataTableColumn<PurchaseRequest>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã PYC',
        width: 220,
        sortable: true,
        hideable: false,
        cell: (pr) => (
          <div className="flex items-center gap-1.5">
            <span className="truncate font-medium">{pr.code}</span>
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
        // bao-CR-316: ô này in `created_at` nên phải SẮP theo `created_at`. Khóa cũ là
        // `request_date` — cột đó nay là ngày LẬP phiếu (người dùng sửa được), sắp theo nó
        // thì thứ tự hiện ra không khớp con số đang bày trong ô.
        key: 'created_at',
        header: 'Ngày tạo',
        width: 150,
        sortable: true,
        cell: (pr) => formatDateTime(pr.created_at) || '',
      },
      { key: 'requester', header: 'Người yêu cầu', width: 200, cell: (pr) => pr.requester || '' },
      { key: 'department', header: 'Bộ phận', width: 180, cell: (pr) => pr.department || '' },
      {
        key: 'need_date',
        header: 'Cần hàng',
        width: 120,
        sortable: true,
        cell: (pr) => formatDate(pr.need_date) || '',
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
        sortable: true,
        cell: (pr) =>
          pr.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : null,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (pr) => <StatusBadge status={pr.status} labels={PR_STATUS_LABELS} />,
      },
      {
        // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
        key: 'updated_at',
        header: 'Ngày cập nhật',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (pr) => formatDateTime(pr.updated_at) || '',
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (pr) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản phiếu"
              onClick={(e) => handleClone(pr, e)}
            >
              <Copy className="size-4 text-muted-foreground" />
            </Button>
          ) : null,
      },
    ],
    [canCreate, handleClone],
  )

  //  Cùng một ô dựng HAI lần (hàng ngang ở khổ rộng · tờ trượt ở khổ hẹp).
  //  State nằm ở đây nên hai bản luôn nói cùng một giá trị — khuôn của
  //  `payment-request-list-page`, không phải trùng lặp cần dọn.

  const companySelect = (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9">
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

  const departmentSelect = (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9">
        <SelectValue placeholder="Bộ phận yêu cầu" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
        {(departments?.items ?? []).map((dept) => (
          <SelectItem key={dept.id} value={String(dept.id)}>
            {dept.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9">
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
  )

  const itemGroupSelect = (
    <Select value={itemGroup} onValueChange={setItemGroup}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9" aria-label="Lọc theo phân loại">
        <SelectValue placeholder="Phân loại" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả phân loại</SelectItem>
        {(itemGroups?.items ?? []).map((group) => (
          <SelectItem key={group.id} value={group.name}>
            {group.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const assigneeSelect = (
    <Select value={assignee} onValueChange={setAssignee}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9" aria-label="Lọc theo NSTM phụ trách">
        <SelectValue placeholder="NSTM phụ trách" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả NSTM</SelectItem>
        {(employees?.items ?? [])
          //  Nhân sự chưa có mã thì không lọc được — bỏ khỏi danh sách chứ đừng
          //  để một dòng bấm vào là bảng rỗng.
          .filter((employee) => Boolean(employee.code))
          .map((employee) => (
            <SelectItem key={employee.id} value={employee.code}>
              {employee.full_name} ({employee.code})
            </SelectItem>
          ))}
      </SelectContent>
    </Select>
  )

  const needDateInput = (
    <DateRangePicker
      from={needDateFrom}
      to={needDateTo}
      placeholder="Ngày cần hàng..."
      className="w-full md:w-auto"
      onChange={(f, t) => {
        setNeedDateFrom(f)
        setNeedDateTo(t)
      }}
    />
  )

  const reqDateInput = (
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
    //  trúng mép ngoài khe thì trang không nhúc nhích.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Yêu cầu mua hàng"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  một dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">Phiếu yêu cầu mua hàng (PYC) của các bộ phận.</span>
        }
        //  Hai nút chia đôi hàng ở khổ hẹp. Nhắm `[&>div]` vì cụm nút bọc thêm
        //  một lớp `div` — `[&>button]` không chạm tới.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          <div className="flex items-center gap-2">
            {canExport && (
              <Button variant="outline" className="max-md:flex-1" onClick={handleExportExcel}>
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            )}
            <PermissionGate entity="purchase_request" action="create">
              <Button
                className="max-md:flex-1"
                onClick={() => navigate(appRoutes.procurement.purchaseRequestNew)}
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
          getRowId={(pr) => pr.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy yêu cầu mua hàng nào."
          //  Khổ hẹp: THẺ thay bảng — xem `PurchaseRequestCard`.
          mobileCard={(pr) => <PurchaseRequestCard row={pr} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.purchase-requests"
          onRowClick={(pr) => navigate(appRoutes.procurement.purchaseRequestDetail(pr.id))}
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
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: bản đầy đủ liệt kê bốn thứ tìm
                   được nên bị xén mất đúng phần đuôi — thứ người đọc chưa đoán
                   được.

                   ⚠️ **Đo rồi hãy viết.** Màn này có thêm chip *Gấp* trên thanh
                   công cụ, nên ô tìm chỉ còn **73px** — đo ngày 14/09/2026 trên
                   máy 390px. Bản "rút gọn" cũ tốn 156px, tức dài gấp đôi ô và
                   chẳng khá hơn bản đầy đủ chút nào. Rút chữ thôi KHÔNG cứu
                   được; phải trả lại chỗ cho ô — xem `iconOnly` ở
                   `QuickFilterSheet` bên dưới. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã PYC, người yêu cầu, mã/tên sản phẩm…"
                placeholderShort="Tìm PYC, SP…"
                aria-label="Tìm yêu cầu mua hàng"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  Chip *Gấp* ở LẠI thanh công cụ, không vào tờ trượt: đây là bộ
                   lọc một chạm dùng nhiều nhất của màn này, nhét vào sau hai lớp
                   (mở tờ trượt → bấm → đóng) là đổi một chạm thành ba. */}
              <Button
                variant={isUrgent === 'true' ? 'default' : 'outline'}
                size="sm"
                className="h-9 shrink-0 text-xs"
                onClick={() => setIsUrgent(isUrgent === 'true' ? ALL : 'true')}
              >
                Gấp
              </Button>

              {/*  `md:contents` chứ KHÔNG phải `md:flex`: bọc cụm lọc trong một thẻ
                   flex riêng thì với thanh công cụ nó là MỘT ô, không đủ chỗ là
                   rớt nguyên khối xuống dòng dưới và chừa khoảng trống dài bên
                   phải ô tìm kiếm. Màn Đơn mua hàng đã vỡ đúng kiểu đó khi thêm
                   ô lọc thứ sáu (bao-CR-319). */}
              <div className="hidden md:contents">
                {companySelect}
                {departmentSelect}
                {statusSelect}
                {itemGroupSelect}
                {assigneeSelect}
                {needDateInput}
                {reqDateInput}
                <ConditionalFilter />
              </div>

              {/*  ⚠️ Ô trong tờ trượt phải có NHÃN. Trên thanh công cụ, ô chọn tự
                   giải nghĩa bằng giá trị đang chọn («Tất cả công ty»); xếp dọc
                   năm ô như vậy trong một tờ trắng thì thành một danh sách chữ
                   trôi nổi. Riêng HAI ô ngày thì nhãn là bắt buộc tuyệt đối —
                   chúng trông y hệt nhau, không có nhãn thì không cách nào biết
                   ô nào là *ngày cần hàng*, ô nào là *ngày tạo*. */}
              {/*  ⚠️ `iconOnly`: thanh công cụ khổ hẹp của màn này phải gói ô
                   tìm + chip *Gấp* + nút lọc + nút tải lại vào MỘT hàng, và 48px
                   chữ «Bộ lọc» đúng là phần chênh giữa ô tìm đọc được và ô tìm
                   cụt ở chữ thứ tám (73px → 121px). Giữ chữ thì phải bỏ chip
                   *Gấp* — mà đó là bộ lọc một chạm dùng nhiều nhất của màn này,
                   đổi nó thành ba chạm còn tệ hơn. Cái phễu vẫn có huy hiệu chấm
                   khi đang lọc, và tiêu đề tờ trượt vẫn ghi «Bộ lọc». */}
              <QuickFilterSheet
                iconOnly
                activeCount={activeCount}
                onClearAll={clearAllFilters}
                onApply={filter.apply}
              >
                <QuickFilterField label="Công ty">{companySelect}</QuickFilterField>
                <QuickFilterField label="Bộ phận yêu cầu">{departmentSelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Phân loại">{itemGroupSelect}</QuickFilterField>
                <QuickFilterField label="NSTM phụ trách">{assigneeSelect}</QuickFilterField>
                <QuickFilterField label="Ngày cần hàng">{needDateInput}</QuickFilterField>
                <QuickFilterField label="Ngày tạo">{reqDateInput}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
