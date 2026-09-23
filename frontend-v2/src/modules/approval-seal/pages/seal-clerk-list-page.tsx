import { CheckCircle2, Clock, Plus, ShieldCheck, Users } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { SealClerkStatCard } from '../components/seal-clerk-stat-card'
import { SEAL_CLERK_FILTER_FIELDS } from '../config/seal-clerk-filter-fields'
import { useSealClerkColumns } from '../hooks/use-seal-clerk-columns'
import { useSealClerks, useSyncSealClerks } from '../hooks/use-seal-clerks'
import { CLERK_STATUS, type SealClerkGroup } from '../types/seal-clerk'

const ALL = 'all'

/**
 * ⚠️ Danh sách văn thư TẢI HẾT MỘT LẦN rồi lọc/đếm tại trình duyệt (đại ca chốt
 * 22/09/2026). Bản cũ phân trang phía máy chủ nhưng lại đếm và lọc trên
 * `data.items` = **trang đang xem**, mà `/api/seal-clerks` chỉ nhận `search` +
 * `company_id` (không có lọc `is_head`/`status`, không có đường đếm): quá một
 * trang là thẻ "Đa pháp nhân 2" bấm vào ra bảng rỗng vì hai người đó nằm ở
 * trang sau. Danh sách này vốn vài chục dòng (mỗi công ty một hai văn thư) nên
 * tải hết là đủ; đụng tới hàng nghìn dòng thì phải thêm lọc + đếm ở backend chứ
 * đừng nâng con số này lên.
 */
const FETCH_LIMIT = 500

type FilterTab = 'all' | 'head' | 'active' | 'leave'

export function SealClerkListPage() {
  return (
    <FilterProvider config={{ fields: SEAL_CLERK_FILTER_FIELDS }}>
      <SealClerkListContent />
    </FilterProvider>
  )
}

function SealClerkListContent() {
  const navigate = useNavigate()
  const { can } = usePermission()
  // Quản lý phân công dùng chung khóa quyền `seal_type` (cấu hình Duyệt dấu).
  const canManage = can('seal_type', 'create')
  const canReadCompany = can('company', 'read')

  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL)
  const [tabFilter, setTabFilter] = useState<FilterTab>('all')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  //  Bộ lọc nâng cao chạy TẠI CHỖ (xem `seal-clerk-filter-fields.ts`), nên lấy
  //  thẳng `appliedState` chứ không đi qua `useFilterQuery`.
  const { appliedState, activeCount, reset: resetAdvanced, apply } = useFilterContext()
  //  Chuỗi ổn định để `usePageResetOnFilterChange` so theo NỘI DUNG: `appliedState`
  //  là object mới sau mỗi lần áp dụng.
  const advancedKey = useMemo(() => JSON.stringify(appliedState), [appliedState])

  //  Theo dõi giá trị tìm kiếm ĐÃ HOÃN, không theo ô nhập thô — theo ô thô thì
  //  mỗi ký tự gõ vào là một lần đặt lại trang.
  const [page, setPage] = usePageResetOnFilterChange([
    debouncedValue,
    companyId,
    tabFilter,
    advancedKey,
  ])

  const { data: companies } = useCompanies(
    { page_size: FETCH_LIMIT, is_active: true },
    { enabled: canReadCompany },
  )

  //  Chỉ `search` và `company_id` đi xuống máy chủ — đó là hai thứ nó biết lọc.
  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page: 1, page_size: FETCH_LIMIT }
    if (debouncedValue) p.search = debouncedValue
    if (companyId !== ALL) p.company_id = Number(companyId)
    return p
  }, [debouncedValue, companyId])

  const { data, isLoading, isError } = useSealClerks(params)
  const sync = useSyncSealClerks()

  const items = useMemo(() => data?.items ?? [], [data?.items])

  //  Đếm trên TOÀN BỘ kết quả (không phải trang đang xem) — xem chú thích của
  //  `FETCH_LIMIT`.
  const stats = useMemo(
    () => ({
      total: items.length,
      head: items.filter((i) => i.is_head).length,
      active: items.filter((i) => i.status === CLERK_STATUS.active).length,
      leave: items.filter((i) => i.status !== CLERK_STATUS.active).length,
    }),
    [items],
  )

  //  Hai tầng lọc CỘNG DỒN (AND), đúng nếp mọi màn danh sách khác: dải thẻ đếm
  //  là đường một chạm, bộ lọc nâng cao là bộ điều kiện ghép. Thẻ đếm luôn đọc
  //  số trên `items` (chưa lọc) nên nó không tự bóp mình về 0 sau khi lọc.
  const filteredItems = useMemo(() => {
    const byTab =
      tabFilter === 'head'
        ? items.filter((r) => r.is_head)
        : tabFilter === 'active'
          ? items.filter((r) => r.status === CLERK_STATUS.active)
          : tabFilter === 'leave'
            ? items.filter((r) => r.status !== CLERK_STATUS.active)
            : items
    return applyClientFilter(byTab, appliedState)
  }, [items, tabFilter, appliedState])

  //  Cắt trang tại chỗ để chân bảng (tổng số, chọn cỡ trang) vẫn chạy như mọi
  //  màn danh sách khác.
  const pagedItems = useMemo(
    () => filteredItems.slice((page - 1) * pageSize, page * pageSize),
    [filteredItems, page, pageSize],
  )

  //  Bấm lại đúng thẻ đang chọn = bỏ lọc. Thẻ "Tổng số" luôn về 'all' vì nó
  //  CHÍNH LÀ trạng thái không lọc.
  const toggleTab = useCallback(
    (tab: FilterTab) => setTabFilter((cur) => (cur === tab ? 'all' : tab)),
    [],
  )

  const onToggleHead = useCallback(
    (row: SealClerkGroup, isHead: boolean) =>
      sync.mutate({
        employee_id: row.employee_id,
        company_ids: row.companies.map((c) => c.id),
        is_head: isHead,
      }),
    [sync],
  )

  const columns = useSealClerkColumns({ canManage, isPending: sync.isPending, onToggleHead })

  //  Ô chọn công ty dựng HAI LẦN (hàng ngang khổ rộng · tờ trượt khổ hẹp) nên
  //  khai một chỗ. Đây là bộ lọc DUY NHẤT đi xuống máy chủ — backend lọc theo
  //  `company_id` thật, khác với bộ lọc nâng cao chạy tại chỗ.
  //
  //  ⚠️ Dùng `<Select>` của shadcn với ĐÚNG bộ class `w-full md:w-40 text-xs h-9`
  //  của màn Yêu cầu đóng dấu (`seal-request-list-page.tsx`) — hai màn cùng phân
  //  hệ, cùng một thanh công cụ, cùng lọc theo công ty thì phải trông giống hệt
  //  nhau. Bản trước dùng `SearchSelect` (ô chọn CÓ Ô TÌM bên trong): khác họ
  //  thành phần nên khác cả cỡ chữ lẫn dáng ô, đứng cạnh nhau là thấy lệch (đại
  //  ca bắt lỗi 22/09/2026). Danh mục công ty chỉ hơn chục dòng nên không cần ô
  //  tìm; ngày nào nó dài ra thì đổi CẢ HAI màn một lượt, đừng đổi riêng màn này.
  const companySelect = canReadCompany ? (
    <Select value={companyId} onValueChange={setCompanyId}>
      <SelectTrigger className="w-full md:w-40 text-xs h-9">
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
  ) : null

  return (
    <PageContainer fill>
      {/*  Nút Tải lại ĐÃ BỎ khỏi đây (22/09/2026): `DataTable` tự dựng sẵn một
          nút Tải lại trong thanh công cụ của nó, nên trang có hai nút giống hệt
          nhau cách nhau một gang tay, làm cùng một việc. */}
      <PageHeader
        title="Phân công văn thư đóng dấu"
        description="Quản lý nhân sự văn thư chịu trách nhiệm đóng dấu theo từng công ty và văn thư tổng xử lý các hồ sơ đa pháp nhân."
        actions={
          canManage && (
            <Button onClick={() => navigate(appRoutes.approvalSeal.clerksNew)}>
              <Plus className="size-4" />
              Thêm phân công
            </Button>
          )
        }
      />

      {/*  Dải thẻ đếm — đồng thời là BỘ LỌC DUY NHẤT của trang. Dải chip "Tất cả
          / Đa pháp nhân / Hoạt động" trong thanh công cụ đã bỏ: nó điều khiển
          đúng state này, nhưng thiếu nhóm "Nghỉ phép" nên hai bộ không bao giờ
          khớp nhau, lại chỉ hiện từ khổ `lg` trở lên. */}
      <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <SealClerkStatCard
          label="Tổng số văn thư"
          value={stats.total}
          unit="nhân sự"
          icon={Users}
          tone="primary"
          active={tabFilter === 'all'}
          onClick={() => setTabFilter('all')}
        />
        <SealClerkStatCard
          label="Đa pháp nhân"
          value={stats.head}
          unit="văn thư tổng"
          icon={ShieldCheck}
          tone="indigo"
          active={tabFilter === 'head'}
          onClick={() => toggleTab('head')}
        />
        <SealClerkStatCard
          label="Đang hoạt động"
          value={stats.active}
          unit="sẵn sàng"
          icon={CheckCircle2}
          tone="emerald"
          active={tabFilter === 'active'}
          onClick={() => toggleTab('active')}
        />
        <SealClerkStatCard
          label="Nghỉ phép / Tạm dừng"
          value={stats.leave}
          unit="vắng mặt"
          icon={Clock}
          tone="amber"
          active={tabFilter === 'leave'}
          onClick={() => toggleTab('leave')}
        />
      </div>

      <Card className="flex min-h-0 flex-1 flex-col p-4 shadow-xs">
        <DataTable
          fillHeight
          columns={columns}
          rows={pagedItems}
          getRowId={(r) => r.employee_id}
          onRowClick={(r) => navigate(appRoutes.approvalSeal.clerkDetail(r.anchor_id))}
          isLoading={isLoading}
          isError={isError}
          //  Rỗng vì BỘ LỌC khác hẳn rỗng vì CHƯA CÓ GÌ: gộp một câu thì người
          //  vừa gõ nhầm một chữ đọc ra "chưa phân công ai" và tin là vậy.
          emptyMessage={
            items.length === 0
              ? 'Chưa phân công văn thư đóng dấu nào.'
              : 'Không có văn thư nào khớp bộ lọc đang chọn.'
          }
          storageKey="approval-seal.clerks"
          pagination={{
            page,
            pageSize,
            total: filteredItems.length,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'văn thư',
          }}
          toolbar={
            <>
              {/*  Ô tìm dùng chung `SearchField` (đổi 22/09/2026, trước đây trang
                   này tự ghép `<Input>` + icon): khác một khối liền có NÚT XÓA
                   CHỮ, vòng sáng đúng của cả khối, và câu gợi ý tự rút gọn ở khổ
                   điện thoại. Sàn `min-w-40` để nó không bị cụm nút bóp còn vô
                   dụng đúng lúc vừa bật bộ lọc. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm theo tên, mã văn thư, công ty…"
                placeholderShort="Tìm văn thư…"
                className="max-md:min-w-40 md:w-72 md:max-w-sm md:flex-none"
              />

              {/*  Khổ hẹp: ô chọn công ty + lọc nâng cao dọn vào tờ trượt, thanh
                   công cụ còn một hàng. Cùng khuôn với Yêu cầu đóng dấu và các
                   màn Thu mua. */}
              <QuickFilterSheet
                activeCount={activeCount + (companyId !== ALL ? 1 : 0)}
                onClearAll={() => {
                  setCompanyId(ALL)
                  resetAdvanced()
                }}
                onApply={apply}
              >
                <div className="space-y-3">{companySelect}</div>
                <AdvancedFilterSection />
              </QuickFilterSheet>

              {/*  Cùng ô chọn ấy dựng lần thứ hai cho hàng ngang khổ rộng — giá
                   trị nằm trên URL nên hai bản luôn nói cùng một điều. */}
              <div className="hidden items-center gap-3 md:flex">
                {companySelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>
    </PageContainer>
  )
}
