import { Download } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { appConfig } from '@/core/config/app-config'
import { usePermission } from '@/core/authorization/use-permission'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
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
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
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
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { downloadFile } from '@/core/api/download-file'
import { SurveyProgressCard } from '../components/survey-progress-card'
import {
  SURVEY_PROGRESS_COLORS,
  SurveyProgressStateBadge,
} from '../components/survey-progress-state-badge'
import { SURVEY_PROGRESS_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { useSurveyProgress } from '../hooks/use-purchase-documents'
import type { SurveyProgressItem } from '../types/survey-progress-types'

const ALL = 'all'

/**
 * Khoảng ngày lọc theo MỐC nào. Ba mốc của một dòng khảo sát lệch nhau cả tuần:
 * tiếp nhận đầu tháng, hạn trả giữa tháng, trả kết quả thật thì có khi sang
 * tháng sau — hỏi nhầm mốc là ra tập khác hẳn chứ không lệch vài dòng.
 *
 * Mặc định là NGÀY TIẾP NHẬN, trùng mốc mà bộ lọc `month` của backend vẫn dùng.
 * Cả ba cặp đều đã có sẵn ở `survey_progress/controller.py`.
 */
const DATE_FIELDS = [
  { value: 'received', label: 'Theo ngày tiếp nhận', from: 'received_date_from', to: 'received_date_to' },
  { value: 'result_due', label: 'Theo hạn trả KQ', from: 'result_due_date_from', to: 'result_due_date_to' },
  { value: 'result', label: 'Theo ngày trả KQ', from: 'result_date_from', to: 'result_date_to' },
] as const

const DEFAULT_DATE_FIELD = DATE_FIELDS[0].value

const FILTER_CONFIG = {
  fields: SURVEY_PROGRESS_FILTER_FIELDS,
  allowConjunctionToggle: true,
  //  Mọi ô lọc trên thanh công cụ. Thiếu tên nào ở đây là bấm "Áp dụng" bộ lọc
  //  nâng cao xong mất luôn ô đó.
  preserveParams: [
    'state',
    'late',
    'date_field',
    'date_from',
    'date_to',
    'sort_by',
    'sort_dir',
  ],
}

export function SurveyProgressPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyProgressContent />
    </FilterProvider>
  )
}

function SurveyProgressContent() {
  const { can } = usePermission()
  const canReadSupplier = can('supplier', 'read')
  const canExport = can('survey_request', 'export')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  // bao-CR-423: ô Tiến độ dòng chọn được NHIỀU nhãn; không chọn gì là "Tất cả".
  // Chọn nhiều nhãn nghĩa là HOẶC — backend hợp điều kiện của từng nhãn lại.
  const [progressStates, setProgressStates] = useUrlMultiParam('state')
  const [late, setLate] = useUrlParamState('late', ALL)
  const [dateField, setDateField] = useUrlParamState('date_field', DEFAULT_DATE_FIELD)
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { queryParams, queryKey } = useFilterQuery()

  const navigate = useNavigate()

  //  Bộ lọc nâng cao: khổ rộng mở bằng nút riêng + popover, khổ hẹp nhúng thẳng
  //  phần ruột vào tờ trượt. Cần `apply`/`reset`/`activeCount` nên phải lấy
  //  context, không chỉ query.
  const filter = useFilterContext()

  //  CÙNG một `useIsMobile` mà `DataTable` dùng để đổi sang thẻ, nên hai bên
  //  không thể lệch nhau: hễ đang bày thẻ thì chạm-để-mở cũng đang bật.
  const isMobile = useIsMobile()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    progressStates,
    late,
    dateField,
    dateFrom,
    dateTo,
  ])

  //  Cặp tham số ngày đã đổi tên theo mốc đang chọn. Tách riêng vì bảng và nút
  //  Xuất Excel phải hỏi CÙNG một tập — xuất ra khác cái đang xem là lỗi ngầm.
  const dateParams: Record<string, string> = {}
  if (dateFrom || dateTo) {
    const field = DATE_FIELDS.find((item) => item.value === dateField) ?? DATE_FIELDS[0]
    if (dateFrom) dateParams[field.from] = dateFrom
    if (dateTo) dateParams[field.to] = dateTo
  }

  const params: ListParams = { page, page_size: pageSize, ...queryParams, ...dateParams }
  if (debouncedValue) params.q = debouncedValue
  //  Gửi nối bằng dấu phẩy — nhãn tiến độ không chứa dấu phẩy nên tách lại được;
  //  `read_multi_param` bên backend đọc cả dạng này lẫn dạng lặp khóa (bao-CR-423).
  if (progressStates.length) params.state = progressStates.join(',')
  if (late !== ALL) params.late = late

  const { data, isLoading, isError } = useSurveyProgress(params)
  const items = data?.items ?? []
  const showSupplier = data?.show_supplier ?? canReadSupplier

  const handleExportExcel = async () => {
    const query = new URLSearchParams()
    if (debouncedValue) query.set('q', debouncedValue)
    if (progressStates.length) query.set('state', progressStates.join(','))
    if (late !== ALL) query.set('late', late)
    for (const [key, value] of Object.entries(dateParams)) query.set(key, value)
    const queryString = query.toString() ? `?${query.toString()}` : ''
    await downloadFile(`/api/survey-progress/export/xlsx${queryString}`, 'tien-do-bao-gia.xlsx')
  }

  const columns = useMemo<DataTableColumn<SurveyProgressItem>[]>(() => {
    const allCols: (DataTableColumn<SurveyProgressItem> & { supplierOnly?: boolean })[] = [
      {
        key: 'code',
        header: 'Mã YCBG',
        width: 150,
        sortable: true,
        defaultPinned: true,
        //  `wrap` cho cột chữ: khách cần ĐỌC ĐỦ, không phải đoán qua dấu "…"
        //  (khách nêu 31/08/2026). Cột số và cột ngày để nguyên một dòng, kẻo
        //  hàng cao lệch nhau nhìn rối. Lưu ý: gắn `truncate` trong `cell` là
        //  vô hiệu hóa `wrap` — class ô con thắng lớp bọc của bảng.
        wrap: true,
        cell: (r) => (
          <Link
            to={`/procurement/survey-requests/${r.sr_id}`}
            className="font-semibold text-primary hover:underline"
          >
            {r.code}
          </Link>
        ),
      },
      { key: 'company', header: 'Công ty', width: 180, sortable: true, wrap: true, cell: (r) => r.company || '' },
      { key: 'department', header: 'Bộ phận', width: 140, sortable: true, wrap: true, cell: (r) => r.department || '' },
      { key: 'requester', header: 'Người yêu cầu', width: 150, sortable: true, wrap: true, cell: (r) => r.requester || '' },
      { key: 'purpose', header: 'Mục đích', width: 190, defaultHidden: true, wrap: true, cell: (r) => r.purpose || '' },
      { key: 'request_date', header: 'Ngày YC', width: 100, defaultHidden: true, cell: (r) => formatDate(r.request_date) || '' },
      { key: 'status', header: 'TT phiếu', width: 110, wrap: true, cell: (r) => r.status || '' },
      { key: 'internal_line_code', header: 'Mã dòng', width: 120, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.internal_line_code || '' },
      { key: 'item_group', header: 'Phân loại', width: 130, sortable: true, wrap: true, cell: (r) => r.item_group || '' },
      { key: 'requirement_detail', header: 'Thông số kỹ thuật', width: 240, wrap: true, cell: (r) => r.requirement_detail || '' },
      { key: 'other_requirement', header: 'Yêu cầu khác', width: 180, defaultHidden: true, wrap: true, cell: (r) => r.other_requirement || '' },
      { key: 'request_qty', header: 'SL dự kiến', width: 100, align: 'right', cell: (r) => <span className="tabular-nums">{formatQuantity(r.request_qty) || 0}</span> },
      { key: 'uom', header: 'ĐVT', width: 70, cell: (r) => r.uom || '' },
      { key: 'proposed_price', header: 'Giá đề xuất', width: 110, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatUnitPrice(r.proposed_price) || 0}</span> },
      { key: 'assignee_name', header: 'NSTM phụ trách', width: 180, wrap: true, cell: (r) => r.assignee_name || '' },
      { key: 'received_date', header: 'Ngày tiếp nhận', width: 120, cell: (r) => formatDate(r.received_date) || '' },
      { key: 'result_due_date', header: 'Hạn trả KQ', width: 110, cell: (r) => formatDate(r.result_due_date) || '' },
      { key: 'result_date', header: 'Ngày trả KQ', width: 110, cell: (r) => formatDate(r.result_date) || '' },
      {
        key: 'days_late',
        header: 'Trễ (ngày)',
        width: 100,
        align: 'right',
        cell: (r) => (r.days_late && r.days_late > 0 ? <span className="font-semibold text-destructive">{r.days_late}</span> : ''),
      },
      { key: 'handling_days', header: 'Số ngày xử lý', width: 110, align: 'right', cell: (r) => r.handling_days ?? '' },
      { key: 'progress_state', header: 'Tiến độ dòng', width: 160, cell: (r) => <SurveyProgressStateBadge state={r.progress_state} /> },
      { key: 'line_status', header: 'TT dòng', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.line_status || '' },
      { key: 'option_count', header: 'Số PA', width: 80, align: 'right', cell: (r) => r.option_count ?? 0 },
      { key: 'opt_label', header: 'Phương án chốt', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_label || '' },
      { key: 'opt_supplier_code', header: 'Mã NCC', width: 120, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_supplier_code || '' },
      { key: 'opt_supplier_name', header: 'Nhà cung cấp', width: 220, supplierOnly: true, wrap: true, cell: (r) => r.opt_supplier_name || '' },
      { key: 'opt_internal_code', header: 'Mã SP theo NCC', width: 140, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_internal_code || '' },
      { key: 'opt_product_code', header: 'Mã SP hệ thống', width: 140, defaultHidden: true, wrap: true, cell: (r) => r.opt_product_code || '' },
      { key: 'opt_product_name', header: 'Tên SP báo giá', width: 220, wrap: true, cell: (r) => <span className="font-medium">{r.opt_product_name || ''}</span> },
      { key: 'opt_spec', header: 'Quy cách', width: 190, defaultHidden: true, wrap: true, cell: (r) => r.opt_spec || '' },
      { key: 'opt_origin', header: 'Xuất xứ', width: 110, defaultHidden: true, wrap: true, cell: (r) => r.opt_origin || '' },
      { key: 'opt_quote_unit', header: 'ĐVT báo giá', width: 100, defaultHidden: true, wrap: true, cell: (r) => r.opt_quote_unit || '' },
      { key: 'opt_moq', header: 'SL tối thiểu', width: 100, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatQuantity(r.opt_moq) || 0}</span> },
      { key: 'opt_price', header: 'Đơn giá báo', width: 120, align: 'right', cell: (r) => <span className="font-semibold tabular-nums">{formatUnitPrice(r.opt_price) || 0}</span> },
      { key: 'opt_volume_range', header: 'Khoảng SL áp giá', width: 140, defaultHidden: true, wrap: true, cell: (r) => r.opt_volume_range || '' },
      { key: 'opt_vat', header: 'VAT%', width: 70, align: 'right', defaultHidden: true, cell: (r) => r.opt_vat ?? 0 },
      { key: 'opt_delivery_time', header: 'Thời gian giao', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_delivery_time || '' },
      { key: 'opt_delivery_place', header: 'Nơi giao', width: 160, defaultHidden: true, wrap: true, cell: (r) => r.opt_delivery_place || '' },
      { key: 'opt_shipping_cost', header: 'Phí vận chuyển', width: 120, align: 'right', defaultHidden: true, cell: (r) => <span className="tabular-nums">{formatMoney(r.opt_shipping_cost) || 0}</span> },
      { key: 'opt_sample_ready', header: 'Có mẫu', width: 80, defaultHidden: true, cell: (r) => (r.opt_sample_ready ? 'Có' : '') },
      { key: 'opt_lab_result', header: 'KQ kiểm nghiệm', width: 130, defaultHidden: true, wrap: true, cell: (r) => r.opt_lab_result || '' },
      { key: 'opt_note', header: 'Ghi chú NSTM', width: 190, defaultHidden: true, supplierOnly: true, wrap: true, cell: (r) => r.opt_note || '' },
    ]

    return allCols.filter((col) => !col.supplierOnly || showSupplier)
  }, [showSupplier])

  //  Cùng một ô chọn dựng HAI lần (hàng ngang ở khổ rộng · tờ trượt ở khổ hẹp).
  //  State nằm ở đây nên hai bản luôn nói cùng một giá trị — khuôn của
  //  `purchase-progress-page`, không phải trùng lặp cần dọn.
  //
  //  `max-md:w-full`: trong tờ trượt mỗi ô có trọn bề ngang màn hình; giữ bề
  //  rộng cứng `w-48` thì ô nép trái và chừa một khoảng trống dài bên phải.
  //  `MultiPicker` tự chiếm trọn bề ngang của thẻ bọc, nên bề rộng cứng đặt ở
  //  lớp `div` bên ngoài chứ không đặt trên ô.
  const stateSelect = (
    <div className="w-48 max-md:w-full" aria-label="Lọc theo tiến độ dòng">
      <MultiPicker
        value={progressStates}
        onChange={setProgressStates}
        options={Object.keys(SURVEY_PROGRESS_COLORS).map((st) => ({ id: st, label: st }))}
        placeholder="Tất cả tiến độ"
        searchPlaceholder="Tìm tiến độ…"
        emptyMessage="Không tìm thấy tiến độ nào."
        summaryInTrigger
        clearInTrigger
      />
    </div>
  )

  const lateSelect = (
    <Select value={late} onValueChange={setLate}>
      <SelectTrigger className="w-36 max-md:w-full" aria-label="Lọc theo trễ hạn">
        <SelectValue placeholder="Trễ hạn" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả</SelectItem>
        <SelectItem value="1">Trễ hạn</SelectItem>
        <SelectItem value="0">Đúng hạn</SelectItem>
      </SelectContent>
    </Select>
  )

  //  Chọn MỐC trước, rồi tới khoảng ngày — đọc xuôi thành một câu "theo hạn trả
  //  KQ, từ … tới …". Hai ô đứng liền nhau để không ai lọc nhầm mốc mà không để
  //  ý; trong tờ trượt cũng phải giữ đúng thứ tự đó.
  const dateFieldSelect = (
    <Select value={dateField} onValueChange={setDateField}>
      <SelectTrigger className="w-48 max-md:w-full" aria-label="Lọc theo mốc ngày">
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

  //  Huy hiệu trên nút «Bộ lọc» của khổ hẹp đếm CẢ HAI tầng — ô lọc nhanh và
  //  điều kiện nâng cao — vì cả hai nay nằm sau đúng một nút đó. Đếm thiếu một
  //  tầng thì người dùng thấy nút không dấu gì mà danh sách vẫn đang bị lọc.
  const activeFilterCount =
    [progressStates.length > 0, late !== ALL, Boolean(dateFrom || dateTo)].filter(Boolean).length +
    filter.activeCount

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật
    //  `purchase-progress-page` và `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Tiến độ báo giá"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">
            Theo dõi tiến độ xử lý từng dòng yêu cầu báo giá.
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp — cụm nút bọc thêm một lớp `div` nên phải
        //  nhắm `[&>div]`, `[&>button]` không chạm tới.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          canExport ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-9 max-md:flex-1"
                onClick={handleExportExcel}
              >
                <Download className="mr-1.5 size-4" />
                Xuất Excel
              </Button>
            </div>
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
          rows={items}
          getRowId={(row) => `${row.sr_id}-${row.code}-${row.stt || 0}`}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy dữ liệu tiến độ báo giá."
          //  Khổ hẹp: THẺ thay bảng — xem `SurveyProgressCard`.
          mobileCard={(row) => <SurveyProgressCard row={row} />}
          //  ⚠️ Chạm-để-mở CHỈ bật ở khổ hẹp, và chỉ khi đọc được YCBG.
          //
          //  Ở chế độ thẻ cột *Mã YCBG* không còn là liên kết, nên nếu không có
          //  nhịp này thì từ một dòng tiến độ KHÔNG có đường nào về chứng từ
          //  gốc. Khổ rộng thì ngược lại, bật vào là hỏng: đây là báo cáo 45 cột
          //  để ĐỐI CHIẾU, người ta bôi đen ô để chép số — mà thả chuột sau khi
          //  bôi đen vẫn tính là một cú bấm, tức mỗi lần chép là một lần bị
          //  quăng sang trang khác.
          //
          //  Thiếu quyền đọc YCBG thì bỏ hẳn, kẻo bấm xong rơi vào màn báo thiếu
          //  quyền — cùng luật `purchase-progress-page`.
          onRowClick={
            isMobile && can('survey_request', 'read')
              ? (row) => {
                  if (row.sr_id > 0) {
                    navigate(appRoutes.procurement.surveyRequestDetail(row.sr_id))
                  }
                }
              : undefined
          }
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.survey-progress"
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'dòng',
          }}
          toolbar={
            //  ⚠️ **Khổ điện thoại: bốn ô lọc dọn vào TỜ TRƯỢT**, thanh công cụ
            //  còn một hàng. Bốn ô khai bề rộng cứng (`w-48`…`w-36`) cộng ô
            //  khoảng ngày, nên ở 390px mỗi ô rơi xuống một hàng riêng: **năm
            //  hàng ≈ 600px** chắn trên đầu danh sách, tức dòng đầu tiên bắt đầu
            //  dưới mép màn hình.
            <>
              {/*  Câu gợi ý RÚT GỌN ở khổ hẹp: bản đầy đủ liệt kê bốn thứ tìm
                   được nên bị xén giữa chừng, mất đúng phần đuôi — thứ người
                   đọc chưa đoán được.

                   ⚠️ **Đo rồi hãy viết.** Ô tìm ở khổ hẹp chia hàng với nút *Bộ
                   lọc* và nút *Tải lại*, nên chỉ còn **~134px** — đo ngày
                   14/09/2026 trên máy 390px. Hai vế (~100px) là vừa; ba vế
                   (~139px) vẫn bị xén, tức bản "rút gọn" không giải quyết được
                   gì so với bản đầy đủ. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã YCBG, SP, NCC, NSTM…"
                placeholderShort="Tìm YCBG, SP…"
                aria-label="Tìm dòng tiến độ báo giá"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  `md:contents` chứ KHÔNG phải `md:flex`: bọc cụm lọc trong một
                   thẻ flex riêng thì với thanh công cụ nó là MỘT ô, không đủ chỗ
                   là rớt nguyên khối xuống dòng dưới và chừa khoảng trống dài
                   bên phải ô tìm kiếm. */}
              <div className="max-md:hidden md:contents">
                {stateSelect}
                {lateSelect}
                {dateFieldSelect}
                {dateRangeInput}
                <ConditionalFilter />
              </div>

              {/*  ⚠️ Ô trong tờ trượt phải có NHÃN. Trên thanh công cụ, ô chọn tự
                   giải nghĩa bằng giá trị đang chọn («Tất cả tiến độ»); xếp dọc
                   mấy ô như vậy trong một tờ trắng thì thành danh sách chữ trôi
                   nổi, người đọc không biết ô nào lọc cái gì cho tới khi bấm
                   thử. Riêng ô «Trễ hạn» thì nhãn là BẮT BUỘC: giá trị mặc định
                   của nó đọc trơ trọi là «Tất cả», không nói được tất cả cái gì. */}
              <QuickFilterSheet
                activeCount={activeFilterCount}
                onClearAll={() => {
                  setProgressStates([])
                  setLate(ALL)
                  setDateField(DEFAULT_DATE_FIELD)
                  setDateRange('', '')
                  filter.reset()
                }}
                onApply={filter.apply}
              >
                <QuickFilterField label="Tiến độ dòng">{stateSelect}</QuickFilterField>
                <QuickFilterField label="Trễ hạn">{lateSelect}</QuickFilterField>
                <QuickFilterField label="Mốc ngày">{dateFieldSelect}</QuickFilterField>
                <QuickFilterField label="Khoảng ngày">{dateRangeInput}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
