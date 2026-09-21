import { Copy, Plus } from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import { httpClient } from '@/core/api/http-client'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Badge } from '@/shared/ui/badge'
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
import { SearchSelect } from '@/shared/ui/search-select'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import { formatDateTime } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { SurveyCard } from '../components/survey-card'
import { SURVEY_FILTER_FIELDS } from '../config/procurement-filter-fields'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
import { useSurveys } from '../hooks/use-purchase-documents'
import {
  SURVEY_STATUS_LABELS,
  SURVEY_TYPE_LABELS,
  statusOptions,
  type Survey,
} from '../types/purchase-document'

const ALL = 'all'

const FILTER_CONFIG = {
  fields: SURVEY_FILTER_FIELDS,
  allowConjunctionToggle: true,
  //  `product_code` từng nằm đây nhưng màn không có ô nào ghi nó — bản v1 có ô
  //  «Mã SP (NCC)» riêng, còn ở đây ô tìm kiếm đã gánh luôn phần đó (backend đọc
  //  `code` / `q` / `search` / `product_code` vào CÙNG một câu tìm đa trường).
  preserveParams: ['status', 'survey_type', 'item_group', 'sort_by', 'sort_dir'],
}

export function SurveyListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <SurveyListContent />
    </FilterProvider>
  )
}

function SurveyListContent() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { can } = usePermission()
  const canCreate = can('survey', 'create')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [surveyType, setSurveyType] = useUrlParamState('survey_type', ALL)
  //  Nhóm hàng lọc theo TÊN, không phải id — `Survey.item_group` lưu tên nhóm
  //  (bảng chưa có cột `item_group_id`), giống hệt ô cùng tên ở bản v1.
  const [itemGroup, setItemGroup] = useUrlParamState('item_group', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const { data: itemGroups } = usePurchaseRequestItemGroups()

  const sortBy = searchParams.get('sort_by') || ''
  const sortDir = (searchParams.get('sort_dir') as 'asc' | 'desc') || 'asc'

  const { queryParams, queryKey } = useFilterQuery()

  //  Bộ lọc nâng cao: khổ rộng mở bằng nút riêng + popover, khổ hẹp nhúng
  //  thẳng phần ruột vào tờ trượt. Cần `apply`/`reset`/`activeCount` nên phải
  //  lấy context, không chỉ query.
  const filter = useFilterContext()

  //  Mốc bóng đổ cho thanh công cụ ghim ở khổ hẹp — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    status,
    surveyType,
    itemGroup,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.code = debouncedValue
  if (status !== ALL) params.status = status
  if (surveyType !== ALL) params.survey_type = surveyType
  if (itemGroup !== ALL) params.item_group = itemGroup
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useSurveys(params)

  // KHÔNG có nút Xuất Excel ở màn này: backend chưa có route `/api/surveys/export/xlsx`
  // (bấm là 404), và bản v1 cũng không xuất được danh sách phiếu khảo sát.

  const handleClone = useCallback(
    async (survey: Survey, e: React.MouseEvent) => {
      e.stopPropagation()
      try {
        const res = await httpClient.post<{ data: { id: number } }>(`/api/surveys/${survey.id}/clone`)
        toast.success('Đã nhân bản phiếu khảo sát')
        const newId = res.data?.data?.id
        if (newId) navigate(appRoutes.procurement.surveyDetail(newId))
      } catch {
        toast.error('Nhân bản phiếu khảo sát thất bại')
      }
    },
    [navigate],
  )

  //  Huy hiệu trên nút «Bộ lọc» của khổ hẹp đếm CẢ HAI tầng — ô lọc nhanh và
  //  điều kiện nâng cao — vì cả hai nay nằm sau đúng một nút đó. Đếm thiếu một
  //  tầng thì người dùng thấy nút không dấu gì mà danh sách vẫn đang bị lọc.
  const activeCount =
    [status !== ALL, surveyType !== ALL, itemGroup !== ALL].filter(Boolean).length +
    filter.activeCount

  const clearAllFilters = () => {
    setStatus(ALL)
    setSurveyType(ALL)
    setItemGroup(ALL)
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

  const columns = useMemo<DataTableColumn<Survey>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 160,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (survey) => <span className="truncate font-medium">{survey.code}</span>,
      },
      {
        key: 'survey_type',
        header: 'Loại',
        //  Đủ chỗ cho nhãn dài nhất "Khảo sát NCC & SP" mà không cắt chữ.
        width: 170,
        sortable: true,
        cell: (survey) => (
          <Badge variant="outline">
            {SURVEY_TYPE_LABELS[survey.survey_type] ?? survey.survey_type}
          </Badge>
        ),
      },
      { key: 'sr_code', header: 'Mã YCBG', width: 140, cell: (survey) => survey.sr_code || '' },
      {
        key: 'main_content',
        header: 'Nội dung chính',
        width: 280,
        cell: (survey) => (
          <span className="truncate" title={survey.main_content}>
            {survey.main_content || ''}
          </span>
        ),
      },
      { key: 'item_code', header: 'Mã hàng', width: 140, cell: (survey) => survey.item_code || '' },
      {
        key: 'item_group',
        header: 'Nhóm hàng',
        width: 160,
        cell: (survey) => survey.item_group || '',
      },
      { key: 'nspt', header: 'NSPT', width: 170, cell: (survey) => survey.nspt || '' },
      {
        key: 'created_at',
        header: 'Ngày tạo',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (survey) => formatDateTime(survey.created_at) || '',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        sortable: true,
        cell: (survey) => <StatusBadge status={survey.status} labels={SURVEY_STATUS_LABELS} />,
      },
      {
        // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
        key: 'updated_at',
        header: 'Ngày cập nhật',
        width: 150,
        sortable: true,
        sortDescFirst: true,
        cell: (survey) => formatDateTime(survey.updated_at) || '',
      },
      {
        key: 'actions',
        header: '',
        width: 60,
        hideable: false,
        cell: (survey) =>
          canCreate ? (
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản phiếu khảo sát"
              onClick={(e) => handleClone(survey, e)}
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
  //  `payment-request-list-page`, không phải trùng lặp cần dọn.
  const typeSelect = (
    <Select value={surveyType} onValueChange={setSurveyType}>
      <SelectTrigger className="h-9 w-full text-xs md:w-44" aria-label="Lọc theo loại khảo sát">
        <SelectValue placeholder="Loại khảo sát" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại</SelectItem>
        {Object.entries(SURVEY_TYPE_LABELS).map(([k, v]) => (
          <SelectItem key={k} value={k}>
            {v}
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
        {statusOptions(SURVEY_STATUS_LABELS).map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  Danh mục nhóm hàng vài chục dòng — nạp một lần rồi lọc tại chỗ, không cần
  //  tra phía server. `value` là TÊN nhóm vì backend so bằng tên.
  //
  //  ⚠️ Nhãn đặt ở thẻ BỌC, không truyền `aria-label` cho `SearchSelect`:
  //  component không spread prop lạ nên thuộc tính có gạch ngang lọt `tsc` rồi
  //  rơi vào hư không — đúng cái bẫy ghi trong chính tệp `search-select.tsx`.
  const itemGroupSelect = (
    <div className="w-full md:w-44" aria-label="Lọc theo nhóm hàng">
      <SearchSelect
        value={itemGroup === ALL ? '' : itemGroup}
        onChange={(value) => setItemGroup(value || ALL)}
        options={(itemGroups?.items ?? []).map((group) => ({
          value: group.name,
          label: group.name,
        }))}
        placeholder="Tất cả nhóm hàng"
        searchPlaceholder="Tìm nhóm hàng…"
        emptyMessage="Không tìm thấy nhóm hàng nào."
        clearable
        size="sm"
      />
    </div>
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi sang danh sách THẺ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng luật
    //  `payment-request-list-page` và `CrudListPage`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Phiếu khảo sát"
        description={
          //  Ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi, nhưng ngốn
          //  hai dòng ở đầu MỌI lần mở màn — ngay trên thứ người ta vào đây để
          //  xem.
          <span className="max-md:hidden">
            Khảo sát nhà cung cấp và sản phẩm phục vụ so sánh giá.
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp — cụm nút bọc thêm một lớp `div` nên phải
        //  nhắm `[&>div]`, `[&>button]` không chạm tới.
        actionsClassName="max-md:[&>div]:w-full"
        actions={
          <div className="flex items-center gap-2">
            <PermissionGate entity="survey" action="create">
              <Button
                className="max-md:flex-1"
                onClick={() => navigate(appRoutes.procurement.surveyNew)}
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
          getRowId={(survey) => survey.id}
          onRowClick={(survey) => navigate(appRoutes.procurement.surveyDetail(survey.id))}
          isLoading={isLoading}
          isError={isError}
          emptyMessage="Không tìm thấy phiếu khảo sát nào."
          //  Khổ hẹp: THẺ thay bảng — xem `SurveyCard`.
          //
          //  ⚠️ Nút *Nhân bản* của cột thao tác KHÔNG theo sang thẻ: bảng khai
          //  `onRowClick` nên thẻ bị bọc trong một `<button>`, lồng nút vào là
          //  HTML sai. Nhân bản là việc hiếm và vẫn làm được ở khổ rộng.
          mobileCard={(survey) => <SurveyCard row={survey} />}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.surveys"
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
                   được nên bị xén giữa chừng, mất đúng phần đuôi — thứ người
                   đọc chưa đoán được.

                   ⚠️ **Đo rồi hãy viết.** Ô tìm ở khổ hẹp chia hàng với nút *Bộ
                   lọc* và nút *Tải lại*, nên chỉ còn **134px** — đo ngày
                   14/09/2026 trên máy 390px. Hai vế (~99px) là vừa; ba vế
                   (~137px) vẫn bị xén, tức bản "rút gọn" không giải quyết được
                   gì so với bản đầy đủ. Câu đủ vẫn còn ở khổ rộng và ở
                   `aria-label`. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm mã phiếu, mã SP, tên SP, mã NCC…"
                placeholderShort="Tìm phiếu, SP…"
                aria-label="Tìm phiếu khảo sát"
                className="md:min-w-56 md:max-w-xs"
              />

              {/*  `md:contents` chứ KHÔNG phải `md:flex`: bọc cụm lọc trong một thẻ
                   flex riêng thì với thanh công cụ nó là MỘT ô, không đủ chỗ là
                   rớt nguyên khối xuống dòng dưới và chừa khoảng trống dài bên
                   phải ô tìm kiếm. Màn Đơn mua hàng đã vỡ đúng kiểu đó khi thêm
                   ô lọc thứ sáu (bao-CR-319). */}
              <div className="hidden md:contents">
                {typeSelect}
                {itemGroupSelect}
                {statusSelect}
                <ConditionalFilter />
              </div>

              {/*  ⚠️ Ô trong tờ trượt phải có NHÃN. Trên thanh công cụ, ô chọn tự
                   giải nghĩa bằng giá trị đang chọn («Tất cả loại»); xếp dọc mấy
                   ô như vậy trong một tờ trắng thì thành danh sách chữ trôi nổi,
                   người đọc không biết ô nào lọc cái gì cho tới khi bấm thử. */}
              <QuickFilterSheet
                activeCount={activeCount}
                onClearAll={clearAllFilters}
                onApply={filter.apply}
              >
                <QuickFilterField label="Loại khảo sát">{typeSelect}</QuickFilterField>
                <QuickFilterField label="Nhóm hàng">{itemGroupSelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
