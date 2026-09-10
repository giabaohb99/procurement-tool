import { CircleX, Plus } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { useUrlSort } from '@/shared/hooks/use-url-sort'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { DepartmentFormDialog } from '../components/department-form-dialog'
import { DEPARTMENT_COLUMNS } from '../config/department-columns'
import { DEPARTMENT_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { DEPARTMENT_KIND_LABELS, DEPARTMENT_KIND_OPTIONS, type Department } from '../types/department'

const ALL = 'all'

/** `preserveParams`: giữ ba select của thanh công cụ trên URL khi áp bộ lọc nâng cao. */
const FILTER_CONFIG = {
  fields: DEPARTMENT_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['is_active', 'kind', 'company_id', 'sort_by', 'sort_dir'],
}

export function DepartmentListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <DepartmentListContent />
    </FilterProvider>
  )
}

/**
 * Danh mục phòng ban.
 *
 * Thanh công cụ giữ ô tìm chung + select Trạng thái. Mã / Tên phòng ban với đầy
 * đủ phép so sánh nằm ở "Bộ lọc" nâng cao.
 */
function DepartmentListContent() {
  const navigate = useNavigate()

  const { can } = usePermission()
  //  Ô chọn Pháp nhân mượn danh mục của phân hệ khác (`company.read`). Thiếu
  //  quyền là cứ mount lên gọi API rồi ăn toast 403 chẳng liên quan gì tới việc
  //  đang làm — nên vừa tắt query vừa giấu luôn ô chọn.
  const canReadCompany = can('company', 'read')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [kind, setKind] = useUrlParamState('kind', ALL)
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isFormOpen, setFormOpen] = useState(false)
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)
  const isMobile = useIsMobile()

  const { data: companies } = useCompanies({ page_size: 500 }, { enabled: canReadCompany })
  const { queryParams, queryKey } = useFilterQuery()
  //  Bộ lọc nâng cao: đếm để gắn huy hiệu lên nút «Bộ lọc», và hai hàm để nút
  //  «Xóa lọc» / «Áp dụng» của tờ trượt điều khiển được nó.
  const {
    activeCount: filterActiveCount,
    reset: filterReset,
    apply: filterApply,
  } = useFilterContext()

  //  Bảng đang bị thu hẹp bởi BẤT KỲ đường nào — quyết định câu nói khi rỗng.
  const isFiltering =
    Boolean(debouncedValue) ||
    active !== ALL ||
    kind !== ALL ||
    companyId !== ALL ||
    filterActiveCount > 0

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    active,
    kind,
    companyId,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  // `q` là tham số RIÊNG của endpoint này: khớp tên phòng ban HOẶC tên trưởng
  // bộ phận (join sang bảng nhân sự). Không phải cột trong whitelist filter.
  if (debouncedValue) params.q = debouncedValue
  if (active !== ALL) params.is_active = active === 'true'
  if (kind !== ALL) params.kind = Number(kind)
  if (companyId !== ALL) params.company_id = Number(companyId)
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useDepartments(params)

  //  Ba ô lọc dựng MỘT LẦN, bày ở HAI chỗ: hàng ngang của thanh công cụ từ
  //  `md`, tờ trượt lọc ở dưới ngưỡng đó. State nằm trên URL nên hai bản luôn
  //  nói cùng một giá trị. Bề rộng cứng chỉ áp từ `md` — trong tờ trượt mỗi ô
  //  có trọn bề ngang màn hình.
  const kindSelect = (
    <Select value={kind} onValueChange={setKind}>
      <SelectTrigger className="w-full md:w-52" aria-label="Lọc theo loại đơn vị">
        <SelectValue placeholder="Loại đơn vị" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả loại đơn vị</SelectItem>
        {DEPARTMENT_KIND_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={String(option.value)}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  Ô Pháp nhân mượn danh mục của phân hệ khác — thiếu `company.read` thì giấu
  //  hẳn, xem ghi chú ở `canReadCompany`.
  const companySelect = canReadCompany && (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="w-full md:w-52" aria-label="Lọc theo pháp nhân">
        <SelectValue placeholder="Pháp nhân" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả pháp nhân</SelectItem>
        {(companies?.items ?? []).map((company) => (
          <SelectItem key={company.id} value={String(company.id)}>
            {company.short_name || company.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const activeSelect = (
    <Select value={active} onValueChange={setActive}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
        <SelectItem value="true">Hoạt động</SelectItem>
        <SelectItem value="false">Đã ẩn</SelectItem>
      </SelectContent>
    </Select>
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi thành danh sách thẻ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Phòng ban"
        //  Dòng mô tả ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi,
        //  nhưng ngốn hai dòng ở đầu MỌI lần mở màn.
        description={
          <span className="max-md:hidden">Cơ cấu tổ chức và trưởng bộ phận của từng phòng.</span>
        }
        actions={
          //  Khổ hẹp: nút chiếm trọn hàng — hành động chính phải là thứ dễ chạm nhất.
          <PermissionGate entity="department" action="create">
            <Button className="max-md:w-full" onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «đã cuộn» xuống thanh
           công cụ ghim (do `DataTable` vẽ, tầng này không với tới bằng prop). */}
      <div
        ref={stickyRef}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
      <Card className="flex min-h-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          fillHeight
          columns={DEPARTMENT_COLUMNS}
          rows={data?.items}
          getRowId={(department) => department.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì chưa có gì: một câu chung cho
            //  cả hai thì người vừa gõ nhầm một chữ đọc ra "chưa có dữ liệu".
            isFiltering
              ? 'Không có phòng ban nào khớp bộ lọc.'
              : 'Chưa có phòng ban nào. Bấm «Thêm mới» để tạo.'
          }
          storageKey="hr.departments"
          //  Khổ hẹp: THẺ thay bảng. Bảng khai 7 cột, bề rộng tự nhiên ~1360px —
          //  trên máy 390px chỉ thấy *Mã* và *Mã số hiệu*, tức hai cột KHÔNG dùng
          //  để nhận ra một phòng ban; tên phòng và trưởng bộ phận đều nằm sau
          //  một lượt cuộn ngang.
          //
          //  ⚠️ Thẻ chỉ nói cái BẤT THƯỜNG: huy hiệu trạng thái tắt khi *Hoạt
          //  động*, chỉ lên tiếng ở phòng *Đã ẩn* — thứ người quản lý danh mục
          //  cần nhặt ra.
          mobileCard={(d: Department) => (
            <CrudRecordCard
              title={d.name}
              subtitle={
                <>
                  <span className="block truncate">
                    {d.code} · {DEPARTMENT_KIND_LABELS[d.kind]}
                  </span>
                  <span className="block truncate">
                    {d.manager_name ? `Trưởng BP: ${d.manager_name}` : 'Chưa có trưởng bộ phận'}
                  </span>
                </>
              }
              chips={d.is_active ? [] : [{ icon: CircleX, text: 'Đã ẩn', tone: 'muted' as const }]}
            />
          )}
          //  Danh sách thẻ dài hơn một màn và CẢ TRANG cuộn, nên không ghim thì
          //  ô tìm trôi mất ngay nhịp vuốt đầu.
          toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
          onRowClick={(d) => navigate(appRoutes.hr.departmentDetail(d.id))}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'phòng ban',
          }}
          toolbar={
            <>
              {/*  ⚠️ Câu gợi ý rút gọn ở khổ hẹp và đo theo lúc ĐANG LỌC: nút
                   *Bộ lọc* nở thêm 24px khi mọc huy hiệu số. Bản cũ «Tìm theo
                   tên phòng ban hoặc trưởng bộ phận…» dài gấp ba chỗ có. Bản
                   đầy đủ giữ từ `md`. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder={
                  isMobile ? 'Tìm phòng ban…' : 'Tìm theo tên phòng ban hoặc trưởng bộ phận…'
                }
                className="max-md:min-w-40 md:w-64 md:max-w-sm md:flex-none"
              />

              {/*  Khổ hẹp: ba ô lọc + bộ lọc nâng cao dọn hết vào tờ trượt, hàng
                   công cụ còn một dòng. Bản cũ để bốn ô bề rộng CỨNG trong một
                   thẻ rộng 322px nên mỗi ô rớt xuống một hàng riêng — năm hàng
                   dài ngắn khác nhau xếp thành bậc thang. */}
              <QuickFilterSheet
                activeCount={
                  (kind !== ALL ? 1 : 0) +
                  (companyId !== ALL ? 1 : 0) +
                  (active !== ALL ? 1 : 0) +
                  filterActiveCount
                }
                onClearAll={() => {
                  setKind(ALL)
                  setCompanyId(ALL)
                  setActive(ALL)
                  filterReset()
                }}
                onApply={filterApply}
              >
                <QuickFilterField label="Loại đơn vị">{kindSelect}</QuickFilterField>
                {companySelect && (
                  <QuickFilterField label="Pháp nhân">{companySelect}</QuickFilterField>
                )}
                <QuickFilterField label="Trạng thái">{activeSelect}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex">
                {kindSelect}
                {companySelect}
                {activeSelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>
      </div>

      <DepartmentFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
