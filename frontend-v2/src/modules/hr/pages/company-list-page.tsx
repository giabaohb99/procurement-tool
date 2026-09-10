import { Plus } from 'lucide-react'
import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appConfig } from '@/core/config/app-config'
import {
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
  useFilterQuery,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useIsMobile } from '@/shared/hooks/use-mobile'
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
import { CompanyCard } from '../components/company-card'
import { CompanyFormDialog } from '../components/company-form-dialog'
import { COMPANY_COLUMNS } from '../config/company-columns'
import { COMPANY_FILTER_FIELDS } from '../config/hr-filter-fields'
import { useCompanies } from '../hooks/use-companies'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { COMPANY_LEVEL_OPTIONS, type Company } from '../types/company'

const ALL = 'all'

/** `preserveParams`: giữ hai select của thanh công cụ trên URL khi áp bộ lọc nâng cao. */
const FILTER_CONFIG = {
  fields: COMPANY_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['is_active', 'level', 'sort_by', 'sort_dir'],
}

export function CompanyListPage() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <CompanyListContent />
    </FilterProvider>
  )
}

/**
 * Danh mục pháp nhân.
 *
 * Thanh công cụ giữ ô tìm theo tên + select Trạng thái; Mã công ty và Mã số
 * thuế đưa vào "Bộ lọc" nâng cao.
 */
function CompanyListContent() {
  const navigate = useNavigate()

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [active, setActive] = useUrlParamState('is_active', ALL)
  const [level, setLevel] = useUrlParamState('level', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [isFormOpen, setFormOpen] = useState(false)
  const { sortBy, sortDir, handleSortChange } = useUrlSort()
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const { queryParams, queryKey } = useFilterQuery()
  //  Bộ lọc nâng cao: đếm để gắn huy hiệu lên nút «Bộ lọc», và hai hàm để nút
  //  «Xóa lọc» / «Áp dụng» của tờ trượt điều khiển được nó.
  const {
    activeCount: filterActiveCount,
    reset: filterReset,
    apply: filterApply,
  } = useFilterContext()
  const isMobile = useIsMobile()

  //  Bảng đang bị thu hẹp bởi BẤT KỲ đường nào — quyết định câu nói khi rỗng.
  const isFiltering =
    Boolean(debouncedValue) || active !== ALL || level !== ALL || filterActiveCount > 0

  const [page, setPage] = usePageResetOnFilterChange([
    queryKey,
    debouncedValue,
    active,
    level,
    sortBy,
    sortDir,
  ])

  const params: ListParams = { page, page_size: pageSize, ...queryParams }
  if (debouncedValue) params.name = debouncedValue
  if (active !== ALL) params.is_active = active === 'true'
  if (level !== ALL) params.level = Number(level)
  if (sortBy) {
    params.sort_by = sortBy
    params.sort_dir = sortDir
  }

  const { data, isLoading, isError } = useCompanies(params)

  //  Hai ô lọc dựng MỘT LẦN, bày ở HAI chỗ: hàng ngang của thanh công cụ từ
  //  `md`, tờ trượt lọc ở dưới ngưỡng đó. State nằm trên URL nên hai bản luôn
  //  nói cùng một giá trị. Bề rộng cứng chỉ áp từ `md` — trong tờ trượt mỗi ô
  //  có trọn bề ngang màn hình.
  const levelSelect = (
    <Select value={level} onValueChange={setLevel}>
      <SelectTrigger className="w-full md:w-52" aria-label="Lọc theo cấp pháp nhân">
        <SelectValue placeholder="Cấp pháp nhân" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả cấp</SelectItem>
        {COMPANY_LEVEL_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={String(option.value)}>
            {option.label}
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
        <SelectItem value="true">Đang dùng</SelectItem>
        <SelectItem value="false">Ngừng</SelectItem>
      </SelectContent>
    </Select>
  )

  return (
    //  ⚠️ `fill` chỉ bật từ `md`: ở khổ hẹp bảng đổi thành danh sách thẻ dài, mà
    //  `fill` nhét nó vào một khe vài trăm pixel và biến thành cuộn LỒNG — vuốt
    //  trúng mép ngoài khe thì trang không nhúc nhích. Cùng bài học với
    //  `CrudListPage` và `leave-balance-page`.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Công ty"
        //  Dòng mô tả ẩn ở khổ hẹp: câu giới thiệu màn, đọc một lần rồi thôi,
        //  nhưng ngốn hai dòng ở đầu MỌI lần mở màn — ngay phía trên thứ người
        //  ta thật sự vào đây để xem.
        description={
          <span className="max-md:hidden">
            Danh mục pháp nhân: mã số thuế, người đại diện, thông tin hóa đơn.
          </span>
        }
        actions={
          //  Khổ hẹp: nút chiếm trọn hàng — hành động chính của màn phải là thứ
          //  dễ chạm nhất.
          <PermissionGate entity="company" action="create">
            <Button className="max-md:w-full" onClick={() => setFormOpen(true)}>
              <Plus />
              Thêm mới
            </Button>
          </PermissionGate>
        }
      />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «đã cuộn» xuống thanh
           công cụ ghim (do `DataTable` vẽ, tầng này không với tới bằng prop) —
           bóng đổ của nó đọc thuộc tính này. Xem `list-sticky.ts`. */}
      <div
        ref={stickyRef}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
      <Card className="flex min-h-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          fillHeight
          columns={COMPANY_COLUMNS}
          rows={data?.items}
          getRowId={(company) => company.id}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={
            //  Nói rõ RỖNG VÌ BỘ LỌC hay rỗng vì chưa có gì: một câu chung cho
            //  cả hai thì người vừa gõ nhầm một chữ đọc ra "chưa có dữ liệu" —
            //  và ở màn danh mục, điều đó dẫn thẳng tới việc họ đi khai lại một
            //  pháp nhân đã tồn tại.
            isFiltering
              ? 'Không có công ty nào khớp bộ lọc.'
              : 'Chưa có công ty nào. Bấm «Thêm mới» để tạo.'
          }
          storageKey="hr.companies"
          //  Khổ hẹp: THẺ thay bảng. Bảng khai 10 cột, bề rộng tự nhiên ~1880px
          //  — trên máy 390px chỉ thấy *Tên pháp nhân* (còn bị cắt đuôi thành
          //  «CÔNG TY TNHH HÓ…») và *Mã*, tức mã số thuế · người đại diện ·
          //  trạng thái đều nằm sau một lượt cuộn ngang.
          mobileCard={(company: Company) => <CompanyCard company={company} />}
          //  Danh sách thẻ dài hơn một màn (13 pháp nhân ≈ 1600px) và CẢ TRANG
          //  cuộn, nên không ghim thì ô tìm trôi mất ngay nhịp vuốt đầu.
          toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
          onRowClick={(company) => navigate(appRoutes.hr.companyDetail(company.id))}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={handleSortChange}
          pagination={{
            page,
            pageSize,
            total: data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'công ty',
          }}
          toolbar={
            <>
              {/*  ⚠️ Câu gợi ý rút gọn ở khổ hẹp và phải đo theo lúc ĐANG LỌC:
                   nút *Bộ lọc* nở thêm 24px khi mọc huy hiệu số, nên phần gõ
                   chữ tụt xuống ~117px — bản «Tìm theo tên pháp nhân…» cần hơn
                   gấp rưỡi thế. Bản đầy đủ giữ từ `md`, ở đó ô rộng 256px. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder={isMobile ? 'Tìm pháp nhân…' : 'Tìm theo tên pháp nhân…'}
                className="max-md:min-w-40 md:w-64 md:max-w-sm md:flex-none"
              />

              {/*  Khổ hẹp: hai ô lọc + bộ lọc nâng cao dọn hết vào tờ trượt, hàng
                   công cụ còn một dòng. Bản cũ để ba ô bề rộng CỨNG (ô tìm
                   `min-w-56` + `w-52` + `w-44`) trong một thẻ rộng 322px nên mỗi
                   ô rớt xuống một hàng riêng, bốn hàng dài ngắn khác nhau xếp
                   thành bậc thang. Cùng khuôn `CrudListPage`. */}
              <QuickFilterSheet
                activeCount={
                  (level !== ALL ? 1 : 0) + (active !== ALL ? 1 : 0) + (filterActiveCount ?? 0)
                }
                onClearAll={() => {
                  setLevel(ALL)
                  setActive(ALL)
                  filterReset()
                }}
                onApply={filterApply}
              >
                <QuickFilterField label="Cấp pháp nhân">{levelSelect}</QuickFilterField>
                <QuickFilterField label="Trạng thái">{activeSelect}</QuickFilterField>
                <AdvancedFilterSection />
              </QuickFilterSheet>

              <div className="hidden items-center gap-3 md:flex">
                {levelSelect}
                {activeSelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>
      </div>

      <CompanyFormDialog open={isFormOpen} onOpenChange={setFormOpen} />
    </PageContainer>
  )
}
