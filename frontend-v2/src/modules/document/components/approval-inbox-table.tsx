import { AlertTriangle, CalendarRange } from 'lucide-react'
import { useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { LIST_TOOLBAR_STICKY_TOP } from '@/modules/hr/utils/list-sticky'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { Card } from '@/shared/ui/card'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { APPROVAL_INBOX_FILTER_FIELDS } from '../config/approval-inbox-filter-fields'
import { ApprovalInboxCard } from './approval-inbox-card'
import {
  useMyDocumentDecisions,
  useMyDocumentTasks,
} from '../hooks/use-my-document-approvals'
import { approvalInboxColumns } from './approval-inbox-columns'
import { buildInboxRows, INBOX_SCOPE } from './approval-inbox-row'
import { InboxScopeFilter } from './inbox-scope-filter'

/** Khoảng nhìn lại của phần ĐÃ DUYỆT. 30 ngày phủ một chu kỳ làm việc. */
const KHOANG = [
  { value: '7', label: '7 ngày qua' },
  { value: '30', label: '30 ngày qua' },
  { value: '90', label: '90 ngày qua' },
]

const DEFAULT_DATE = '30'

/**
 * `preserveParams`: thiếu tên nào ở đây thì bấm "Áp dụng" bộ lọc nâng cao sẽ
 * xóa mất tham số đó khỏi URL. Không cần kể `q` — `searchParamName` giữ sẵn.
 */
const FILTER_CONFIG = {
  fields: APPROVAL_INBOX_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['scope', 'days'],
}

export function ApprovalInboxTable() {
  return (
    <FilterProvider config={FILTER_CONFIG}>
      <ApprovalInboxContent />
    </FilterProvider>
  )
}

/**
 * HỘP DUYỆT VĂN BẢN — việc chờ tôi bấm và việc tôi vừa bấm, trong MỘT bảng.
 *
 * Trước đây là hai tab. Gộp lại vì hai tập này là cùng một câu hỏi ("văn bản nào
 * qua tay tôi") ở hai thời điểm, mà tab bắt bấm thêm một cú mới biết mình vừa ký
 * cái gì — trong khi hộp chờ phần lớn thời gian chỉ có vài dòng, thừa chỗ.
 *
 * Trật tự là **việc chưa làm nằm trên, việc đã làm nằm dưới**, phân biệt bằng
 * huy hiệu ở cột cuối (xem `approval-inbox-row.ts`). Không sắp xếp theo cột:
 * đảo thứ tự là mất chính cái trật tự đang mang nghĩa.
 *
 * **Tìm và lọc chạy NGAY TẠI TRÌNH DUYỆT**, khác các màn danh sách gọi API phân
 * trang: bảng này gộp hai nguồn rồi mới dựng dòng nên không có endpoint nào để
 * cắm điều kiện vào — mà cả hai nguồn đều trả hết một lượt, không phân trang.
 *
 * Không có nút duyệt trên dòng: bấm dòng là mở văn bản ra đọc rồi duyệt tại đó.
 * Bày nút ngay trên danh sách là mời người ta ký một thứ chỉ nhìn thấy mỗi tiêu đề.
 */
function ApprovalInboxContent() {
  const navigate = useNavigate()
  //  Cần cả `apply`/`reset`/`activeCount` chứ không chỉ `appliedState`: ở khổ
  //  hẹp bộ lọc nâng cao mở bằng tờ trượt, và tờ trượt tự dựng nút áp dụng.
  const filter = useFilterContext()
  const { appliedState } = filter

  //  Dải ghim đầu trang chỉ đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Khối gắn `ref` luôn được dựng (không chờ dữ liệu) nên
  //  không cần `nodeKey` để bắt hook dò lại khung cuộn.
  const scrollProbeRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(scrollProbeRef)

  //  Ba ô lọc nhanh lấy URL làm nguồn sự thật: tải lại trang hay gửi link cho
  //  nhau vẫn ra đúng cái đang xem.
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [scope, setScope] = useUrlParamState('scope', INBOX_SCOPE.all)
  const [ngay, setNgay] = useUrlParamState('days', DEFAULT_DATE)

  const { items: pendingTasks, isLoading: loadingPending } = useMyDocumentTasks()
  const { items: clicked, isLoading: loadingClick } = useMyDocumentDecisions(Number(ngay))

  const all = useMemo(() => buildInboxRows(pendingTasks, clicked), [pendingTasks, clicked])

  const items = useMemo(() => {
    const can = debouncedValue.trim().toLowerCase()
    const loc = all.filter((row) => {
      if (scope === INBOX_SCOPE.pending && row.kind !== 'pending') return false
      if (scope === INBOX_SCOPE.overdue && !row.isOverdue) return false
      if (scope === INBOX_SCOPE.done && row.kind !== 'done') return false
      if (!can) return true
      return [
        row.code,
        row.title,
        row.nodeName,
        row.startedByName,
        row.actionLabel,
        row.comment,
      ].some((o) => o.toLowerCase().includes(can))
    })
    return applyClientFilter(loc, appliedState)
  }, [all, debouncedValue, scope, appliedState])

  const overdueCount = pendingTasks.filter((row) => row.is_overdue).length
  //  Ô chọn khoảng chỉ ảnh hưởng phần đã duyệt — khi đang xem riêng việc chờ thì
  //  nó không làm gì cả, để lại chỉ tổ khiến người dùng tưởng danh sách bị cắt.
  const showRange = scope !== INBOX_SCOPE.pending && scope !== INBOX_SCOPE.overdue

  //  ⚠️ Dựng MỘT LẦN rồi dùng cho cả hai khổ (hàng ngang ở màn rộng · tờ trượt ở
  //  màn hẹp). Chép hai bản là hai khổ màn lọc ra hai kết quả khác nhau mà không
  //  chỗ nào báo — bài học `buildFields` của duoc-CR-364.
  //  `w-full md:w-40`: trong tờ trượt ô trải hết bề ngang, trên thanh công cụ nó
  //  về lại bề rộng cũ.
  const rangeSelect = (
    <Select value={ngay} onValueChange={setNgay}>
      <SelectTrigger className="w-full md:w-40" aria-label="Khoảng thời gian đã duyệt">
        <CalendarRange className="size-4 text-muted-foreground" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {KHOANG.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    //  ⚠️ Khối này phải GIỮ NGUYÊN chuỗi `flex min-h-0 flex-1 flex-col` — nó là
    //  mắt xích giữa `PageContainer fill` và `Card`, thiếu một vế là thẻ mất
    //  `flex-1` và bảng không còn cao bằng khung.
    //
    //  `group` + `data-scrolled` là đường dẫn tín hiệu «đã cuộn» xuống tới dải
    //  ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng này không
    //  với tới được bằng prop). Bóng đổ của dải đó đọc thuộc tính này — xem
    //  `list-sticky.ts`.
    <div
      ref={scrollProbeRef}
      data-scrolled={scrolled ? '' : undefined}
      className="group flex min-h-0 flex-1 flex-col"
    >
      {overdueCount > 0 && (
        <p className="mb-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <span>
            <b>{overdueCount}</b> văn bản đã quá hạn duyệt.
          </span>
        </p>
      )}

      {/*  Bộ ba fit chiều cao: `PageContainer fill` → `Card flex min-h-0 flex-1
           flex-col` → `DataTable fillHeight` (xem `docs/ui/table.md` mục 2). */}
      {/*  `min-w-0`: thẻ là ô của một hộp flex, mà ô flex mặc định `min-width:auto`
           nên nó không co xuống dưới bề rộng tự nhiên của bảng bên trong
           (~1450px). Thiếu nó thì CẢ TRANG trượt ngang ở khổ hẹp. */}
      <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
        <DataTable
          columns={approvalInboxColumns}
          rows={items}
          getRowId={(row) => row.id}
          //  Ô tìm chiếm trọn hàng đầu ở khổ hẹp, nên hàng còn lại dư chỗ và
          //  `ml-auto` mặc định xé nó thành hai mẩu cách nhau. Dồn liền một cụm.
          toolbarActionsClassName="max-md:ml-0"
          //  ⚠️ Ghim thanh công cụ ở khổ hẹp — ở đó cả trang cuộn (trang gỡ
          //  `fill`), nên không ghim thì ô tìm và dãy lọc phạm vi trôi mất ngay
          //  nhịp vuốt đầu tiên; muốn đổi bộ lọc phải vuốt ngược lên đầu.
          //  Mốc `top-0`: màn này không có dải tab nào phía trên thanh công cụ.
          toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
          //  Khổ hẹp: THẺ thay bảng — xem `ApprovalInboxCard`.
          mobileCard={(row) => <ApprovalInboxCard row={row} />}
          //  Đuôi `.v2`: thứ tự cột được nhớ trong localStorage, nên đổi thứ tự
          //  mặc định ở mã nguồn KHÔNG tới được máy đã từng mở bảng này. Đổi
          //  khóa là cách duy nhất để bố cục mới thật sự hiện ra.
          storageKey="document.approval-inbox.v2"
          fillHeight
          isLoading={loadingPending || loadingClick}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.entityId))}
          emptyMessage={
            //  Phân biệt "không có gì" với "lọc không ra gì": một bên là tin
            //  mừng, một bên là phải xóa bớt điều kiện.
            all.length > 0
              ? 'Không có văn bản nào khớp điều kiện đang lọc.'
              : 'Không có văn bản nào đang chờ bạn duyệt.'
          }
          toolbar={
            <>
              {/*  `max-md:basis-full` — ô tìm chiếm TRỌN hàng đầu ở khổ hẹp. Câu
                   gợi ý «Tìm số hiệu, tên, bước…» cần ~171px; chen nó cùng hàng
                   với dãy lọc phạm vi (310px) thì không còn gì cho nó. Từ `md`
                   trở lên `basis-full` tắt, ô về lại bề rộng cũ cạnh các nút. */}
              <SearchField
                value={keyword}
                onChange={setKeyword}
                placeholder="Tìm số hiệu, tên, bước…"
                className="max-md:basis-full md:min-w-56 md:max-w-2xs"
              />

              <InboxScopeFilter
                value={scope}
                onChange={setScope}
                pendingCount={pendingTasks.length}
                overdueCount={overdueCount}
                approvedCount={clicked.length}
              />

              {/*  ⚠️ `activeCount` cộng CẢ HAI tầng — khoảng thời gian và điều
                   kiện nâng cao — vì dưới 768px cả hai nay nằm sau đúng nút này.
                   Đếm thiếu một tầng thì người dùng thấy nút trơn mà danh sách
                   vẫn đang bị cắt bớt, rồi đi tìm lỗi ở dữ liệu.

                   «Đang lọc» = KHÁC mặc định chứ không phải «có giá trị»: mặc
                   định của ô khoảng là `30` chứ không rỗng (bài học duoc-CR-364).

                   Nút tự ẩn từ `md` trở lên (`QuickFilterSheet` khai `md:hidden`). */}
              <QuickFilterSheet
                activeCount={
                  (showRange && ngay !== DEFAULT_DATE ? 1 : 0) + filter.activeCount
                }
                onClearAll={() => {
                  setNgay(DEFAULT_DATE)
                  filter.reset()
                }}
                onApply={filter.apply}
              >
                {showRange && (
                  <QuickFilterField label="Khoảng thời gian đã duyệt">
                    {rangeSelect}
                  </QuickFilterField>
                )}
                <AdvancedFilterSection />
              </QuickFilterSheet>

              {/*  ⚠️ `md:contents` chứ KHÔNG `md:flex`: bọc cụm lọc trong một thẻ
                   flex riêng thì cả cụm là MỘT ô của thanh công cụ — không đủ chỗ
                   là nó rớt nguyên khối xuống dòng dưới, chừa một khoảng trống
                   dài bên phải ô tìm. `display: contents` cho từng ô thành ô trực
                   tiếp của thanh công cụ nên chúng xếp kín từng dòng.

                   `ConditionalFilter` nằm TRONG đây vì popover của nó neo vào
                   nút, mà ở 390px tấm `95vw` bung ra che gần hết màn và vẫn
                   không đủ ngang cho một hàng điều kiện — khổ hẹp đi bằng
                   `AdvancedFilterSection` trong tờ trượt ở trên.

                   Ô khoảng thời gian KHÔNG phải bộ lọc mà là khoảng dữ liệu đi
                   hỏi backend — để lẫn vào bộ lọc nâng cao thì lọc kiểu gì cũng
                   không moi ra được văn bản đã duyệt từ bốn tháng trước. */}
              <div className="hidden md:contents">
                {showRange && rangeSelect}
                <ConditionalFilter />
              </div>
            </>
          }
        />
      </Card>
    </div>
  )
}
