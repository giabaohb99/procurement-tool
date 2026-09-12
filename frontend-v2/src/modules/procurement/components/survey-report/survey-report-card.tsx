import {
  CalendarCheck,
  CalendarClock,
  Check,
  ChevronDown,
  ChevronRight,
  LayoutList,
  ListPlus,
  Lock,
  Paperclip,
  Pencil,
  Plus,
  Rows3,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { Fragment, useState } from 'react'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { cn } from '@/shared/utils/cn'
import { formatDate, parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'
import { nameInitials } from '@/shared/utils/name-initials'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { useSurveyReportActions, useSurveyRequestReport } from '../../hooks/use-survey-request-report'
import {
  REPORT_DOC_DOING,
  REPORT_DOC_DONE,
  REPORT_DOC_STATUS_LABELS,
  type SurveyReportDoc,
  type SurveyReportItem,
  type SurveyReportPhase,
  type SurveyRequestReport,
} from '../../types/survey-request-report'
import {
  REPORT_FILTER_ALL,
  REPORT_STATUS_FILTER_ALL,
  isReportDocDone,
  isReportDocLocked,
  latestPlannedDate,
  matchReportDoc,
  nearestExpiry,
  pendingDepends,
  reportDocLateDays,
  reportDocsById,
  reportPercent,
  reportPlanLateDays,
} from '../../utils/survey-report-helpers'
import { SurveyReportDocDialog } from './survey-report-doc-dialog'
import { SurveyReportItemDialog } from './survey-report-item-dialog'
import { SurveyReportPhaseDialog } from './survey-report-phase-dialog'
import { SurveyReportTracking } from './survey-report-tracking'

//  Màu pill theo mã trạng thái hồ sơ (0..3). Dải màu ở MÉP TRÁI mỗi dòng đã bỏ
//  (12/09/2026): trạng thái đã nói bằng ô tick và bằng chữ trên pill, thêm một
//  cột màu nữa chỉ là nhiễu — mắt đọc dải màu trước cả tiêu đề hồ sơ.
const STATUS_PILL: Record<number, string> = {
  0: 'bg-muted text-muted-foreground',
  1: 'bg-warning/15 text-warning',
  2: 'bg-primary/10 text-primary',
  3: 'bg-success/15 text-success',
}

/** Id của dòng «Chung» trong bảng — trùng `item_id = 0` của hồ sơ chung. */
const COMMON_ROW_ID = 0
/** Số cột của bảng dòng hàng — dùng cho `colSpan` của dải mở rộng và dòng tổng. */
const ITEM_TABLE_COLUMNS = 6

/**
 * Hai cách đọc cùng một khối, người dùng chọn — không cách nào thay được cách kia:
 * - `phase` (TỔNG): toàn bộ hồ sơ xếp theo giai đoạn, mỗi hồ sơ gắn tag dòng hàng.
 *   Đọc theo TRÌNH TỰ thời gian của thương vụ — "giờ đang vướng khâu nào".
 * - `item` (THEO DÒNG HÀNG): bảng mỗi dòng hàng một dòng, bấm sổ hồ sơ của nó.
 *   Đọc theo MẶT HÀNG — "riêng KNO₃ còn thiếu giấy gì".
 */
type ReportViewMode = 'phase' | 'item'

const VIEW_STORAGE_KEY = 'erp.survey-report.view'

/** Dạng xem lần trước của người dùng. Hỏng/không có thì về «tổng». */
function readViewMode(): ReportViewMode {
  try {
    return localStorage.getItem(VIEW_STORAGE_KEY) === 'item' ? 'item' : 'phase'
  } catch {
    //  Trình duyệt chặn localStorage (chế độ riêng tư) — mất trí nhớ chứ không vỡ màn.
    return 'phase'
  }
}

/** Một DÒNG của bảng: nút dòng hàng, hoặc dòng «Chung» gom hồ sơ `item_id = 0`. */
interface ReportItemRow {
  id: number
  name: string
  /** `null` với dòng «Chung» — nó không phải một bản ghi nút, không sửa/xóa được. */
  item: SurveyReportItem | null
  /** Hồ sơ của RIÊNG dòng này, chưa qua ô tìm / lọc trạng thái. */
  docs: SurveyReportDoc[]
}

interface SurveyReportCardProps {
  surveyRequestId: number
  /** NS Thu mua (cờ `process`) mới sửa được — backend gác lại lần nữa. */
  canEdit: boolean
}

/**
 * Khối BÁO CÁO THỰC HIỆN trên chi tiết YCBG.
 *
 * Hai lớp GẤP, cố ý:
 * - Cả khối gấp sẵn, bấm tiêu đề mới sổ ra — nó nằm cuối trang chi tiết, dưới
 *   khối kết quả khảo sát, và phần lớn lượt mở phiếu không đụng tới nó.
 * - Trong khối, mỗi NÚT DÒNG HÀNG là một dòng bảng bấm để sổ hồ sơ của nó
 *   (cùng khuôn với «Chi phí theo dòng hàng» của đơn mua hàng nhập khẩu).
 *
 * Người không có quyền sửa vẫn xem được; khối rỗng thì ẩn hẳn với họ.
 */
export function SurveyReportCard({ surveyRequestId, canEdit }: SurveyReportCardProps) {
  const { data: report, isLoading, isError } = useSurveyRequestReport(surveyRequestId)
  const actions = useSurveyReportActions(surveyRequestId)
  const { user } = useAuth()
  //  Hồ sơ mới điền sẵn người thực hiện = người đang đăng nhập (đổi được).
  const defaultAssigneeId = user?.employee_id ?? 0

  /** Cả khối đang sổ ra chưa — mặc định GẤP. */
  const [cardOpen, setCardOpen] = useState(false)
  const [viewMode, setViewMode] = useState<ReportViewMode>(readViewMode)
  const [statusFilter, setStatusFilter] = useState(REPORT_STATUS_FILTER_ALL)
  const [query, setQuery] = useState('')
  /** Các dòng hàng đang SỔ (hiện hồ sơ con). Nút trên header gạt cả loạt. */
  const [openRows, setOpenRows] = useState<Set<number>>(new Set())
  /** Giai đoạn đang THU GỌN ở dạng xem tổng — mặc định mọi giai đoạn đều mở. */
  const [collapsedPhases, setCollapsedPhases] = useState<Set<number>>(new Set())
  //  `phaseId` bỏ trống = mở từ nút chung, hộp tự điền giai đoạn đầu tiên. Bấm
  //  «+ hồ sơ» ngay trong một giai đoạn thì điền sẵn ĐÚNG giai đoạn đó.
  const [docDialog, setDocDialog] = useState<{
    doc: SurveyReportDoc | null
    itemId: number
    phaseId?: number
  } | null>(null)
  const [itemDialog, setItemDialog] = useState<{ item: SurveyReportItem | null } | null>(null)
  const [phaseDialog, setPhaseDialog] = useState<{ phase: SurveyReportPhase | null } | null>(null)

  const busy =
    actions.init.isPending ||
    actions.applyTemplate.isPending ||
    actions.saveItem.isPending ||
    actions.deleteItem.isPending ||
    actions.savePhase.isPending ||
    actions.deletePhase.isPending ||
    actions.saveDoc.isPending ||
    actions.setDocStatus.isPending ||
    actions.deleteDoc.isPending ||
    actions.deleteReport.isPending

  //  Xóa CẢ khối — thao tác nặng nên hỏi xác nhận; hoàn tác được ở Lịch sử.
  const handleDeleteReport = async () => {
    const total = report?.docs.length ?? 0
    if (
      !(await confirm({
        title: 'Xóa báo cáo thực hiện?',
        message: `Xóa toàn bộ báo cáo thực hiện${total ? ` (${total} hồ sơ)` : ''}? Bạn có thể hoàn tác ngay sau đó ở khối Lịch sử thao tác.`,
        confirmLabel: 'Xóa báo cáo',
      }))
    )
      return
    await actions.deleteReport.mutateAsync()
  }

  //  Bấm ô tick trên một hồ sơ: xong thì mở lại về «Đang làm», chưa xong thì
  //  đóng thành «Hoàn thành». Dùng chung cho cả hai dạng xem.
  const handleToggleDoc = (doc: SurveyReportDoc) =>
    actions.setDocStatus.mutate({
      docId: doc.id,
      status: isReportDocDone(doc) ? REPORT_DOC_DOING : REPORT_DOC_DONE,
    })

  //  Xóa MỘT hồ sơ ngay trên dòng, không phải mở hộp sửa: mẫu chung đổ ra
  //  hàng chục dòng, dọn bớt mà mỗi dòng ba cú bấm thì không ai dọn. Vẫn hỏi
  //  xác nhận vì xóa là mất, và nói rõ hồ sơ khác đang chờ nó sẽ được mở khóa.
  const handleDeleteDoc = async (doc: SurveyReportDoc) => {
    if (
      !(await confirm({
        message: `Xóa hồ sơ "${doc.title}"? Hồ sơ khác đang chờ nó sẽ được mở khóa.`,
        confirmLabel: 'Xóa hồ sơ',
      }))
    )
      return
    await actions.deleteDoc.mutateAsync({ docId: doc.id })
  }

  //  «Tạo mẫu» vào một nút dòng hàng (hoặc chỉ một giai đoạn của nút Chung).
  //  Backend CỘNG THÊM và bỏ qua hồ sơ trùng, nên không cần hỏi xác nhận; thứ
  //  cần nói là ĐÃ THÊM MẤY — so số hồ sơ trước/sau, bằng nhau nghĩa là mẫu đã
  //  có đủ ở đó (bấm hai lần không ra thêm gì, phải báo chứ đừng im).
  const handleApplyTemplate = async (itemId: number, phaseId?: number) => {
    const before = report?.docs.length ?? 0
    const next = await actions.applyTemplate.mutateAsync({ itemId, phaseId })
    const added = next.docs.length - before
    if (added > 0) toast.success(`Đã tạo ${added} hồ sơ theo mẫu chung`)
    else toast.info('Mẫu chung đã có đủ ở đây — không thêm hồ sơ nào')
  }

  if (isLoading) {
    if (!canEdit) return null
    return (
      <Card className="gap-4 py-4">
        <CardContent className="px-4">
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    )
  }
  //  Gọi API HỎNG thì phải NÓI ra, đừng biến mất im lặng: người vừa bấm «Thêm
  //  Báo cáo thực hiện» nhìn vào một khoảng trống và tưởng nút không ăn, trong
  //  khi thật ra máy chủ trả lỗi (hay gặp nhất: DB chưa chạy migration của khối).
  if (!report) {
    if (!isError || !canEdit) return null
    return (
      <Card className="gap-4 py-4">
        <CardContent className="px-4">
          <p className="text-sm text-destructive">
            Không tải được khối Báo cáo thực hiện. Tải lại trang; nếu vẫn lỗi thì báo quản trị
            hệ thống.
          </p>
        </CardContent>
      </Card>
    )
  }

  const isEmpty = report.phases.length === 0 && report.docs.length === 0 && report.items.length === 0
  //  Khối rỗng với người chỉ xem: ẩn hẳn, khỏi bày một thẻ trắng.
  if (isEmpty && !canEdit) return null

  //  Khối rỗng thì không gấp — lời mời khởi tạo phải thấy ngay, gấp lại thì
  //  người vừa bấm «Thêm Báo cáo thực hiện» phải bấm thêm lần nữa mới thấy gì.
  const showBody = cardOpen || isEmpty

  const docsById = reportDocsById(report)
  const itemNameById = new Map(report.items.map((item) => [item.id, item.name]))
  const trimmedQuery = query.trim()
  const hasDocFilter = statusFilter !== REPORT_STATUS_FILTER_ALL || trimmedQuery !== ''
  //  Hai tầng lọc chồng nhau: trạng thái → từ khóa (soi mọi ô chữ của hồ sơ).
  //  Tầng «nút dòng hàng» không còn là bộ lọc — nó thành dòng bảng sổ được.
  const matchesFilter = (doc: SurveyReportDoc) =>
    (statusFilter === REPORT_STATUS_FILTER_ALL || doc.status === statusFilter) &&
    matchReportDoc(doc, trimmedQuery, itemNameById.get(doc.item_id) ?? '')
  const visibleDocs = report.docs.filter(matchesFilter)
  const doneCount = report.docs.filter(isReportDocDone).length

  //  Hồ sơ CHUNG đứng riêng một dòng chứ không lặp lại dưới mọi nút dòng hàng:
  //  bảng có dòng TỔNG, mà lặp thì một hồ sơ bị đếm nhiều lần. Ô chọn nút trong
  //  hộp sửa hồ sơ vẫn giữ nghĩa cũ («Chung» = áp cho cả phiếu).
  const commonDocs = report.docs.filter((doc) => doc.item_id === COMMON_ROW_ID)
  const rows: ReportItemRow[] = [
    ...(commonDocs.length > 0 || report.items.length === 0
      ? [
          {
            id: COMMON_ROW_ID,
            name: 'Chung (cả phiếu)',
            item: null,
            docs: commonDocs,
          },
        ]
      : []),
    ...report.items.map((item) => ({
      id: item.id,
      name: item.name,
      item,
      docs: report.docs.filter((doc) => doc.item_id === item.id),
    })),
  ]
  //  Đang lọc thì dòng không còn hồ sơ nào khớp ẩn đi; không lọc gì vẫn bày
  //  dòng rỗng để còn sửa/xóa nút đó.
  const visibleRows = rows.filter((row) => !hasDocFilter || row.docs.some(matchesFilter))

  //  Giai đoạn CHƯA CÓ hồ sơ nào không lọt vào dải sổ của dòng hàng nào cả —
  //  bày riêng bên dưới, không thì nó thành bản ghi mồ côi không đường sửa/xóa.
  const orphanPhases = report.phases.filter(
    (phase) => !report.docs.some((doc) => doc.phase_id === phase.id),
  )

  //  Giai đoạn có hồ sơ khớp bộ lọc — dạng xem tổng chỉ bày những giai đoạn này
  //  khi đang lọc, không thì kết quả tìm lọt thỏm giữa một loạt giai đoạn rỗng.
  const visiblePhases = report.phases.filter(
    (phase) => !hasDocFilter || visibleDocs.some((doc) => doc.phase_id === phase.id),
  )

  //  Đang tìm kiếm / lọc trạng thái thì SỔ hết bất kể trạng thái gấp — không thì
  //  kết quả tìm được nằm sau một dòng đang gấp, tưởng là không có.
  const forceOpen = hasDocFilter
  const allRowsOpen = visibleRows.length > 0 && visibleRows.every((row) => openRows.has(row.id))
  const toggleAllRows = () =>
    setOpenRows(allRowsOpen ? new Set() : new Set(visibleRows.map((row) => row.id)))
  const toggleRow = (rowId: number) =>
    setOpenRows((current) => {
      const next = new Set(current)
      if (next.has(rowId)) next.delete(rowId)
      else next.add(rowId)
      return next
    })
  const allPhasesOpen =
    visiblePhases.length > 0 && visiblePhases.every((phase) => !collapsedPhases.has(phase.id))
  const toggleAllPhases = () =>
    setCollapsedPhases(allPhasesOpen ? new Set(visiblePhases.map((phase) => phase.id)) : new Set())
  const togglePhaseCollapse = (phaseId: number) =>
    setCollapsedPhases((current) => {
      const next = new Set(current)
      if (next.has(phaseId)) next.delete(phaseId)
      else next.add(phaseId)
      return next
    })

  //  Nút «Mở tất cả / Thu gọn» gạt ĐÚNG TRỤC đang xem: dạng tổng gạt giai đoạn,
  //  dạng dòng hàng gạt dòng hàng. Một nút, hai nghĩa — vì chỉ một trục hiện ra.
  const allOpen = viewMode === 'phase' ? allPhasesOpen : allRowsOpen
  const toggleAll = viewMode === 'phase' ? toggleAllPhases : toggleAllRows

  const changeViewMode = (mode: ReportViewMode) => {
    setViewMode(mode)
    try {
      localStorage.setItem(VIEW_STORAGE_KEY, mode)
    } catch {
      //  Không ghi nhớ được thì thôi, đổi dạng xem vẫn phải ăn.
    }
  }

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row flex-wrap items-center justify-between gap-3 border-b px-4 pb-3!">
        <button
          type="button"
          aria-expanded={showBody}
          disabled={isEmpty}
          title={showBody ? 'Thu gọn báo cáo thực hiện' : 'Mở báo cáo thực hiện'}
          className="flex min-w-0 flex-1 items-center gap-2 text-left"
          onClick={() => setCardOpen((current) => !current)}
        >
          <ChevronDown
            className={cn(
              'size-4 shrink-0 text-muted-foreground transition-transform',
              !showBody && '-rotate-90',
            )}
          />
          <CardTitle className="text-base text-navy dark:text-foreground">
            Báo cáo thực hiện
          </CardTitle>
          {report.docs.length > 0 && (
            <span className="text-xs whitespace-nowrap text-muted-foreground">
              {doneCount}/{report.docs.length} hồ sơ · {reportPercent(report.docs)}%
            </span>
          )}
        </button>
        {showBody && !isEmpty && (
          <div className="flex flex-wrap items-center justify-end gap-2">
            {/* Nút gạt hai dạng xem. Tự dựng chứ không lấy `Tabs`: đây không phải
                hai trang nội dung mà là một công tắc trong thanh công cụ, đứng
                cạnh các nút khác — `shared/ui/` chưa có toggle-group. */}
            <div className="flex items-center rounded-md border p-0.5">
              <ViewModeButton
                active={viewMode === 'phase'}
                label="Xem tổng"
                title="Xem tổng: hồ sơ xếp theo giai đoạn"
                icon={<LayoutList className="size-3.5" />}
                onClick={() => changeViewMode('phase')}
              />
              <ViewModeButton
                active={viewMode === 'item'}
                label="Theo dòng hàng"
                title="Xem theo dòng hàng: mỗi dòng hàng một dòng, bấm để sổ hồ sơ"
                icon={<Rows3 className="size-3.5" />}
                onClick={() => changeViewMode('item')}
              />
            </div>
            <SearchField
              value={query}
              onChange={setQuery}
              placeholder="Tìm hồ sơ, mô tả, tệp..."
              placeholderShort="Tìm hồ sơ..."
              className="h-8 w-48 flex-none"
              aria-label="Tìm hồ sơ trong báo cáo"
            />
            <Select
              value={String(statusFilter)}
              onValueChange={(value) => setStatusFilter(Number(value))}
            >
              <SelectTrigger size="sm" aria-label="Lọc theo trạng thái hồ sơ">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={String(REPORT_STATUS_FILTER_ALL)}>Mọi trạng thái</SelectItem>
                {Object.entries(REPORT_DOC_STATUS_LABELS).map(([code, label]) => (
                  <SelectItem key={code} value={code}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={toggleAll}>
              {allOpen ? 'Thu gọn' : 'Mở tất cả'}
            </Button>
            {canEdit && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => setPhaseDialog({ phase: null })}
                >
                  <ListPlus />
                  Thêm giai đoạn
                </Button>
                <Button
                  size="sm"
                  disabled={busy || report.phases.length === 0}
                  title={report.phases.length === 0 ? 'Thêm giai đoạn trước' : ''}
                  onClick={() => setDocDialog({ doc: null, itemId: COMMON_ROW_ID })}
                >
                  <Plus />
                  Thêm hồ sơ
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="px-2 text-destructive hover:text-destructive"
                  disabled={busy}
                  aria-label="Xóa báo cáo thực hiện"
                  title="Xóa toàn bộ báo cáo thực hiện (hoàn tác được ở Lịch sử thao tác)"
                  onClick={handleDeleteReport}
                >
                  <Trash2 />
                </Button>
              </>
            )}
          </div>
        )}
      </CardHeader>

      {showBody && (
        <CardContent className="space-y-4 px-4">
          {isEmpty ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <p className="text-sm text-muted-foreground">
                Chưa có báo cáo cho phiếu này. Khởi tạo theo mẫu chung (5 giai đoạn + bộ hồ sơ
                chung + nút theo dòng hàng) rồi chỉnh lại cho hợp, hoặc tự thêm giai đoạn từ
                đầu. Mỗi dòng hàng / giai đoạn có nút «Tạo mẫu» riêng để đổ thêm sau.
              </p>
              <div className="flex gap-2">
                <Button disabled={busy} onClick={() => actions.init.mutate()}>
                  <Sparkles />
                  Khởi tạo báo cáo mẫu
                </Button>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => setPhaseDialog({ phase: null })}
                >
                  <ListPlus />
                  Thêm giai đoạn
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* Câu «rỗng vì bộ lọc» phải khác «chưa có gì» — người gõ nhầm một
                  chữ không được đọc ra "chưa có dữ liệu" (bẫy duoc-CR-322). */}
              {hasDocFilter && visibleDocs.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Không có hồ sơ nào khớp bộ lọc hiện tại
                  {report.docs.length > 0
                    ? ` — phiếu đang có ${report.docs.length} hồ sơ, thử xóa từ khóa hoặc đổi trạng thái.`
                    : '.'}
                </p>
              )}

              {/* Báo cáo tổng thể của CẢ phiếu — đếm bỏ qua ô tìm + lọc trạng
                  thái, giống khung tracking: số tổng không đổi theo từ khóa đang gõ. */}
              <ReportSummary docs={report.docs} />

              {/* Cột trái: thân báo cáo (theo dạng xem) · cột phải: khung tracking */}
              <div className="gap-5 lg:grid lg:grid-cols-[minmax(0,1fr)_215px]">
                <div className="space-y-3">
                  {viewMode === 'phase' ? (
                    <ReportPhaseList
                      phases={report.phases}
                      docs={visibleDocs}
                      docsById={docsById}
                      itemNameById={itemNameById}
                      hasDocFilter={hasDocFilter}
                      forceOpen={forceOpen}
                      collapsedPhases={collapsedPhases}
                      canEdit={canEdit}
                      busy={busy}
                      onTogglePhase={togglePhaseCollapse}
                      onEditPhase={(phase) => setPhaseDialog({ phase })}
                      onAddDoc={(phaseId) =>
                        setDocDialog({ doc: null, itemId: COMMON_ROW_ID, phaseId })
                      }
                      onApplyTemplate={(phaseId) => handleApplyTemplate(COMMON_ROW_ID, phaseId)}
                      onEditDoc={(doc) => setDocDialog({ doc, itemId: doc.item_id })}
                      onDeleteDoc={handleDeleteDoc}
                      onToggleDoc={handleToggleDoc}
                    />
                  ) : (
                    <ReportItemTable
                      report={report}
                      rows={visibleRows}
                      docsById={docsById}
                      matchesFilter={matchesFilter}
                      openRows={openRows}
                      forceOpen={forceOpen}
                      orphanPhases={orphanPhases}
                      canEdit={canEdit}
                      busy={busy}
                      onToggleRow={toggleRow}
                      onAddItem={() => setItemDialog({ item: null })}
                      onEditItem={(item) => setItemDialog({ item })}
                      onAddDoc={(itemId) => setDocDialog({ doc: null, itemId })}
                      onApplyTemplate={(itemId) => handleApplyTemplate(itemId)}
                      onEditDoc={(doc) => setDocDialog({ doc, itemId: doc.item_id })}
                      onDeleteDoc={handleDeleteDoc}
                      onEditPhase={(phase) => setPhaseDialog({ phase })}
                      onToggleDoc={handleToggleDoc}
                    />
                  )}

                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Lock className="size-3" />
                    hồ sơ khóa = chờ hồ sơ tiên quyết hoàn thành trước
                  </span>
                </div>

                <SurveyReportTracking
                  report={report}
                  itemFilter={REPORT_FILTER_ALL}
                  className="hidden lg:block"
                />
              </div>
            </>
          )}
        </CardContent>
      )}

      <SurveyReportDocDialog
        open={docDialog !== null}
        onOpenChange={(open) => {
          if (!open) setDocDialog(null)
        }}
        doc={docDialog?.doc ?? null}
        report={report}
        defaultPhaseId={docDialog?.phaseId ?? report.phases[0]?.id ?? 0}
        defaultItemId={docDialog?.itemId ?? COMMON_ROW_ID}
        defaultAssigneeId={defaultAssigneeId}
        pending={actions.saveDoc.isPending || actions.deleteDoc.isPending}
        onSave={(docId, payload) => actions.saveDoc.mutateAsync({ docId, payload })}
        onDelete={(docId) => actions.deleteDoc.mutateAsync({ docId })}
      />

      <SurveyReportItemDialog
        open={itemDialog !== null}
        onOpenChange={(open) => {
          if (!open) setItemDialog(null)
        }}
        item={itemDialog?.item ?? null}
        pending={actions.saveItem.isPending || actions.deleteItem.isPending}
        onSave={(itemId, name) => actions.saveItem.mutateAsync({ itemId, name })}
        onDelete={(itemId) => actions.deleteItem.mutateAsync({ itemId })}
      />

      <SurveyReportPhaseDialog
        open={phaseDialog !== null}
        onOpenChange={(open) => {
          if (!open) setPhaseDialog(null)
        }}
        phase={phaseDialog?.phase ?? null}
        docCount={
          phaseDialog?.phase
            ? report.docs.filter((doc) => doc.phase_id === phaseDialog.phase?.id).length
            : 0
        }
        pending={actions.savePhase.isPending || actions.deletePhase.isPending}
        onSave={(phaseId, name, location) => actions.savePhase.mutateAsync({ phaseId, name, location })}
        onDelete={(phaseId) => actions.deletePhase.mutateAsync({ phaseId })}
      />
    </Card>
  )
}

/** Một nửa của công tắc dạng xem — nút phẳng, nửa đang chọn nổi lên như tab. */
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
        'flex h-7 items-center gap-1.5 rounded-sm px-2 text-xs font-medium whitespace-nowrap transition-colors',
        active
          ? 'bg-accent text-accent-foreground'
          : 'text-muted-foreground hover:text-foreground',
      )}
      onClick={onClick}
    >
      {icon}
      {label}
    </button>
  )
}

interface ReportPhaseListProps {
  /** TẤT CẢ giai đoạn — số thứ tự phải đếm theo đây chứ không theo danh sách đã lọc. */
  phases: SurveyReportPhase[]
  /** Hồ sơ ĐÃ qua ô tìm + lọc trạng thái. */
  docs: SurveyReportDoc[]
  docsById: Map<number, SurveyReportDoc>
  itemNameById: Map<number, string>
  hasDocFilter: boolean
  forceOpen: boolean
  collapsedPhases: Set<number>
  canEdit: boolean
  busy: boolean
  onTogglePhase: (phaseId: number) => void
  onEditPhase: (phase: SurveyReportPhase) => void
  /** Thêm hồ sơ vào ĐÚNG giai đoạn vừa bấm. */
  onAddDoc: (phaseId: number) => void
  /** Đổ phần mẫu chung của giai đoạn vừa bấm vào hồ sơ Chung. */
  onApplyTemplate: (phaseId: number) => void
  onEditDoc: (doc: SurveyReportDoc) => void
  onDeleteDoc: (doc: SurveyReportDoc) => void
  onToggleDoc: (doc: SurveyReportDoc) => void
}

/**
 * DẠNG XEM TỔNG: toàn bộ hồ sơ của phiếu xếp theo giai đoạn, đọc được trình tự
 * thương vụ từ trên xuống. Giai đoạn RỖNG vẫn bày (khi không lọc) — nó là lời
 * nhắc "khâu này chưa ai khai hồ sơ", và cũng là đường vào để sửa giai đoạn đó.
 */
function ReportPhaseList({
  phases,
  docs,
  docsById,
  itemNameById,
  hasDocFilter,
  forceOpen,
  collapsedPhases,
  canEdit,
  busy,
  onTogglePhase,
  onEditPhase,
  onAddDoc,
  onApplyTemplate,
  onEditDoc,
  onDeleteDoc,
  onToggleDoc,
}: ReportPhaseListProps) {
  return (
    <div className="space-y-4">
      {phases.map((phase, index) => {
        const phaseDocs = docs.filter((doc) => doc.phase_id === phase.id)
        //  Đang lọc mà giai đoạn không còn hồ sơ nào khớp thì giấu cả cụm —
        //  không thì kết quả tìm lọt thỏm giữa một loạt tiêu đề rỗng.
        if (phaseDocs.length === 0 && hasDocFilter) return null
        const collapsed = !forceOpen && collapsedPhases.has(phase.id)
        return (
          <div key={phase.id} className="space-y-2">
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                aria-expanded={!collapsed}
                aria-label={collapsed ? 'Hiện hồ sơ của giai đoạn' : 'Thu gọn giai đoạn'}
                className="-mr-1 rounded-md p-0.5 text-muted-foreground hover:text-foreground"
                onClick={() => onTogglePhase(phase.id)}
              >
                <ChevronDown
                  className={cn('size-4 transition-transform', collapsed && '-rotate-90')}
                />
              </button>
              <span className="grid size-6 place-items-center rounded-md bg-navy text-xs font-semibold text-white dark:bg-muted dark:text-foreground">
                {index + 1}
              </span>
              <span className="text-sm font-semibold">{phase.name}</span>
              {phase.location && (
                <span className="text-xs text-muted-foreground">{phase.location}</span>
              )}
              <PhaseProgressBar docs={phaseDocs} className="ml-auto" />
              {canEdit && (
                <>
                  {/* Đường vào NGẮN NHẤT để khai hồ sơ: bấm ngay tại giai đoạn
                      đang đọc, hộp điền sẵn giai đoạn đó — khỏi phải lên nút
                      chung ở đầu khối rồi tự chọn lại trong ô. */}
                  <button
                    type="button"
                    disabled={busy}
                    title={`Thêm hồ sơ vào giai đoạn "${phase.name}"`}
                    aria-label={`Thêm hồ sơ vào giai đoạn "${phase.name}"`}
                    className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                    onClick={() => onAddDoc(phase.id)}
                  >
                    <Plus className="size-3.5" />
                  </button>
                  {/* «Tạo mẫu» ngay tại giai đoạn: đổ phần mẫu chung của khâu
                      này vào hồ sơ Chung — cộng thêm, có rồi thì bỏ qua. Giai
                      đoạn tự đặt tên (không có trong mẫu) thì backend trả 400
                      kèm danh sách tên hợp lệ, toast lỗi tự hiện. */}
                  <button
                    type="button"
                    disabled={busy}
                    title={`Tạo hồ sơ mẫu vào giai đoạn "${phase.name}"`}
                    aria-label={`Tạo hồ sơ mẫu vào giai đoạn "${phase.name}"`}
                    className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                    onClick={() => onApplyTemplate(phase.id)}
                  >
                    <Sparkles className="size-3.5" />
                  </button>
                  <button
                    type="button"
                    title={`Sửa giai đoạn "${phase.name}"`}
                    aria-label={`Sửa giai đoạn "${phase.name}"`}
                    className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                    onClick={() => onEditPhase(phase)}
                  >
                    <Pencil className="size-3.5" />
                  </button>
                </>
              )}
            </div>
            {collapsed ? null : phaseDocs.length === 0 ? (
              <div className="flex items-center gap-2 pl-8">
                <p className="text-xs text-muted-foreground">Chưa có hồ sơ.</p>
                {canEdit && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      disabled={busy}
                      onClick={() => onAddDoc(phase.id)}
                    >
                      <Plus className="size-3" />
                      Thêm hồ sơ
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-xs"
                      disabled={busy}
                      onClick={() => onApplyTemplate(phase.id)}
                    >
                      <Sparkles className="size-3" />
                      Tạo theo mẫu
                    </Button>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-1.5">
                {phaseDocs.map((doc) => (
                  <ReportDocRow
                    key={doc.id}
                    doc={doc}
                    docsById={docsById}
                    canEdit={canEdit}
                    busy={busy}
                    //  Dạng xem này trộn hồ sơ của mọi dòng hàng nên mỗi dòng
                    //  phải TỰ nói nó thuộc dòng hàng nào.
                    itemName={itemNameById.get(doc.item_id) ?? ''}
                    showItemTag
                    onToggle={() => onToggleDoc(doc)}
                    onEdit={() => onEditDoc(doc)}
                    onDelete={() => onDeleteDoc(doc)}
                  />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

interface ReportItemTableProps {
  report: SurveyRequestReport
  /** Các dòng ĐÃ lọc — dòng không còn hồ sơ nào khớp đã bị bỏ ở tầng trên. */
  rows: ReportItemRow[]
  docsById: Map<number, SurveyReportDoc>
  matchesFilter: (doc: SurveyReportDoc) => boolean
  openRows: Set<number>
  forceOpen: boolean
  orphanPhases: SurveyReportPhase[]
  canEdit: boolean
  busy: boolean
  onToggleRow: (rowId: number) => void
  onAddItem: () => void
  onEditItem: (item: SurveyReportItem) => void
  onAddDoc: (itemId: number) => void
  /** Đổ CẢ mẫu chung (mọi giai đoạn) vào nút dòng hàng vừa bấm. */
  onApplyTemplate: (itemId: number) => void
  onEditDoc: (doc: SurveyReportDoc) => void
  onDeleteDoc: (doc: SurveyReportDoc) => void
  onEditPhase: (phase: SurveyReportPhase) => void
  onToggleDoc: (doc: SurveyReportDoc) => void
}

/**
 * DẠNG XEM THEO DÒNG HÀNG: mỗi dòng hàng một dòng bảng, bấm để sổ hồ sơ của
 * riêng nó (cùng khuôn với «Chi phí theo dòng hàng» của đơn mua hàng nhập khẩu).
 */
function ReportItemTable({
  report,
  rows,
  docsById,
  matchesFilter,
  openRows,
  forceOpen,
  orphanPhases,
  canEdit,
  busy,
  onToggleRow,
  onAddItem,
  onEditItem,
  onAddDoc,
  onApplyTemplate,
  onEditDoc,
  onDeleteDoc,
  onEditPhase,
  onToggleDoc,
}: ReportItemTableProps) {
  const doneCount = report.docs.filter(isReportDocDone).length
  return (
    <>
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Dòng hàng</TableHead>
              <TableHead className="w-20 text-center">Hồ sơ</TableHead>
              <TableHead className="w-20 text-center">Đã xong</TableHead>
              <TableHead className="w-40">Tiến độ</TableHead>
              <TableHead className="w-32">Hạn gần nhất</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => {
              const open = forceOpen || openRows.has(row.id)
              const rowDocs = row.docs.filter(matchesFilter)
              return (
                <Fragment key={row.id}>
                  <TableRow className="cursor-pointer" onClick={() => onToggleRow(row.id)}>
                    <TableCell className="text-muted-foreground">
                      {open ? (
                        <ChevronDown className="size-4" />
                      ) : (
                        <ChevronRight className="size-4" />
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5">
                        <span className="font-medium">{row.name}</span>
                        {row.item && canEdit && (
                          <button
                            type="button"
                            title={`Sửa nút "${row.name}"`}
                            aria-label={`Sửa nút "${row.name}"`}
                            className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                            onClick={(event) => {
                              event.stopPropagation()
                              if (row.item) onEditItem(row.item)
                            }}
                          >
                            <Pencil className="size-3.5" />
                          </button>
                        )}
                      </span>
                    </TableCell>
                    <TableCell className="text-center tabular-nums">{row.docs.length}</TableCell>
                    <TableCell className="text-center tabular-nums">
                      {row.docs.filter(isReportDocDone).length}
                    </TableCell>
                    <TableCell>
                      <PhaseProgressBar docs={row.docs} className="w-full" />
                    </TableCell>
                    <TableCell>
                      <ExpiryChip expiry={nearestExpiry(row.docs)} />
                    </TableCell>
                  </TableRow>
                  {open && (
                    <TableRow className="hover:bg-transparent">
                      <TableCell colSpan={ITEM_TABLE_COLUMNS} className="bg-muted/40 p-3">
                        <ReportRowDetail
                          report={report}
                          docs={rowDocs}
                          docsById={docsById}
                          canEdit={canEdit}
                          busy={busy}
                          addLabel={
                            row.item ? `Thêm hồ sơ cho "${row.name}"` : 'Thêm hồ sơ chung'
                          }
                          templateLabel={
                            row.item ? `Tạo mẫu cho "${row.name}"` : 'Tạo mẫu vào hồ sơ chung'
                          }
                          onAddDoc={() => onAddDoc(row.id)}
                          onApplyTemplate={() => onApplyTemplate(row.id)}
                          onEditDoc={onEditDoc}
                          onDeleteDoc={onDeleteDoc}
                          onEditPhase={onEditPhase}
                          onToggleDoc={onToggleDoc}
                        />
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              )
            })}
            {canEdit && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={ITEM_TABLE_COLUMNS} className="py-1.5">
                  <Button variant="ghost" size="sm" disabled={busy} onClick={onAddItem}>
                    <Plus />
                    Thêm nút dòng hàng
                  </Button>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell colSpan={2} className="font-semibold">
                Tổng cả phiếu
              </TableCell>
              <TableCell className="text-center font-semibold tabular-nums">
                {report.docs.length}
              </TableCell>
              <TableCell className="text-center font-semibold tabular-nums">
                {doneCount}
              </TableCell>
              <TableCell>
                <PhaseProgressBar docs={report.docs} className="w-full" />
              </TableCell>
              <TableCell>
                <ExpiryChip expiry={nearestExpiry(report.docs)} />
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </div>

      {/* Giai đoạn CHƯA CÓ hồ sơ nào không lọt vào dải sổ của dòng hàng nào cả —
          bày riêng, không thì nó thành bản ghi mồ côi không đường sửa/xóa. Dạng
          xem tổng không cần cụm này: ở đó giai đoạn rỗng vẫn đứng đúng chỗ. */}
      {orphanPhases.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span>Giai đoạn chưa có hồ sơ:</span>
          {orphanPhases.map((phase) => (
            <span
              key={phase.id}
              className="inline-flex items-center gap-1 rounded-md border bg-muted/40 py-0.5 pr-1 pl-2 font-medium"
            >
              {phase.name}
              {canEdit && (
                <button
                  type="button"
                  title={`Sửa giai đoạn "${phase.name}"`}
                  aria-label={`Sửa giai đoạn "${phase.name}"`}
                  className="rounded-md p-0.5 hover:text-foreground"
                  onClick={() => onEditPhase(phase)}
                >
                  <Pencil className="size-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </>
  )
}

interface ReportRowDetailProps {
  report: SurveyRequestReport
  /** Hồ sơ của dòng hàng này, ĐÃ qua ô tìm + lọc trạng thái. */
  docs: SurveyReportDoc[]
  docsById: Map<number, SurveyReportDoc>
  canEdit: boolean
  busy: boolean
  addLabel: string
  templateLabel: string
  onAddDoc: () => void
  onApplyTemplate: () => void
  onEditDoc: (doc: SurveyReportDoc) => void
  onDeleteDoc: (doc: SurveyReportDoc) => void
  onEditPhase: (phase: SurveyReportPhase) => void
  onToggleDoc: (doc: SurveyReportDoc) => void
}

/**
 * Dải sổ ra dưới một dòng hàng: hồ sơ của dòng đó, xếp theo GIAI ĐOẠN. Giai
 * đoạn không có hồ sơ của dòng này thì bỏ qua — bày đủ 5 giai đoạn rỗng dưới
 * từng dòng chỉ làm dải sổ dài ra mà không nói thêm điều gì.
 */
function ReportRowDetail({
  report,
  docs,
  docsById,
  canEdit,
  busy,
  addLabel,
  templateLabel,
  onAddDoc,
  onApplyTemplate,
  onEditDoc,
  onDeleteDoc,
  onEditPhase,
  onToggleDoc,
}: ReportRowDetailProps) {
  return (
    <div className="space-y-4">
      {docs.length === 0 ? (
        <p className="text-xs text-muted-foreground">Chưa có hồ sơ nào ở dòng hàng này.</p>
      ) : (
        report.phases.map((phase, index) => {
          const phaseDocs = docs.filter((doc) => doc.phase_id === phase.id)
          if (phaseDocs.length === 0) return null
          return (
            <div key={phase.id} className="space-y-2">
              <div className="flex items-center gap-2.5">
                <span className="grid size-6 place-items-center rounded-md bg-navy text-xs font-semibold text-white dark:bg-muted dark:text-foreground">
                  {index + 1}
                </span>
                <span className="text-sm font-semibold">{phase.name}</span>
                {phase.location && (
                  <span className="text-xs text-muted-foreground">{phase.location}</span>
                )}
                <PhaseProgressBar docs={phaseDocs} className="ml-auto" />
                {canEdit && (
                  <button
                    type="button"
                    title="Sửa giai đoạn"
                    aria-label="Sửa giai đoạn"
                    className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                    onClick={() => onEditPhase(phase)}
                  >
                    <Pencil className="size-3.5" />
                  </button>
                )}
              </div>
              <div className="space-y-1.5">
                {phaseDocs.map((doc) => (
                  <ReportDocRow
                    key={doc.id}
                    doc={doc}
                    docsById={docsById}
                    canEdit={canEdit}
                    busy={busy}
                    onToggle={() => onToggleDoc(doc)}
                    onEdit={() => onEditDoc(doc)}
                    onDelete={() => onDeleteDoc(doc)}
                  />
                ))}
              </div>
            </div>
          )
        })
      )}

      {canEdit && (
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={busy || report.phases.length === 0}
            title={report.phases.length === 0 ? 'Thêm giai đoạn trước' : ''}
            onClick={onAddDoc}
          >
            <Plus />
            {addLabel}
          </Button>
          {/* «Tạo mẫu» cho riêng dòng hàng này (yêu cầu "bấm ở dòng 3 lớp thì
              cũng cho cái nút tạo mẫu"): đổ cả bộ mẫu chung vào nút, giai đoạn
              nào của mẫu chưa có thì backend tự dựng — nên KHÔNG khóa khi chưa
              có giai đoạn như nút bên cạnh. */}
          <Button variant="outline" size="sm" disabled={busy} onClick={onApplyTemplate}>
            <Sparkles />
            {templateLabel}
          </Button>
        </div>
      )}
    </div>
  )
}

/** Mức khẩn của một ngày hết hiệu lực, suy từ số ngày còn lại tới HÔM NAY. */
type ExpiryTone = 'overdue' | 'soon' | 'normal'

interface ExpiryMeta {
  tone: ExpiryTone
  note: string
}

/**
 * Diễn giải ngày hết hiệu lực: quá hạn / sắp hết (≤7 ngày) / còn xa. `null` khi
 * chuỗi rỗng hay sai định dạng. So theo NGÀY địa phương (đặt giờ về 0) — lệch
 * múi giờ làm lệch một ngày, đúng bẫy của `parseLocalDate`.
 */
function expiryMeta(expiry: string): ExpiryMeta | null {
  const date = parseLocalDate(expiry)
  if (!date) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const days = Math.round((date.getTime() - today.getTime()) / 86_400_000)
  if (days < 0) return { tone: 'overdue', note: `Quá hạn ${-days} ngày` }
  if (days === 0) return { tone: 'soon', note: 'Hết hạn hôm nay' }
  if (days <= 7) return { tone: 'soon', note: `Còn ${days} ngày` }
  return { tone: 'normal', note: `Còn ${days} ngày` }
}

/**
 * Diễn giải mốc DỰ ĐỊNH HOÀN TẤT của cả khối (bao-CR-392): trễ n ngày / đến hạn
 * hôm nay / còn n ngày; xong hết rồi thì không còn gì để trễ. `null` khi rỗng.
 */
function plannedMeta(planned: string, docs: SurveyReportDoc[]): ExpiryMeta | null {
  const date = parseLocalDate(planned)
  if (!date) return null
  if (docs.length && docs.every(isReportDocDone)) return { tone: 'normal', note: 'Đã hoàn thành' }
  const late = reportPlanLateDays(docs, toDateInputValue(new Date()))
  if (late > 0) return { tone: 'overdue', note: `Trễ ${late} ngày` }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const days = Math.round((date.getTime() - today.getTime()) / 86_400_000)
  if (days === 0) return { tone: 'soon', note: 'Đến hạn hôm nay' }
  return { tone: 'normal', note: `Còn ${days} ngày` }
}

const EXPIRY_TONE_CLASS: Record<ExpiryTone, string> = {
  overdue: 'bg-destructive/10 text-destructive',
  soon: 'bg-warning/15 text-warning',
  normal: 'bg-muted text-muted-foreground',
}

/** Ô «Hạn gần nhất» của bảng dòng hàng — rỗng thì gạch ngang chứ không để trống. */
function ExpiryChip({ expiry }: { expiry: string }) {
  const meta = expiry ? expiryMeta(expiry) : null
  if (!expiry || !meta) return <span className="text-muted-foreground">—</span>
  return (
    <span
      title={`Hết hiệu lực ${formatDate(expiry)} · ${meta.note}`}
      className={cn(
        'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        EXPIRY_TONE_CLASS[meta.tone],
      )}
    >
      <CalendarClock className="size-3" />
      {formatDate(expiry)}
    </span>
  )
}

/**
 * Thanh tiến độ: fill chạy theo %, TRÊN thanh in `hoàn tất/tổng · %`. Fill dùng
 * màu MỀM (tint) để chữ ở giữa đọc rõ trên cả phần đã tô lẫn phần trống, sáng
 * lẫn tối — thay vì phủ chữ lên một mảng màu đặc rồi lệch tương phản một nửa thanh.
 *
 * `barClassName` / `labelClassName` để dùng lại ở ô tổng (thanh cao hơn, cả bề
 * ngang) mà không đẻ thêm một component thanh thứ hai.
 */
function PhaseProgressBar({
  docs,
  className,
  barClassName,
  labelClassName,
}: {
  docs: SurveyReportDoc[]
  className?: string
  barClassName?: string
  labelClassName?: string
}) {
  const total = docs.length
  const done = docs.filter(isReportDocDone).length
  const percent = reportPercent(docs)
  const complete = total > 0 && done === total
  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${done}/${total} hồ sơ hoàn tất, ${percent}%`}
      title={`${done}/${total} hồ sơ hoàn tất · ${percent}%`}
      className={cn(
        'relative h-5 w-32 shrink-0 overflow-hidden rounded-full border bg-muted/50',
        className,
        barClassName,
      )}
    >
      <div
        className={cn(
          'absolute inset-y-0 left-0 rounded-full transition-[width] duration-500',
          complete ? 'bg-success/35' : 'bg-primary/30',
        )}
        style={{ width: `${percent}%` }}
      />
      <span
        className={cn(
          'absolute inset-0 flex items-center justify-center gap-1 px-2 text-[10px] font-semibold tabular-nums text-foreground/85',
          labelClassName,
        )}
      >
        {done}/{total} · {percent}%
      </span>
    </div>
  )
}

/** Báo cáo TỔNG THỂ của cả phiếu: tổng · đã xong · hết hiệu lực gần nhất · dự định hoàn tất. */
function ReportSummary({ docs }: { docs: SurveyReportDoc[] }) {
  const total = docs.length
  const expiry = nearestExpiry(docs)
  const meta = expiry ? expiryMeta(expiry) : null
  //  Mốc kế hoạch = ngày dự định XA NHẤT trong khối (bao-CR-392).
  const planned = latestPlannedDate(docs)
  const plan = planned ? plannedMeta(planned, docs) : null
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
        <p className="text-xs text-muted-foreground">Tổng hồ sơ</p>
        <p className="text-lg font-semibold tabular-nums">{total}</p>
      </div>
      <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
        <p className="text-xs text-muted-foreground">Đã hoàn thành</p>
        <PhaseProgressBar
          docs={docs}
          barClassName="mt-2 h-6 w-full"
          labelClassName="text-xs text-foreground"
        />
      </div>
      <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <CalendarClock className="size-3" />
          Hết hiệu lực gần nhất
        </p>
        <p
          className={cn(
            'text-lg font-semibold tabular-nums',
            meta?.tone === 'overdue' && 'text-destructive',
            meta?.tone === 'soon' && 'text-warning',
          )}
        >
          {expiry ? formatDate(expiry) : '—'}
          {meta && <span className="ml-1.5 text-xs font-medium">· {meta.note}</span>}
        </p>
      </div>
      <div className="rounded-lg border bg-muted/20 px-3 py-2.5">
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <CalendarCheck className="size-3" />
          Dự định hoàn tất
        </p>
        <p
          className={cn(
            'text-lg font-semibold tabular-nums',
            plan?.tone === 'overdue' && 'text-destructive',
            plan?.tone === 'soon' && 'text-warning',
          )}
        >
          {planned ? formatDate(planned) : '—'}
          {plan && <span className="ml-1.5 text-xs font-medium">· {plan.note}</span>}
        </p>
      </div>
    </div>
  )
}

/**
 * Ô «Dự định hoàn tất» trên dòng hồ sơ (bao-CR-392): đỏ + «Trễ n ngày» khi hồ sơ
 * chưa xong mà qua ngày dự định; đã xong hoặc chưa tới ngày thì xám. Rỗng thì không dựng.
 */
function DocPlannedChip({ doc }: { doc: SurveyReportDoc }) {
  if (!doc.planned_date) return null
  const late = reportDocLateDays(doc, toDateInputValue(new Date()))
  const note = late > 0 ? `Trễ ${late} ngày` : isReportDocDone(doc) ? 'Đã hoàn thành' : ''
  return (
    <span
      title={[`Dự định hoàn tất ${formatDate(doc.planned_date)}`, note].filter(Boolean).join(' · ')}
      className={cn(
        'flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        late > 0 ? EXPIRY_TONE_CLASS.overdue : 'bg-muted text-muted-foreground',
      )}
    >
      <CalendarCheck className="size-3" />
      {formatDate(doc.planned_date)}
      {late > 0 && <span className="font-semibold">· Trễ {late} ngày</span>}
    </span>
  )
}

/** Ô ngày trên dòng hồ sơ: hiện hạn hết hiệu lực (tô màu theo độ khẩn), hoặc
 *  ngày bắt đầu khi chưa đặt hạn. Rê chuột đọc cả hai mốc. Rỗng thì không dựng. */
function DocDateChip({ doc }: { doc: SurveyReportDoc }) {
  if (!doc.expires_at && !doc.start_date) return null
  const meta = doc.expires_at ? expiryMeta(doc.expires_at) : null
  const title = [
    doc.start_date && `Bắt đầu ${formatDate(doc.start_date)}`,
    doc.expires_at && `Hết hiệu lực ${formatDate(doc.expires_at)}`,
    meta?.note,
  ]
    .filter(Boolean)
    .join(' · ')
  return (
    <span
      title={title}
      className={cn(
        'flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] font-medium tabular-nums',
        meta ? EXPIRY_TONE_CLASS[meta.tone] : 'bg-muted text-muted-foreground',
      )}
    >
      <CalendarClock className="size-3" />
      {doc.expires_at ? formatDate(doc.expires_at) : `Từ ${formatDate(doc.start_date)}`}
    </span>
  )
}

/** Vòng tròn chữ viết tắt của nhân sự thực hiện — rê chuột đọc tên đầy đủ. */
function DocAssignee({ name }: { name: string }) {
  if (!name) return null
  return (
    <span
      title={`Người thực hiện: ${name}`}
      className="grid size-6 shrink-0 place-items-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary"
    >
      {nameInitials(name)}
    </span>
  )
}

interface ReportDocRowProps {
  doc: SurveyReportDoc
  docsById: Map<number, SurveyReportDoc>
  canEdit: boolean
  busy: boolean
  /** Tên dòng hàng của hồ sơ — rỗng = hồ sơ CHUNG. Chỉ dùng khi `showItemTag`. */
  itemName?: string
  /** Bày thẻ tên dòng hàng không. Dạng xem theo dòng hàng thì KHÔNG: dòng bảng
   *  bên trên đã nói rồi, lặp lại chỉ chiếm chỗ của mô tả. */
  showItemTag?: boolean
  onToggle: () => void
  onEdit: () => void
  onDelete: () => void
}

function ReportDocRow({
  doc,
  docsById,
  canEdit,
  busy,
  itemName = '',
  showItemTag = false,
  onToggle,
  onEdit,
  onDelete,
}: ReportDocRowProps) {
  const done = isReportDocDone(doc)
  const locked = isReportDocLocked(doc, docsById)
  const waiting = pendingDepends(doc, docsById)
  const isLink = /^https?:\/\//i.test(doc.file_note)

  //  MỘT DÒNG cho mỗi hồ sơ: tiêu đề bên trái, mô tả co giãn ở giữa (cắt bớt,
  //  rê chuột đọc đủ), khóa tiên quyết / đính kèm / trạng thái / sửa dồn phải —
  //  đính kèm và sửa chỉ còn icon. Chi tiết đầy đủ nằm ở hộp Sửa. Tên nút dòng
  //  hàng KHÔNG lặp ở đây nữa: dòng bảng bên trên đã nói rồi.
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border bg-card py-1.5 pr-1.5 pl-3',
        locked && 'opacity-70',
      )}
    >
      <button
        type="button"
        aria-label={done ? 'Mở lại hồ sơ' : 'Đánh dấu hoàn thành'}
        title={locked ? 'Chờ hồ sơ tiên quyết hoàn thành trước' : ''}
        disabled={!canEdit || locked || busy}
        className={cn(
          'grid size-5 shrink-0 place-items-center rounded-md border-2 transition-colors',
          done
            ? 'border-success bg-success text-white'
            : 'border-input bg-muted/50 text-transparent hover:border-success/60',
          (!canEdit || locked) && 'cursor-not-allowed',
        )}
        onClick={onToggle}
      >
        <Check className="size-3.5" />
      </button>

      {showItemTag && (
        <span
          title={itemName || 'Chung (cả phiếu)'}
          className={cn(
            'max-w-36 shrink-0 truncate rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase',
            itemName ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground',
          )}
        >
          {itemName || 'Chung'}
        </span>
      )}

      <span className="max-w-[45%] shrink-0 truncate text-sm font-medium" title={doc.title}>
        {doc.title}
      </span>
      {doc.required && (
        <span className="shrink-0 rounded-full bg-destructive/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-destructive">
          Bắt buộc
        </span>
      )}

      {/* Mô tả chiếm phần còn lại của dòng — cũng là khoảng đệm khi rỗng. */}
      <span
        className="min-w-0 flex-1 truncate text-xs text-muted-foreground"
        title={doc.description || undefined}
      >
        {doc.description}
      </span>

      {doc.depends.length > 0 && waiting.length > 0 && (
        <span
          className="shrink-0 text-destructive"
          title={`Chờ hồ sơ tiên quyết: ${waiting.map((dep) => dep.title).join(', ')}`}
        >
          <Lock className="size-3.5" />
        </span>
      )}

      {isLink ? (
        <a
          href={doc.file_note}
          target="_blank"
          rel="noreferrer"
          title={doc.file_note}
          aria-label="Mở tệp đính kèm"
          className="grid size-7 shrink-0 place-items-center rounded-md text-primary hover:bg-accent"
        >
          <Paperclip className="size-3.5" />
        </a>
      ) : (
        <button
          type="button"
          title={
            doc.file_note ||
            (canEdit ? 'Chưa có tệp — bấm để dán tên tệp/link trong hộp sửa' : 'Chưa có tệp')
          }
          aria-label="Tệp đính kèm"
          onClick={canEdit ? onEdit : undefined}
          className={cn(
            'grid size-7 shrink-0 place-items-center rounded-md',
            doc.file_note ? 'text-foreground' : 'text-muted-foreground/50',
            canEdit ? 'hover:bg-accent hover:text-foreground' : 'cursor-default',
          )}
        >
          <Paperclip className="size-3.5" />
        </button>
      )}

      <DocPlannedChip doc={doc} />
      <DocDateChip doc={doc} />
      <DocAssignee name={doc.assignee_name} />

      <span
        className={cn(
          'shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap',
          STATUS_PILL[doc.status] ?? STATUS_PILL[0],
        )}
      >
        {doc.status_label}
      </span>
      {canEdit && (
        <>
          <Button
            variant="outline"
            size="icon"
            className="size-7 shrink-0"
            aria-label="Sửa hồ sơ"
            title="Sửa hồ sơ"
            onClick={onEdit}
          >
            <Pencil className="size-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-7 shrink-0 text-destructive hover:text-destructive"
            aria-label="Xóa hồ sơ"
            title="Xóa hồ sơ"
            disabled={busy}
            onClick={onDelete}
          >
            <Trash2 className="size-3.5" />
          </Button>
        </>
      )}
    </div>
  )
}
