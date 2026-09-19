import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlMultiParam } from '@/shared/hooks/use-url-multi-param'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { MultiPicker } from '@/shared/ui/multi-picker'
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
import { PO_PROGRESS_STATUS } from '@/shared/constants/statuses'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'
import { DocumentStatusBadge, ProgressStatusBadge } from '../components/document-status-badge'
import { PurchaseProgressCard } from '../components/purchase-progress-card'
import { usePurchaseProgress } from '../hooks/use-purchase-documents'
import type { PurchaseProgressRow } from '../types/purchase-progress'

const ALL = 'all'

/**
 * Khoảng ngày lọc theo MỐC nào. Một dòng ở đây là MỘT LẦN GIAO, nên hai mốc lệch
 * nhau thật: đơn đặt tháng 7 mà giao làm ba đợt thì cùng một dòng đặt hàng nằm
 * rải khắp tháng 8-9. Hỏi "đặt trong kỳ" và "nhận trong kỳ" ra hai tập khác hẳn.
 *
 * Mặc định là NGÀY ĐẶT HÀNG — đó là mốc của chứng từ, cũng là cột bảng đang xếp
 * theo. Backend đọc sẵn cả hai cặp (`purchase_progress/controller.py`).
 */
const DATE_FIELDS = [
  { value: 'order', label: 'Theo ngày ĐH', from: 'order_date_from', to: 'order_date_to' },
  { value: 'received', label: 'Theo ngày nhận', from: 'received_date_from', to: 'received_date_to' },
] as const

const DEFAULT_DATE_FIELD = DATE_FIELDS[0].value

/**
 * Tiến độ mua hàng — báo cáo phẳng theo TỪNG LẦN GIAO của từng dòng đơn hàng,
 * không phải danh sách chứng từ.
 *
 * Endpoint `/api/purchase-progress` KHÔNG chạy qua `apply_filters` mà tự đọc bộ
 * tham số riêng (`company_id`, `department_id`, `status`, `q`, các cặp ngày…) nên
 * màn này không dùng "Bộ lọc điều kiện" như các danh sách khác.
 */
export function PurchaseProgressPage() {
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  // bao-CR-423: ô Công ty và ô Tiến độ chọn được NHIỀU giá trị; không chọn gì là
  // "Tất cả". Chọn nhiều trong CÙNG một ô nghĩa là HOẶC, hai ô khác nhau vẫn là VÀ.
  const [companyIds, setCompanyIds] = useUrlMultiParam('company_id')
  // CR-088: lọc theo ID phòng ban. Gửi TÊN thì phòng đổi tên là bộ lọc trượt sạch,
  // danh sách rỗng mà không báo gì. Backend vẫn nhận `department=<tên>` cho các
  // đường dẫn cũ đã lưu, chỉ có màn này thôi không gửi nữa.
  const [departmentId, setDepartmentId] = useUrlParamState('department_id', ALL)
  const [statuses, setStatuses] = useUrlMultiParam('status')
  const [dateField, setDateField] = useUrlParamState('date_field', DEFAULT_DATE_FIELD)
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const navigate = useNavigate()
  const { can } = usePermission()

  //  CÙNG một `useIsMobile` mà `DataTable` dùng để đổi sang thẻ, nên hai bên
  //  không thể lệch nhau: hễ đang bày thẻ thì chạm-để-mở cũng đang bật.
  const isMobile = useIsMobile()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })

  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    companyIds,
    departmentId,
    statuses,
    dateField,
    dateFrom,
    dateTo,
  ])

  const params: ListParams = { page, page_size: pageSize }
  if (debouncedValue) params.q = debouncedValue
  //  Gửi nối bằng dấu phẩy, kể cả khi mới chọn một — `read_multi_param` bên
  //  backend đọc được cả dạng đó lẫn dạng lặp khóa (bao-CR-423).
  if (companyIds.length) params.company_id = companyIds.join(',')
  if (departmentId !== ALL) params.department_id = Number(departmentId)
  if (statuses.length) params.status = statuses.join(',')
  if (dateFrom || dateTo) {
    const field = DATE_FIELDS.find((item) => item.value === dateField) ?? DATE_FIELDS[0]
    if (dateFrom) params[field.from] = dateFrom
    if (dateTo) params[field.to] = dateTo
  }

  const { data, isLoading, isError } = usePurchaseProgress(params)

  // Không có quyền `supplier.read` thì backend xóa trắng cột NCC / vận chuyển —
  // ẩn luôn cho khỏi bày ra một loạt ô rỗng.
  const showSupplier = data?.show_supplier ?? true
  // useCallback để đưa được vào deps của `columns` mà không phá memo:
  // hàm khai báo thẳng trong thân component sẽ đổi danh tính mỗi lần render.
  const companyName = useCallback(
    (id: number) => (companies?.items ?? []).find((company) => company.id === id)?.name ?? '',
    [companies],
  )

  const columns = useMemo<DataTableColumn<PurchaseProgressRow>[]>(() => {
    const all: (DataTableColumn<PurchaseProgressRow> & { supplierOnly?: boolean })[] = [
      {
        key: 'po_code',
        header: 'Mã ĐMH',
        width: 160,
        hideable: false,
        // Bảng này rộng ~24 cột: ghim sẵn mã đơn để cuộn tới cột cuối vẫn biết
        // đang xem đơn nào. Người dùng ghim/bỏ ghim tiếp ở menu "Cột".
        defaultPinned: true,
        //  `wrap` cho cột chữ: khách cần ĐỌC ĐỦ, không phải đoán qua dấu "…"
        //  (khách nêu 31/08/2026). Cột số và cột ngày để nguyên một dòng, kẻo
        //  hàng cao lệch nhau nhìn rối. Lưu ý: gắn `truncate` trong `cell` là
        //  vô hiệu hóa `wrap` — class ô con thắng lớp bọc của bảng.
        wrap: true,
        cell: (row) => <span className="font-medium">{row.po_code}</span>,
      },
      { key: 'misa_code', header: 'Mã MISA', width: 120, defaultHidden: true, wrap: true, cell: (r) => r.misa_code || '' },
      { key: 'pr_code', header: 'Mã PYC', width: 130, wrap: true, cell: (r) => r.pr_code || '' },
      { key: 'company', header: 'Công ty', width: 190, wrap: true, cell: (r) => companyName(r.company_id) },
      { key: 'department', header: 'Bộ phận', width: 150, wrap: true, cell: (r) => r.department || '' },
      {
        key: 'supplier_name',
        header: 'Nhà cung cấp',
        width: 230,
        supplierOnly: true,
        wrap: true,
        cell: (r) => r.supplier_name || r.supplier_code || '',
      },
      { key: 'nspt', header: 'NSPT', width: 160, wrap: true, cell: (r) => r.nspt || '' },
      { key: 'order_date', header: 'Ngày ĐH', width: 110, cell: (r) => formatDate(r.order_date) || '' },
      { key: 'product_code', header: 'Mã SP', width: 150, wrap: true, cell: (r) => r.product_code || '' },
      {
        key: 'product_name',
        header: 'Tên SP',
        width: 240,
        wrap: true,
        cell: (r) => r.product_name || '',
      },
      { key: 'item_group', header: 'Nhóm hàng', width: 150, defaultHidden: true, wrap: true, cell: (r) => r.item_group || '' },
      { key: 'unit', header: 'ĐVT', width: 80, cell: (r) => r.unit || '' },
      {
        key: 'qty_order',
        header: 'SL đặt',
        width: 100,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.qty_order) || 0}</span>,
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.price) || 0}</span>,
      },
      {
        key: 'order_amount',
        header: 'Thành tiền ĐH',
        width: 150,
        align: 'right',
        cell: (r) => (
          <span className="font-medium tabular-nums">{formatMoney(r.order_amount) || 0}</span>
        ),
      },
      {
        key: 'progress_status',
        header: 'Tiến độ',
        width: 180,
        cell: (r) => <ProgressStatusBadge status={r.progress_status} />,
      },
      { key: 'delivery_no', header: 'Lần giao', width: 100, align: 'right', defaultHidden: true, cell: (r) => r.delivery_no ?? '' },
      { key: 'warehouse_code', header: 'Kho', width: 120, defaultHidden: true, wrap: true, cell: (r) => r.warehouse_code || '' },
      {
        key: 'carrier_name',
        header: 'Đơn vị VC',
        width: 180,
        defaultHidden: true,
        supplierOnly: true,
        wrap: true,
        cell: (r) => r.carrier_name || '',
      },
      {
        key: 'received_qty',
        header: 'SL nhận',
        width: 110,
        align: 'right',
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.received_qty) || 0}</span>,
      },
      { key: 'received_date', header: 'Ngày nhận', width: 120, cell: (r) => formatDate(r.received_date) || '' },
      // bao-CR-409 (ticket prod 51): hóa đơn được ghi ở LẦN GIAO, không phải ở dòng đơn hàng
      {
        key: 'delivery_invoice_date',
        header: 'Ngày HĐ',
        width: 120,
        cell: (r) => formatDate(r.delivery_invoice_date) || '',
      },
      {
        key: 'diff_regulated',
        header: 'CL quy định',
        width: 120,
        align: 'right',
        defaultHidden: true,
        // Âm = giao trễ so với ngày quy định, dương = sớm.
        cell: (r) => <DiffCell value={r.diff_regulated} />,
      },
      {
        key: 'amount',
        header: 'Thành tiền nhận',
        width: 160,
        align: 'right',
        cell: (r) => (
          <span className="font-medium tabular-nums">{formatMoney(r.amount) || 0}</span>
        ),
      },
      // Ngày giao chứng từ cho kế toán thuộc DÒNG HÀNG — đặt cạnh "Hồ sơ CT" vì có ngày này thì
      // dòng chuyển sang "Đã gửi ĐMH cho KT", tách xa nhau thì hai cột không giải thích cho nhau
      {
        key: 'document_delivery_date',
        header: 'Ngày giao CT cho KT',
        width: 150,
        cell: (r) => formatDate(r.document_delivery_date) || '',
      },
      {
        key: 'document_status',
        header: 'Hồ sơ CT',
        width: 190,
        cell: (r) => <DocumentStatusBadge status={r.document_status} />,
      },
    ]

    return all.filter((column) => !column.supplierOnly || showSupplier)
  }, [showSupplier, companyName])

  //  Cùng một ô chọn dựng HAI lần (hàng ngang ở khổ rộng · tờ trượt ở khổ hẹp).
  //  State nằm ở đây nên hai bản luôn nói cùng một giá trị — khuôn của
  //  `payment-request-list-page`, không phải trùng lặp cần dọn.
  //
  //  `max-md:w-full`: trong tờ trượt mỗi ô có trọn bề ngang màn hình; giữ bề
  //  rộng cứng `w-48` thì ô nép trái và chừa một khoảng trống dài bên phải.
  //  `MultiPicker` tự chiếm trọn bề ngang của thẻ bọc, nên bề rộng cứng đặt ở
  //  lớp `div` bên ngoài chứ không đặt trên ô.
  const companySelect = (
    <div className="w-48 max-md:w-full" aria-label="Lọc theo công ty">
      <MultiPicker
        value={companyIds}
        onChange={setCompanyIds}
        options={(companies?.items ?? []).map((company) => ({
          id: String(company.id),
          label: company.name,
        }))}
        placeholder="Tất cả công ty"
        searchPlaceholder="Tìm công ty…"
        emptyMessage="Không tìm thấy công ty nào."
        contentClassName="w-72"
        summaryInTrigger
        clearInTrigger
      />
    </div>
  )

  const departmentSelect = (
    <Select value={departmentId} onValueChange={setDepartmentId}>
      <SelectTrigger className="w-48 max-md:w-full" aria-label="Lọc theo bộ phận">
        <SelectValue placeholder="Bộ phận" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả bộ phận</SelectItem>
        {(departments?.items ?? []).map((item) => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <div className="w-52 max-md:w-full" aria-label="Lọc theo tiến độ">
      <MultiPicker
        value={statuses}
        onChange={setStatuses}
        options={PO_PROGRESS_STATUS.map((item) => ({ id: item.value, label: item.label }))}
        placeholder="Tất cả tiến độ"
        searchPlaceholder="Tìm tiến độ…"
        emptyMessage="Không tìm thấy tiến độ nào."
        summaryInTrigger
        clearInTrigger
      />
    </div>
  )

  //  Chọn MỐC trước, rồi tới khoảng ngày — đọc xuôi thành một câu "theo ngày
  //  nhận, từ … tới …". Hai ô đứng liền nhau để không ai lọc nhầm mốc mà không
  //  để ý; trong tờ trượt cũng phải giữ đúng thứ tự đó.
  const dateFieldSelect = (
    <Select value={dateField} onValueChange={setDateField}>
      <SelectTrigger className="w-40 max-md:w-full" aria-label="Lọc theo mốc ngày">
        <SelectValue placeholder="Mốc ngày" />
      </SelectTrigger>
      <SelectContent>
        {DATE_FIELDS.map((field) => (
          <SelectItem key={field.value} value={field.value}>
            {field.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const dateRangeInput = (
    <DateRangePicker
      from={dateFrom}
      to={dateTo}
      onChange={setDateRange}
      placeholder="Từ ngày – tới ngày"
      className="max-md:w-full"
    />
  )

  const activeFilterCount =
    [
      companyIds.length > 0,
      departmentId !== ALL,
      statuses.length > 0,
      Boolean(dateFrom || dateTo),
    ].filter(Boolean).length

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật
    //  `payment-request-list-page` và `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Tiến độ mua hàng"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">
            Theo dõi từng lần giao hàng của các dòng đơn mua hàng.
          </span>
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
          getRowId={(row) => `${row.po_id}-${row.product_code}-${row.delivery_no ?? 0}-${row.stt ?? 0}`}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không có dòng tiến độ nào khớp bộ lọc."
          //  Khổ hẹp: THẺ thay bảng — xem `PurchaseProgressCard`.
          mobileCard={(row) => <PurchaseProgressCard row={row} />}
          //  ⚠️ Chạm-để-mở CHỈ bật ở khổ hẹp, và chỉ khi đọc được ĐMH.
          //
          //  Ở chế độ thẻ không còn cột nào là liên kết, nên nếu không có nhịp
          //  này thì từ một dòng tiến độ KHÔNG có đường nào về chứng từ gốc.
          //  Khổ rộng thì ngược lại, bật vào là hỏng: đây là báo cáo 26 cột để
          //  ĐỐI CHIẾU, người ta bôi đen ô để chép số — mà thả chuột sau khi bôi
          //  đen vẫn tính là một cú bấm, tức mỗi lần chép là một lần bị quăng
          //  sang trang khác.
          //
          //  Thiếu quyền đọc ĐMH thì bỏ hẳn, kẻo bấm xong rơi vào màn báo thiếu
          //  quyền — cùng luật `payable-list-page`.
          onRowClick={
            isMobile && can('purchase_order', 'read')
              ? (row) => {
                  if (row.po_id > 0) navigate(appRoutes.procurement.purchaseOrderDetail(row.po_id))
                }
              : undefined
          }
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.purchase-progress"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng',
          }}
          toolbar={
            //  ⚠️ **Khổ điện thoại: năm ô lọc dọn vào TỜ TRƯỢT**, thanh công cụ
            //  còn một hàng. Năm ô khai bề rộng cứng (`w-52`…`w-40`) cộng ô
            //  khoảng ngày, nên ở 390px mỗi ô rơi xuống một hàng riêng: **sáu
            //  hàng ≈ 700px** chắn trên đầu danh sách, tức dòng đầu tiên bắt đầu
            //  dưới mép màn hình.
            <>
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: bản đầy đủ liệt kê sáu thứ tìm
                   được, dài gấp đôi ô, nên bị xén mất đúng phần đuôi — thứ
                   người đọc chưa đoán được.

                   ⚠️ **Đo rồi hãy viết, và đo ở 375px chứ không phải 390px.** Ô
                   tìm ở khổ hẹp chia hàng với nút *Bộ lọc* và nút *Tải lại*, nên
                   chỉ còn **134px** trên máy 390px và hẹp hơn nữa ở iPhone
                   SE/mini — đo ngày 14/09/2026. Lấy ~100px làm trần; ba vế
                   (~134px) khít đúng mép nên vẫn mất dấu `…`. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã ĐMH, MISA, PYC, NCC, NSPT, mã/tên sản phẩm…"
                placeholderShort="Tìm ĐMH, SP…"
                aria-label="Tìm dòng tiến độ mua hàng"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  `QuickFilterSheet` tự mang `md:hidden`, khối bên dưới tự mang
                   `max-md:hidden` — hai vế loại trừ nhau nên không bao giờ có
                   hai bản ô lọc cùng lúc hiện ra. */}
              <QuickFilterSheet
                activeCount={activeFilterCount}
                onClearAll={() => {
                  setCompanyIds([])
                  setDepartmentId(ALL)
                  setStatuses([])
                  setDateField(DEFAULT_DATE_FIELD)
                  setDateRange('', '')
                }}
              >
                <QuickFilterField label="Công ty">{companySelect}</QuickFilterField>
                <QuickFilterField label="Bộ phận">{departmentSelect}</QuickFilterField>
                <QuickFilterField label="Tiến độ">{statusSelect}</QuickFilterField>
                <QuickFilterField label="Mốc ngày">{dateFieldSelect}</QuickFilterField>
                <QuickFilterField label="Khoảng ngày">{dateRangeInput}</QuickFilterField>
              </QuickFilterSheet>

              {/*  `md:contents` chứ không `md:flex`: bọc cụm lọc vào một `div`
                   thì với thanh công cụ nó là MỘT phần tử flex và xuống hàng
                   nguyên khối, đẩy nhóm nút *Tải lại · Cột* xuống một hàng
                   trống. `display: contents` gỡ lớp bọc khỏi bố cục. */}
              <div className="max-md:hidden md:contents">
                {companySelect}
                {departmentSelect}
                {statusSelect}
                {dateFieldSelect}
                {dateRangeInput}
              </div>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}

/** Chênh lệch ngày: âm = trễ (đỏ), dương = sớm (xanh), 0 = đúng hẹn. */
function DiffCell({ value }: { value: number }) {
  return (
    <span
      className={cn(
        'tabular-nums',
        value < 0 && 'text-destructive',
        value > 0 && 'text-success',
        !value && 'text-muted-foreground',
      )}
    >
      {value || 0}
    </span>
  )
}
