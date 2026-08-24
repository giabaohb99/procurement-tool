import { AlertTriangle, CalendarRange, Search } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  applyClientFilter,
  ConditionalFilter,
  FilterProvider,
  useFilterContext,
} from '@/shared/conditional-filter'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { APPROVAL_INBOX_FILTER_FIELDS } from '../config/approval-inbox-filter-fields'
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

const MAC_DINH_NGAY = '30'

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
  const { appliedState } = useFilterContext()

  //  Ba ô lọc nhanh lấy URL làm nguồn sự thật: tải lại trang hay gửi link cho
  //  nhau vẫn ra đúng cái đang xem.
  const { value: tuKhoa, setValue: setTuKhoa, debouncedValue } = useUrlSearchParam()
  const [scope, setScope] = useUrlParamState('scope', INBOX_SCOPE.all)
  const [ngay, setNgay] = useUrlParamState('days', MAC_DINH_NGAY)

  const { items: viecCho, isLoading: dangTaiCho } = useMyDocumentTasks()
  const { items: daBam, isLoading: dangTaiBam } = useMyDocumentDecisions(Number(ngay))

  const tatCa = useMemo(() => buildInboxRows(viecCho, daBam), [viecCho, daBam])

  const items = useMemo(() => {
    const can = debouncedValue.trim().toLowerCase()
    const loc = tatCa.filter((row) => {
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
  }, [tatCa, debouncedValue, scope, appliedState])

  const soQuaHan = viecCho.filter((row) => row.is_overdue).length
  //  Ô chọn khoảng chỉ ảnh hưởng phần đã duyệt — khi đang xem riêng việc chờ thì
  //  nó không làm gì cả, để lại chỉ tổ khiến người dùng tưởng danh sách bị cắt.
  const hienKhoang = scope !== INBOX_SCOPE.pending && scope !== INBOX_SCOPE.overdue

  return (
    //  `contents` để hai con (băng cảnh báo + Card) nằm THẲNG trong lưới flex
    //  của trang: bọc thêm một `div` là Card mất `flex-1` và bảng không cao bằng
    //  khung nữa.
    <div className="contents">
      {soQuaHan > 0 && (
        <p className="mb-3 flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          <span>
            <b>{soQuaHan}</b> văn bản đã quá hạn duyệt.
          </span>
        </p>
      )}

      {/*  Bộ ba fit chiều cao: `PageContainer fill` → `Card flex min-h-0 flex-1
           flex-col` → `DataTable fillHeight` (xem `docs/ui/table.md` mục 2). */}
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <DataTable
          columns={approvalInboxColumns}
          rows={items}
          getRowId={(row) => row.id}
          //  Đuôi `.v2`: thứ tự cột được nhớ trong localStorage, nên đổi thứ tự
          //  mặc định ở mã nguồn KHÔNG tới được máy đã từng mở bảng này. Đổi
          //  khóa là cách duy nhất để bố cục mới thật sự hiện ra.
          storageKey="document.approval-inbox.v2"
          fillHeight
          isLoading={dangTaiCho || dangTaiBam}
          onRowClick={(row) => navigate(appRoutes.document.documentDetail(row.entityId))}
          emptyMessage={
            //  Phân biệt "không có gì" với "lọc không ra gì": một bên là tin
            //  mừng, một bên là phải xóa bớt điều kiện.
            tatCa.length > 0
              ? 'Không có văn bản nào khớp điều kiện đang lọc.'
              : 'Không có văn bản nào đang chờ bạn duyệt.'
          }
          toolbar={
            <>
              <div className="relative w-full max-w-2xs">
                <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Tìm số hiệu, tên, bước…"
                  value={tuKhoa}
                  onChange={(event) => setTuKhoa(event.target.value)}
                />
              </div>

              <InboxScopeFilter
                value={scope}
                onChange={setScope}
                soCho={viecCho.length}
                soQuaHan={soQuaHan}
                soDaDuyet={daBam.length}
              />

              {/*  Ô này KHÔNG phải bộ lọc mà là khoảng dữ liệu đi hỏi backend —
                   để lẫn vào bộ lọc nâng cao thì lọc kiểu gì cũng không moi ra
                   được văn bản đã duyệt từ bốn tháng trước. */}
              {hienKhoang && (
                <Select value={ngay} onValueChange={setNgay}>
                  <SelectTrigger className="w-40" aria-label="Khoảng thời gian đã duyệt">
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
              )}

              <ConditionalFilter />
            </>
          }
        />
      </Card>
    </div>
  )
}
