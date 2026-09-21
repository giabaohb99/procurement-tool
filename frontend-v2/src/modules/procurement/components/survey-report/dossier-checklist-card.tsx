import {
  CalendarClock,
  Check,
  ChevronDown,
  ExternalLink,
  LayoutList,
  Lock,
  Rows3,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { useApplicableDossiers } from '@/modules/dossier/hooks/use-applicable-dossiers'
import { useSetDossierProgress } from '@/modules/dossier/hooks/use-dossier-progress'
import { useDossierTypesForForm } from '@/modules/dossier/hooks/use-dossier-types'
import {
  DOC_KINDS,
  DOSSIER_PROGRESS,
  type ApplicableDossier,
} from '@/modules/dossier/types/dossier-applicability'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { ChecklistProgressBar, DossierChecklistGroups } from './dossier-checklist-groups'
import { DossierChecklistTable } from './dossier-checklist-table'
import { DossierQuickEditDialog } from './dossier-quick-edit-dialog'
import { DossierChecklistTracking } from './dossier-checklist-tracking'
import {
  CHECKLIST_STATUS_ALL,
  CHECKLIST_STATUS_OPTIONS,
  countExpiring,
  donePercent,
  expiryTone,
  filterDocs,
  groupByPhase,
  groupByLine,
  isDossierDone,
  nearestExpiryDoc,
  type ExpiryTone,
} from '../../utils/dossier-checklist-helpers'

type ChecklistViewMode = 'phase' | 'item'

const VIEW_STORAGE_KEY = 'erp.dossier-checklist.view'

/** «Không gập nhóm nào» — hằng số để lượt render nào cũng dùng lại đúng một tập. */
const EMPTY_KEYS: ReadonlySet<string> = new Set<string>()

/**
 * THẺ THỬ «Hồ sơ cần hoàn thành» — bản sao bố cục của khối *Báo cáo thực hiện*,
 * chạy bằng **kho Hồ sơ** (21/09/2026, đại ca yêu cầu dựng song song để đánh giá).
 *
 * Ánh xạ: giai đoạn = **Loại hồ sơ** · đầu việc = **tờ hồ sơ** · nút dòng hàng =
 * **điều kiện áp dụng**. Xem `dossier-checklist-helpers.ts`.
 *
 * ⚠️ **Thanh công cụ thiếu ba nút so với bản gốc, và thiếu CÓ LÝ DO.** *Thêm
 * giai đoạn* = thêm Loại hồ sơ; *Thêm hồ sơ* = thêm tờ giấy vào kho; *Thùng
 * rác* = khôi phục bản xóa. Cả ba đều là việc của phân hệ Hồ sơ, tác động tới
 * MỌI phiếu chứ không riêng phiếu này — dựng nút ở đây là mời người dùng sửa
 * danh mục toàn công ty từ trong một tờ YCBG. Thay bằng link mở kho hồ sơ.
 *
 * ⚠️ **Không có nút tick.** Phân hệ Hồ sơ chưa có chỗ lưu trạng thái theo từng
 * phiếu; «xong» ở đây nghĩa là tờ giấy đã có trong kho của công ty. Đó là khác
 * biệt lớn nhất so với bản gốc, và vì hai thẻ giờ trông y hệt nhau nên **phải
 * nói thành lời**: dòng chú thích dưới danh sách (chỗ của câu «hồ sơ khóa = …»
 * bên bản gốc) là nơi duy nhất còn nói điều đó — đừng gỡ cho gọn.
 *
 * ⚠️ Huy hiệu «BẢN THỬ» và khung chú thích hổ phách ở chân thẻ đã BỎ
 * (21/09/2026, đại ca chốt): yêu cầu là hai thẻ nhìn không phân biệt được.
 */
export function DossierChecklistCard({ surveyRequestId }: { surveyRequestId: number }) {
  const { data, isLoading } = useApplicableDossiers(DOC_KINDS.SURVEY_REQUEST, surveyRequestId)
  const { data: typePage } = useDossierTypesForForm()
  const { can } = usePermission()
  //  ⚠️ HAI quyền khác nhau, đừng gộp:
  //  · Sửa chính TỜ HỒ SƠ (tên, loại, hạn hiệu lực) — đụng tới cả công ty,
  //    nên đòi `dossier.write`.
  //  · Tick TIẾN ĐỘ cho phiếu này — là dữ liệu của tờ phiếu, nên đòi quyền
  //    ghi trên CHÍNH phiếu đó. Bắt `dossier.write` ở đây thì người thu mua
  //    phải có quyền sửa danh mục hồ sơ toàn công ty mới đánh dấu xong được
  //    một việc trên đơn của mình. Backend gác lại y hệt.
  const canEdit = can('dossier', 'write')
  const canTrack = can('survey_request', 'write')
  const setProgress = useSetDossierProgress(DOC_KINDS.SURVEY_REQUEST, surveyRequestId)

  const [cardOpen, setCardOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ChecklistViewMode>(() => {
    try {
      return localStorage.getItem(VIEW_STORAGE_KEY) === 'item' ? 'item' : 'phase'
    } catch {
      return 'phase'
    }
  })
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<number>(CHECKLIST_STATUS_ALL)
  /** Giai đoạn đang GẬP ở dạng Xem tổng — mặc định mọi giai đoạn đều mở. */
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  /** Dòng bảng đang SỔ ở dạng Theo dòng hàng — mặc định mọi dòng đều gập. */
  const [openRows, setOpenRows] = useState<Set<string>>(new Set())
  /** Tờ hồ sơ đang mở hộp thoại sửa nhanh; `null` = đóng. */
  const [editing, setEditing] = useState<ApplicableDossier | null>(null)

  const docs = useMemo(() => data?.items ?? [], [data])
  const types = useMemo(() => typePage?.items ?? [], [typePage])
  const visible = useMemo(
    () => filterDocs(docs, query, statusFilter),
    [docs, query, statusFilter],
  )
  const groups = useMemo(
    () =>
      viewMode === 'phase'
        ? groupByPhase(visible, types)
        : groupByLine(visible, data?.lines ?? []),
    [viewMode, visible, types, data],
  )
  //  Cột Tiến trình LUÔN đi theo giai đoạn và LUÔN đếm trên toàn bộ hồ sơ —
  //  giống hệt bản gốc, nơi khung tracking cố ý bỏ qua ô tìm và ô lọc trạng
  //  thái. Trước đây nó dùng chung `groups`, nên bấm sang «Theo dòng hàng» là
  //  cột Tiến trình liệt kê ba dòng hàng thay vì năm giai đoạn, còn gõ vào ô
  //  tìm thì tiến độ tụt xuống theo từ khóa đang gõ.
  const phaseGroups = useMemo(() => groupByPhase(docs, types), [docs, types])

  //  Thiếu `dossier.read` thì hook tự tắt → `data` mãi `undefined` → không vẽ.
  if (isLoading || docs.length === 0) return null

  const changeViewMode = (mode: ChecklistViewMode) => {
    setViewMode(mode)
    //  Đổi trục xem thì trả về mặc định của trục MỚI: khóa nhóm của hai trục
    //  khác hẳn nhau, giữ tập cũ là gập/sổ nhầm một nhóm không liên quan.
    setCollapsed(new Set())
    setOpenRows(new Set())
    try {
      localStorage.setItem(VIEW_STORAGE_KEY, mode)
    } catch {
      //  Không ghi nhớ được thì thôi, đổi dạng xem vẫn phải ăn.
    }
  }

  //  Đang tìm / lọc thì SỔ hết bất kể trạng thái gập — không thì kết quả tìm
  //  được nằm sau một dòng đang gập, người dùng tưởng là không có.
  const hasFilter = query.trim() !== '' || statusFilter !== CHECKLIST_STATUS_ALL

  //  Nút «Mở tất cả / Thu gọn» gạt ĐÚNG TRỤC đang xem: dạng tổng gạt giai đoạn
  //  (nhớ cái GẬP), dạng dòng hàng gạt dòng bảng (nhớ cái MỞ). Một nút, hai
  //  nghĩa — vì mỗi lúc chỉ một trục hiện ra. Y như bản gốc.
  const allOpen =
    viewMode === 'phase'
      ? collapsed.size === 0
      : groups.length > 0 && groups.every((group) => openRows.has(group.key))
  const toggleAll = () => {
    if (viewMode === 'phase') {
      setCollapsed(allOpen ? new Set(groups.map((g) => g.key)) : new Set())
      return
    }
    setOpenRows(allOpen ? new Set() : new Set(groups.map((g) => g.key)))
  }
  const toggleGroup = (key: string) =>
    setCollapsed((current) => {
      const next = new Set(current)
      if (!next.delete(key)) next.add(key)
      return next
    })
  const toggleRow = (key: string) =>
    setOpenRows((current) => {
      const next = new Set(current)
      if (!next.delete(key)) next.add(key)
      return next
    })

  /**
   * Nhãn nút dòng hàng của một tờ hồ sơ: rỗng = **CHUNG** (áp cả phiếu).
   *
   * ⚠️ Hồ sơ khớp NHIỀU dòng thì ghi «n dòng hàng» chứ không nối tên: nhãn có
   * trần 144px, nối hai cái tên dài là cả hai đều cụt và không đọc ra được cái
   * nào — rê chuột đọc đủ ở `title`.
   */
  const itemTagOf = (doc: ApplicableDossier): string => {
    if (doc.matched_lines.length === 0) return ''
    if (doc.matched_lines.length > 1) return `${doc.matched_lines.length} dòng hàng`
    const line = data?.lines.find((l) => l.no === doc.matched_lines[0])
    return line?.label ?? `Dòng ${doc.matched_lines[0]}`
  }

  //  Bấm ô tick: xong thì mở lại về «Đang làm», chưa xong thì đóng thành
  //  «Hoàn thành» — cùng luật với `handleToggleDoc` của khối Báo cáo thực hiện.
  const handleToggleDone = (doc: ApplicableDossier) =>
    setProgress.mutate({
      dossierId: doc.id,
      payload: {
        status: isDossierDone(doc) ? DOSSIER_PROGRESS.DOING : DOSSIER_PROGRESS.DONE,
      },
    })

  const doneCount = docs.filter(isDossierDone).length
  const nearest = nearestExpiryDoc(docs)
  const expiry = nearest?.expiry_date ?? null
  const expiring = countExpiring(docs)

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="flex min-h-9 flex-row flex-wrap items-center justify-between gap-3 border-b px-4 pb-3!">
        <button
          type="button"
          aria-expanded={cardOpen}
          className="flex min-w-0 flex-1 cursor-pointer items-center gap-2 text-left"
          onClick={() => setCardOpen((current) => !current)}
        >
          <ChevronDown
            className={cn(
              'size-4 shrink-0 text-muted-foreground transition-transform',
              !cardOpen && '-rotate-90',
            )}
          />
          <CardTitle className="text-base text-navy dark:text-foreground">
            Hồ sơ cần hoàn thành
          </CardTitle>
          <span className="text-xs whitespace-nowrap text-muted-foreground">
            {doneCount}/{docs.length} hồ sơ · {donePercent(docs)}%
          </span>
        </button>

        {cardOpen && (
          <div className="flex flex-wrap items-center justify-end gap-2">
            <div className="flex items-center rounded-md border p-0.5">
              <ViewModeButton
                active={viewMode === 'phase'}
                label="Xem tổng"
                title="Xem tổng: hồ sơ xếp theo giai đoạn (= Loại hồ sơ)"
                icon={<LayoutList className="size-3.5" />}
                onClick={() => changeViewMode('phase')}
              />
              <ViewModeButton
                active={viewMode === 'item'}
                label="Theo dòng hàng"
                title="Xem theo dòng hàng: gom theo điều kiện áp dụng của từng tờ hồ sơ"
                icon={<Rows3 className="size-3.5" />}
                onClick={() => changeViewMode('item')}
              />
            </div>
            <SearchField
              value={query}
              onChange={setQuery}
              placeholder="Tìm hồ sơ, mã, lý do..."
              placeholderShort="Tìm hồ sơ..."
              className="h-8 w-48 flex-none"
              aria-label="Tìm hồ sơ trong danh sách"
            />
            <Select
              value={String(statusFilter)}
              onValueChange={(value) => setStatusFilter(Number(value))}
            >
              <SelectTrigger size="sm" aria-label="Lọc theo trạng thái hồ sơ">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={String(CHECKLIST_STATUS_ALL)}>Mọi trạng thái</SelectItem>
                {CHECKLIST_STATUS_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={toggleAll}>
              {allOpen ? 'Thu gọn' : 'Mở tất cả'}
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to={appRoutes.dossier.list} target="_blank" rel="noreferrer">
                <ExternalLink />
                Kho hồ sơ
              </Link>
            </Button>
          </div>
        )}
      </CardHeader>

      {cardOpen && (
        <CardContent className="space-y-4 px-4">
          {/* Bốn ô tổng — cùng khuôn, cùng thứ tự với khối Báo cáo thực hiện. */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryTile label="Tổng hồ sơ" value={String(docs.length)} />
            <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
              <p className="text-xs text-muted-foreground">Đã hoàn thành</p>
              <ChecklistProgressBar
                docs={docs}
                barClassName="mt-2 h-6 w-full"
                labelClassName="text-xs text-foreground"
              />
            </div>
            <SummaryTile
              label="Hết hiệu lực gần nhất"
              icon={<CalendarClock className="size-3" />}
              value={expiry ? formatDate(expiry) : '—'}
              note={expiring > 0 ? `${expiring} tờ cần để mắt` : undefined}
              //  Tô theo mức khẩn của chính tờ gần nhất, không tô theo số tờ:
              //  đỏ dành cho tờ ĐÃ hết hạn, vàng cho tờ sắp tới ngưỡng.
              tone={expiryTone(nearest?.expiry_state ?? 0)}
            />
            {/*  Đếm trên dữ liệu ĐẦY ĐỦ, không theo bộ lọc — cùng lẽ với ba ô
                 bên trái. Dạng Theo dòng hàng đếm dòng hàng THẬT của phiếu,
                 không cộng dòng «Chung (cả phiếu)» vào: nó không phải mặt hàng. */}
            <SummaryTile
              label={viewMode === 'phase' ? 'Giai đoạn' : 'Dòng hàng'}
              value={String(
                viewMode === 'phase' ? phaseGroups.length : (data?.lines.length ?? 0),
              )}
            />
          </div>

          {/* Cột trái: danh sách hồ sơ · cột phải: khung tiến trình */}
          <div className="gap-5 lg:grid lg:grid-cols-[minmax(0,1fr)_215px]">
            <div className="space-y-3">
              {viewMode === 'phase' ? (
                <DossierChecklistGroups
                  groups={groups}
                  collapsed={hasFilter ? EMPTY_KEYS : collapsed}
                  onToggle={toggleGroup}
                  //  Nhãn nút dòng hàng CHỈ ở dạng Xem tổng — dạng Theo dòng
                  //  hàng thì dòng bảng đã nói rồi, lặp lại là chiếm chỗ cột mô tả.
                  itemTagOf={itemTagOf}
                  //  Không có `dossier.write` thì KHÔNG dựng nút sửa. Dựng rồi
                  //  khóa là mời người ta bấm vào một thứ chắc chắn trả 403.
                  //  Mở được hộp khi có MỘT trong hai quyền — hộp gộp cả tiến
                  //  độ của phiếu lẫn tờ giấy dùng chung, thiếu một bên vẫn còn
                  //  bên kia để sửa.
                  onEdit={canEdit || canTrack ? setEditing : undefined}
                  onToggleDone={canTrack ? handleToggleDone : undefined}
                  busy={setProgress.isPending}
                />
              ) : (
                <DossierChecklistTable
                  rows={groups}
                  //  Dòng TỔNG đếm trên TOÀN BỘ hồ sơ, không theo bộ lọc — bản
                  //  gốc cũng vậy: con số của cả phiếu không đổi theo từ khóa.
                  allDocs={docs}
                  types={types}
                  openRows={openRows}
                  forceOpen={hasFilter}
                  onToggleRow={toggleRow}
                  //  Mở được hộp khi có MỘT trong hai quyền — hộp gộp cả tiến
                  //  độ của phiếu lẫn tờ giấy dùng chung, thiếu một bên vẫn còn
                  //  bên kia để sửa.
                  onEdit={canEdit || canTrack ? setEditing : undefined}
                  onToggleDone={canTrack ? handleToggleDone : undefined}
                  busy={setProgress.isPending}
                />
              )}

              {/*  Chỗ của dòng chú thích «hồ sơ khóa = …» bên bản gốc. Câu này
                   phải còn: hai cột «đã xong» và «đã có giấy» nghe giống nhau
                   nhưng đếm hai thứ khác hẳn, và người đọc không có cách nào
                   đoán ra điều đó từ giao diện. */}
              <div className="space-y-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Lock className="size-3" />
                  hồ sơ khóa = chờ hồ sơ tiên quyết hoàn thành trước
                </span>
                <span className="flex items-center gap-1">
                  <Check className="size-3" />
                  tiến độ tính riêng cho phiếu này; viên trạng thái bên phải là tình trạng
                  tờ giấy trong kho, dùng chung cả công ty
                </span>
              </div>
            </div>

            <DossierChecklistTracking groups={phaseGroups} className="hidden lg:block" />
          </div>
        </CardContent>
      )}

      <DossierQuickEditDialog
        doc={editing}
        onClose={() => setEditing(null)}
        docKind={DOC_KINDS.SURVEY_REQUEST}
        docId={surveyRequestId}
        //  Ứng viên tiên quyết = mọi hồ sơ áp dụng cho phiếu, KHÔNG lọc theo ô
        //  tìm: đang lọc mà danh sách ứng viên co lại thì bỏ tick nhầm một tờ
        //  chỉ vì nó không khớp từ khóa đang gõ.
        candidates={docs}
        canEditDossier={canEdit}
        canTrack={canTrack}
      />
    </Card>
  )
}

function ViewModeButton({
  active,
  label,
  title,
  icon,
  onClick,
}: {
  active: boolean
  label: string
  title: string
  icon: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      title={title}
      className={cn(
        'flex h-7 cursor-pointer items-center gap-1.5 rounded-sm px-2 text-xs font-medium whitespace-nowrap transition-colors',
        active ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground',
      )}
      onClick={onClick}
    >
      {icon}
      {label}
    </button>
  )
}

/** Một ô tổng — cùng khuôn với bốn ô của `ReportSummary` bên bản gốc. */
function SummaryTile({
  label,
  value,
  icon,
  note,
  tone,
}: {
  label: string
  value: string
  icon?: React.ReactNode
  note?: string
  tone?: ExpiryTone
}) {
  return (
    <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
      <p className="flex items-center gap-1 text-xs text-muted-foreground">
        {icon}
        {label}
      </p>
      <p
        className={cn(
          'text-lg font-semibold tabular-nums',
          tone === 'overdue' && 'text-destructive',
          tone === 'soon' && 'text-warning',
        )}
      >
        {value}
        {note && <span className="ml-1.5 text-xs font-medium">· {note}</span>}
      </p>
    </div>
  )
}
