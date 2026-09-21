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
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
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
import { Input } from '@/shared/ui/input'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { PO_DOCUMENT_STATUS } from '@/shared/constants/statuses'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { PurchaseOrderCard } from '../components/purchase-order-card'
import { DocumentStatusBadge, StatusBadge } from '../components/document-status-badge'
import { PURCHASE_ORDER_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseOrders } from '../hooks/use-purchase-documents'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
import {
  PO_STATUS_LABELS,
  statusOptions,
  type PurchaseOrder,
} from '../types/purchase-document'
import { ORDER_TYPE_IMPORT, ORDER_TYPE_OPTIONS } from '../types/purchase-order-detail'

const ALL = 'all'

/**
 * Khóa cột trên bảng -> khóa cột của file Excel (`HEADER_COLS` trong
 * `backend/app/modules/purchase_order/export.py`). Hai bên đặt tên lệch nhau ở
 * vài cột (`order_date` vẽ `created_at`, `supplier` vẽ mã NCC) nên phải dịch,
 * không thì backend coi là khóa lạ và bỏ qua. Cột không có trong bảng dịch
 * (`nspt`, `actions`) vốn không nằm trong file xuất.
 */
const EXPORT_COLUMN_KEYS: Record<string, string> = {
  code: 'code',
  misa_code: 'misa_code',
  order_date: 'created_at',
  note: 'note',
  supplier: 'supplier_code',
  pr_code: 'pr_code',
  amount: 'amount',
  is_urgent: 'is_urgent',
  document_status: 'document_status',
  status: 'status',
}

const FILTER_CONFIG = {
  fields: PURCHASE_ORDER_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: [
    'company_id',
    'supplier_code',
    'nspt_id',
    'document_status',
    'status',
    'invoice_no',
    'item_group',
    'is_urgent',
    'order_type',
    'order_date_from',
    'order_date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function PurchaseOrderListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <PurchaseOrderListContent />
    </FilterProvider>
  )
}

function PurchaseOrderListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canExport = can('purchase_order', 'export')
  const canCreate = can('purchase_order', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [supplierCode, setSupplierCode] = useUrlParamState('supplier_code', ALL)
  const [nsptId, setNsptId] = useUrlParamState('nspt_id', ALL)
  const [docStatus, setDocStatus] = useUrlParamState('document_status', ALL)
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [isUrgent, setIsUrgent] = useUrlParamState('is_urgent', ALL)
  const [orderType, setOrderType] = useUrlParamState('order_type', ALL)
  //  Hai ô lọc chạy trên BẢNG DÒNG / bảng giao hàng chứ không trên đầu đơn, nên
  //  chúng không nằm trong `FILTERABLE` và không đưa xuống "Bộ lọc điều kiện"
  //  được — phải đứng ngoài đây (`purchase_order/controller.py`).
  //
  //  `item_group` gửi **TÊN** phân loại (dòng đơn chép chữ xuống, không giữ
  //  khóa); `invoice_no` so khớp CHỨA và hỏi cả dòng hàng lẫn lần giao.
  const [itemGroup, setItemGroup] = useUrlParamState('item_group', ALL)
  const {
    value: invoiceNo,
    setValue: setInvoiceNo,
    debouncedValue: debouncedInvoiceNo,
  } = useUrlSearchParam('invoice_no')
  const [orderDateFrom, setOrderDateFrom] = useUrlParamState('order_date_from', '')
  const [orderDateTo, setOrderDateTo] = useUrlParamState('order_date_to', '')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  /** Cột đang hiện trên bảng — nút "Xuất Excel" bám theo để file khớp màn hình. */
  const [visibleColumnKeys, setVisibleColumnKeys] = useState<string[]>([])

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: suppliers } = useSuppliers({ page_size: 500, is_active: true })
  const { data: employees } = useEmployees({ page_size: 500, is_active: true })
  //  Danh mục MƯỢN của phân hệ Sản xuất — tắt hẳn khi thiếu quyền, kẻo cứ mở màn
  //  là ăn một toast 403 cho thứ chỉ là nguồn của ô lọc.
  const { data: itemGroups } = usePurchaseRequestItemGroups(can('item_group', 'read'))
  const { queryParams, queryKey } = useFilterQuery()

  //  Bộ lọc nâng cao: khổ rộng mở bằng nút riêng + popover, khổ hẹp nhúng
  //  thẳng phần ruột vào tờ trượt. Cần `apply`/`reset`/`activeCount`.
  const filter = useFilterContext()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    companyId,
    supplierCode,
    nsptId,
    docStatus,
    status,
    isUrgent,
    orderType,
    itemGroup,
    debouncedInvoiceNo,
    orderDateFrom,
    orderDateTo,
    sortBy,
    sortDir,
  ])

  /**
   * Bộ lọc + sắp xếp đang đặt, KHÔNG kèm phân trang. Tách riêng để nút "Xuất
   * Excel" gửi lại đúng bộ này — backend dùng chung `_list_query` cho cả danh
   * sách lẫn đường xuất file nên tham số y hệt là ra đúng tập dữ liệu người
   * dùng đang nhìn.
   */
  const filterParams: ListParams = { ...queryParams }
  if (debouncedValue) filterParams.code = debouncedValue
  if (companyId !== ALL) filterParams.company_id = Number(companyId)
  if (supplierCode !== ALL) filterParams.supplier_code = supplierCode
  if (nsptId !== ALL) filterParams.nspt_id = Number(nsptId)
  if (docStatus !== ALL) filterParams.document_status = docStatus
  if (status !== ALL) filterParams.status = status
  if (isUrgent === 'true') filterParams.is_urgent = true
  if (orderType !== ALL) filterParams.order_type = Number(orderType)
  if (itemGroup !== ALL) filterParams.item_group = itemGroup
  if (debouncedInvoiceNo) filterParams.invoice_no = debouncedInvoiceNo
  if (orderDateFrom) filterParams.order_date_from = orderDateFrom
  if (orderDateTo) filterParams.order_date_to = orderDateTo
  if (sortBy) {
    filterParams.sort_by = sortBy
    filterParams.sort_dir = sortDir
  }

  const params: ListParams = { page, page_size: pageSize, ...filterParams }

  const { data, isLoading, isError } = usePurchaseOrders(params)

  const handleExportExcel = async () => {
    const cols = visibleColumnKeys
      .map((key) => EXPORT_COLUMN_KEYS[key])
      .filter(Boolean)
      .join(',')
    await downloadFile('/api/purchase-orders/export/xlsx', 'don-mua-hang.xlsx', {
      ...filterParams,
      ...(cols ? { cols } : {}),
    })
  }

  const handleClone = useCallback(
    async (po: PurchaseOrder, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/purchase-orders/${po.id}/clone`)
        toast.success('Đã nhân bản đơn mua hàng')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.purchaseOrderDetail(newId))
      } catch {
        toast.error('Nhân bản đơn mua hàng thất bại')
      }
    },
    [navigate],
  )

  const activeCount = [
    companyId !== ALL,
    supplierCode !== ALL,
    nsptId !== ALL,
    docStatus !== ALL,
    status !== ALL,
    isUrgent === 'true',
    orderType !== ALL,
    itemGroup !== ALL,
    Boolean(invoiceNo),
    Boolean(orderDateFrom || orderDateTo),
  ].filter(Boolean).length

  const clearAllFilters = () => {
    setCompanyId(ALL)
    setSupplierCode(ALL)
    setNsptId(ALL)
    setDocStatus(ALL)
    setStatus(ALL)
    setIsUrgent(ALL)
    setOrderType(ALL)
    setItemGroup(ALL)
    setInvoiceNo('')
    setOrderDateFrom('')
    setOrderDateTo('')
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

  const columns = useMemo<DataTableColumn<PurchaseOrder>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã ĐMH',
        width: 160,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (po) => <span className="truncate font-medium">{po.code}</span>,
      },
      {
        key: 'misa_code',
        header: 'Mã MISA',
        width: 130,
        sortable: true,
        defaultHidden: true,
        cell: (po) => po.misa_code || '',
      },
      {
        key: 'order_date',
        header: 'Ngày đặt',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (po) => formatDateTime(po.created_at) || '',
      },
      {
        key: 'supplier',
        header: 'Nhà cung cấp',
        width: 240,
        cell: (po) => (
          <span className="truncate" title={po.supplier_name}>
            {po.supplier_name || po.supplier_code || ''}
          </span>
        ),
      },
      { key: 'pr_code', header: 'Mã PYC', width: 140, cell: (po) => po.pr_code || '' },
      {
        //  Ẩn mặc định vì ghi chú thường dài, nhưng phải CÓ cột thì người dùng
        //  mới bật lên để kéo nó vào file Excel được (bản v1 vẫn có cột này).
        key: 'note',
        header: 'Ghi chú',
        width: 220,
        defaultHidden: true,
        cell: (po) => (
          <span className="truncate" title={po.note || undefined}>
            {po.note || ''}
          </span>
        ),
      },
      { key: 'nspt', header: 'NSPT', width: 170, defaultHidden: true, cell: (po) => po.nspt || '' },
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
        sortable: true,
        cell: (po) =>
          po.is_urgent ? (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Gấp
            </Badge>
          ) : null,
      },
      {
        // bao-CR-319 — đơn nhập khẩu có nhãn riêng; đơn trong nước để trống cho đỡ rối.
        key: 'order_type',
        header: 'Loại đơn',
        width: 110,
        cell: (po) =>
          Number(po.order_type) === ORDER_TYPE_IMPORT ? (
            <Badge variant="secondary" className="border-0 bg-navy/10 text-navy">
              {po.order_type_label || 'Nhập khẩu'}
            </Badge>
          ) : null,
      },
      {
        key: 'document_status',
        header: 'Hồ sơ',
        width: 130,
        cell: (po) => <DocumentStatusBadge status={po.document_status} />,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (po) => <StatusBadge status={po.status} labels={PO_STATUS_LABELS} />,
      },
      {
        // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
        key: 'updated_at',
        header: 'Ngày cập nhật',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (po) => formatDateTime(po.updated_at) || '',
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (po) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản đơn mua hàng"
              onClick={(e) => handleClone(po, e)}
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
      <SelectTrigger className="w-full md:w-44 text-xs h-9">
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

  const supplierSelect = (
    <Select value={supplierCode} onValueChange={setSupplierCode}>
      <SelectTrigger className="w-full md:w-48 text-xs h-9">
        <SelectValue placeholder="Nhà cung cấp" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả nhà cung cấp</SelectItem>
        {(suppliers?.items ?? []).map((sup) => (
          <SelectItem key={sup.code} value={sup.code}>
            {sup.name} ({sup.code})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const nsptSelect = (
    <Select value={nsptId} onValueChange={setNsptId}>
      <SelectTrigger className="w-full md:w-40 text-xs h-9">
        <SelectValue placeholder="NSPT" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả NSPT</SelectItem>
        {(employees?.items ?? []).map((emp) => (
          <SelectItem key={emp.id} value={String(emp.id)}>
            {emp.full_name} ({emp.code})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const docStatusSelect = (
    <Select value={docStatus} onValueChange={setDocStatus}>
      <SelectTrigger className="w-full md:w-40 text-xs h-9">
        <SelectValue placeholder="Hồ sơ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả hồ sơ</SelectItem>
        {PO_DOCUMENT_STATUS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-40 text-xs h-9">
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
  )

  const orderTypeSelect = (
    <Select value={orderType} onValueChange={setOrderType}>
      <SelectTrigger className="w-full md:w-36 text-xs h-9">
        <SelectValue placeholder="Loại đơn" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại đơn</SelectItem>
        {ORDER_TYPE_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={String(option.value)}>
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

  //  Ô NHẬP chứ không phải ô chọn: số hóa đơn là chuỗi tự do do kế toán gõ, và
  //  người dùng thường chỉ nhớ vài chữ số cuối — backend so khớp CHỨA nên gõ
  //  một khúc là đủ.
  const invoiceNoInput = (
    <Input
      value={invoiceNo}
      onChange={(e) => setInvoiceNo(e.target.value)}
      placeholder="Số hóa đơn…"
      aria-label="Lọc theo số hóa đơn"
      className="h-9 w-full text-xs md:w-36"
    />
  )

  const dateRangeInput = (
    <DateRangePicker
      from={orderDateFrom}
      to={orderDateTo}
      placeholder="Ngày đặt..."
      className="w-full md:w-auto"
      onChange={(f, t) => {
        setOrderDateFrom(f)
        setOrderDateTo(t)
      }}
    />
  )


  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật
    //  `payment-request-list-page` và `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Đơn mua hàng"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  một dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">Đơn mua hàng (PO) gửi nhà cung cấp.</span>
        }
        //  Hai nút chia đôi hàng ở khổ hẹp — không có lớp này thì chúng co theo
        //  chữ và dán mép phải sau một khoảng trống dài. Nhắm `[&>div]` vì cụm
        //  nút bọc thêm một lớp `div`.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          <div className="flex items-center gap-2">
            {canExport && (
              <Button variant="outline" className="max-md:flex-1" onClick={handleExportExcel}>
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            )}
            <PermissionGate entity="purchase_order" action="create">
              <Button
                className="max-md:flex-1"
                onClick={() => navigate(appRoutes.procurement.purchaseOrderNew)}
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
          getRowId={(po) => po.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy đơn mua hàng nào."
          //  Khổ hẹp: THẺ thay bảng — xem `PurchaseOrderCard`.
          mobileCard={(po) => <PurchaseOrderCard row={po} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.purchase-orders"
          onVisibleColumnsChange={setVisibleColumnKeys}
          onRowClick={(po) => navigate(appRoutes.procurement.purchaseOrderDetail(po.id))}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
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
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: bản đầy đủ liệt kê năm thứ tìm
                   được nên bị xén mất đúng phần đuôi — thứ người đọc chưa đoán
                   được.

                   ⚠️ **Đo rồi hãy viết.** Màn này có thêm chip *Gấp* trên thanh
                   công cụ, nên ô tìm chỉ còn **73px** — đo ngày 14/09/2026 trên
                   máy 390px, tức hiện đúng "Tìm ĐMH, ᴎ" rồi cụt. Rút chữ thôi
                   KHÔNG cứu được: hai vế ngắn nhất cũng đã 90px. Phải trả lại
                   chỗ cho ô — xem `iconOnly` ở `QuickFilterSheet` bên dưới.

                   ⚠️ **Mốc đo là 375px, không phải 390px.** Sau khi rút nút lọc,
                   ô rộng 117px ở máy 390px nhưng chỉ **102px** ở iPhone SE/mini
                   (375px) — "Tìm ĐMH, NCC…" tốn 110px nên vừa ở máy này mà cụt ở
                   máy kia. Lấy ~100px làm trần cho mọi câu gợi ý rút gọn. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã ĐMH, MISA, PYC, NCC, mã/tên sản phẩm…"
                placeholderShort="Tìm ĐMH, SP…"
                aria-label="Tìm đơn mua hàng"
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

              {/*  Desktop Filter Controls — `md:contents` chứ KHÔNG phải `md:flex`.
                   Bọc trong một thẻ flex riêng thì cả cụm lọc là MỘT ô của thanh
                   công cụ: không đủ chỗ là nó rớt nguyên khối xuống dòng dưới, để
                   lại một khoảng trống dài bên phải ô tìm kiếm rồi tự xuống dòng
                   thêm lần nữa bên trong. Thêm ô lọc *Loại đơn* (bao-CR-319) là
                   vượt ngưỡng đó. `display: contents` cho các ô lọc thành ô trực
                   tiếp của thanh công cụ nên chúng xếp kín từng dòng. */}
              <div className="hidden md:contents">
                {companySelect}
                {supplierSelect}
                {nsptSelect}
                {docStatusSelect}
                {statusSelect}
                {orderTypeSelect}
                {itemGroupSelect}
                {invoiceNoInput}
                {dateRangeInput}
                <ConditionalFilter />
              </div>

              {/*  ⚠️ Ô trong tờ trượt phải có NHÃN. Trên thanh công cụ, ô chọn tự
                   giải nghĩa bằng giá trị đang chọn («Tất cả công ty»); xếp dọc
                   BẢY ô như vậy trong một tờ trắng thì thành một danh sách chữ
                   trôi nổi, người đọc không biết ô nào lọc cái gì cho tới khi
                   bấm thử. */}
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
                <QuickFilterField label="Nhà cung cấp">{supplierSelect}</QuickFilterField>
                <QuickFilterField label="NSPT">{nsptSelect}</QuickFilterField>
                <QuickFilterField label="Hồ sơ chứng từ">{docStatusSelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Loại đơn">{orderTypeSelect}</QuickFilterField>
                <QuickFilterField label="Phân loại">{itemGroupSelect}</QuickFilterField>
                <QuickFilterField label="Số hóa đơn">{invoiceNoInput}</QuickFilterField>
                <QuickFilterField label="Ngày đặt">{dateRangeInput}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
