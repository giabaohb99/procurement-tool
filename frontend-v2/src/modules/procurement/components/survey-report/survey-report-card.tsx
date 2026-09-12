import {
  CalendarClock,
  Check,
  ChevronDown,
  ChevronsDownUp,
  ChevronsUpDown,
  ListPlus,
  Lock,
  Paperclip,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { cn } from '@/shared/utils/cn'
import { formatDate, parseLocalDate } from '@/shared/utils/format-date'
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
import { useSurveyReportActions, useSurveyRequestReport } from '../../hooks/use-survey-request-report'
import {
  REPORT_DOC_DOING,
  REPORT_DOC_DONE,
  REPORT_DOC_STATUS_LABELS,
  type SurveyReportDoc,
  type SurveyReportItem,
  type SurveyReportPhase,
} from '../../types/survey-request-report'
import {
  REPORT_FILTER_ALL,
  REPORT_STATUS_FILTER_ALL,
  filterReportDocs,
  isReportDocDone,
  isReportDocLocked,
  matchReportDoc,
  nearestExpiry,
  pendingDepends,
  reportDocsById,
  reportPercent,
} from '../../utils/survey-report-helpers'
import { SurveyReportDocDialog } from './survey-report-doc-dialog'
import { SurveyReportItemDialog } from './survey-report-item-dialog'
import { SurveyReportPhaseDialog } from './survey-report-phase-dialog'
import { SurveyReportTracking } from './survey-report-tracking'

/** Màu viền trái + pill theo mã trạng thái hồ sơ (0..3). */
const STATUS_BORDER: Record<number, string> = {
  0: 'border-l-muted-foreground/40',
  1: 'border-l-warning',
  2: 'border-l-primary',
  3: 'border-l-success',
}
const STATUS_PILL: Record<number, string> = {
  0: 'bg-muted text-muted-foreground',
  1: 'bg-warning/15 text-warning',
  2: 'bg-primary/10 text-primary',
  3: 'bg-success/15 text-success',
}

interface SurveyReportCardProps {
  surveyRequestId: number
  /** NS Thu mua (cờ `process`) mới sửa được — backend gác lại lần nữa. */
  canEdit: boolean
  /** Gọi sau khi XÓA cả khối — để trang ẩn khối (bỏ cờ "vừa bấm Thêm"). */
  onDeleted?: () => void
}

/**
 * Khối BÁO CÁO THỰC HIỆN trên chi tiết YCBG: hồ sơ chia theo giai đoạn, lọc
 * theo nút dòng hàng (thêm/sửa/xóa nút được), hồ sơ khóa khi tiên quyết chưa
 * xong. Người không có quyền sửa vẫn xem được; khối rỗng thì ẩn hẳn với họ.
 */
export function SurveyReportCard({ surveyRequestId, canEdit, onDeleted }: SurveyReportCardProps) {
  const { data: report, isLoading } = useSurveyRequestReport(surveyRequestId)
  const actions = useSurveyReportActions(surveyRequestId)
  const { user } = useAuth()
  //  Hồ sơ mới điền sẵn người thực hiện = người đang đăng nhập (đổi được).
  const defaultAssigneeId = user?.employee_id ?? 0

  const [filter, setFilter] = useState(REPORT_FILTER_ALL)
  const [statusFilter, setStatusFilter] = useState(REPORT_STATUS_FILTER_ALL)
  const [query, setQuery] = useState('')
  /** Giai đoạn đang THU GỌN (ẩn hồ sơ con). Nút trên header gạt cả loạt. */
  const [collapsedPhases, setCollapsedPhases] = useState<Set<number>>(new Set())
  const [docDialog, setDocDialog] = useState<{ doc: SurveyReportDoc | null } | null>(null)
  const [itemDialog, setItemDialog] = useState<{ item: SurveyReportItem | null } | null>(null)
  const [phaseDialog, setPhaseDialog] = useState<{ phase: SurveyReportPhase | null } | null>(null)

  const busy =
    actions.init.isPending ||
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
    onDeleted?.()
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
  if (!report) return null

  const isEmpty = report.phases.length === 0 && report.docs.length === 0 && report.items.length === 0
  //  Khối rỗng với người chỉ xem: ẩn hẳn, khỏi bày một thẻ trắng.
  if (isEmpty && !canEdit) return null

  //  Nút đang lọc vừa bị xóa thì rơi về «Tất cả».
  const activeFilter =
    filter !== REPORT_FILTER_ALL && !report.items.some((item) => item.id === filter)
      ? REPORT_FILTER_ALL
      : filter

  const docsById = reportDocsById(report)
  const itemNameById = new Map(report.items.map((item) => [item.id, item.name]))
  const trimmedQuery = query.trim()
  //  Ba tầng lọc chồng nhau: nút dòng hàng → trạng thái → từ khóa (soi mọi ô chữ).
  const visibleDocs = filterReportDocs(report.docs, activeFilter).filter(
    (doc) =>
      (statusFilter === REPORT_STATUS_FILTER_ALL || doc.status === statusFilter) &&
      matchReportDoc(doc, trimmedQuery, itemNameById.get(doc.item_id) ?? ''),
  )
  const hasDocFilter =
    activeFilter !== REPORT_FILTER_ALL ||
    statusFilter !== REPORT_STATUS_FILTER_ALL ||
    trimmedQuery !== ''
  const doneCount = report.docs.filter(isReportDocDone).length

  //  Đang tìm kiếm / lọc trạng thái thì MỞ hết bất kể trạng thái thu gọn —
  //  không thì kết quả tìm được nằm sau một giai đoạn đang gấp, tưởng là không có.
  const forceExpanded = trimmedQuery !== '' || statusFilter !== REPORT_STATUS_FILTER_ALL
  const allCollapsed =
    report.phases.length > 0 && report.phases.every((phase) => collapsedPhases.has(phase.id))
  const toggleCollapseAll = () =>
    setCollapsedPhases(allCollapsed ? new Set() : new Set(report.phases.map((phase) => phase.id)))
  const togglePhaseCollapse = (phaseId: number) =>
    setCollapsedPhases((current) => {
      const next = new Set(current)
      if (next.has(phaseId)) next.delete(phaseId)
      else next.add(phaseId)
      return next
    })

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Báo cáo thực hiện
        </CardTitle>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {report.docs.length > 0 && (
            <span className="text-xs whitespace-nowrap text-muted-foreground">
              {doneCount}/{report.docs.length} hồ sơ · {reportPercent(report.docs)}%
            </span>
          )}
          {!isEmpty && (
            <>
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
              <Button
                variant="outline"
                size="sm"
                className="px-2"
                aria-label={allCollapsed ? 'Hiện tất cả hồ sơ con' : 'Thu gọn tất cả hồ sơ con'}
                title={allCollapsed ? 'Hiện tất cả hồ sơ con' : 'Thu gọn tất cả hồ sơ con'}
                onClick={toggleCollapseAll}
              >
                {allCollapsed ? <ChevronsUpDown /> : <ChevronsDownUp />}
              </Button>
            </>
          )}
          {canEdit && !isEmpty && (
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
                onClick={() => setDocDialog({ doc: null })}
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
      </CardHeader>

      <CardContent className="space-y-4 px-4">
        {isEmpty ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm text-muted-foreground">
              Chưa có báo cáo cho phiếu này. Khởi tạo khung mẫu (5 giai đoạn + nút theo dòng
              hàng) rồi chỉnh lại cho hợp, hoặc tự thêm giai đoạn từ đầu.
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
            {/* Bộ lọc theo nút dòng hàng + quản lý nút */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex flex-wrap items-center gap-0.5 rounded-lg border bg-muted/50 p-0.5">
                <FilterChip
                  active={activeFilter === REPORT_FILTER_ALL}
                  label="Tất cả"
                  onClick={() => setFilter(REPORT_FILTER_ALL)}
                />
                {report.items.map((item) => (
                  <FilterChip
                    key={item.id}
                    active={activeFilter === item.id}
                    label={item.name}
                    onClick={() => setFilter(item.id)}
                    onEdit={canEdit ? () => setItemDialog({ item }) : undefined}
                    editTitle={`Sửa nút "${item.name}"`}
                  />
                ))}
                {canEdit && (
                  <button
                    type="button"
                    className="rounded-md p-1.5 text-muted-foreground hover:text-foreground"
                    title="Thêm nút dòng hàng"
                    onClick={() => setItemDialog({ item: null })}
                  >
                    <Plus className="size-3.5" />
                  </button>
                )}
              </div>
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Lock className="size-3" />
                hồ sơ khóa = chờ hồ sơ tiên quyết hoàn thành trước
              </span>
            </div>

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

            {/* Báo cáo tổng thể của nút đang chọn — đếm theo PHẠM VI NÚT (bỏ
                qua ô tìm + lọc trạng thái), giống khung tracking: số tổng thể
                không đổi theo từ khóa đang gõ. */}
            <ReportSummary docs={filterReportDocs(report.docs, activeFilter)} />

            {/* Cột trái: hồ sơ theo giai đoạn · cột phải: khung tracking */}
            <div className="gap-5 lg:grid lg:grid-cols-[minmax(0,1fr)_215px]">
              <div className="space-y-4">
            {report.phases.map((phase, index) => {
              const phaseDocs = visibleDocs.filter((doc) => doc.phase_id === phase.id)
              //  Đang lọc (nút / trạng thái / từ khóa) thì giai đoạn không có hồ
              //  sơ khớp ẩn đi; không lọc gì vẫn bày giai đoạn rỗng để sửa/xóa nó.
              if (phaseDocs.length === 0 && hasDocFilter) return null
              const isCollapsed = !forceExpanded && collapsedPhases.has(phase.id)
              return (
                <div key={phase.id} className="space-y-2">
                  <div className="flex items-center gap-2.5">
                    <button
                      type="button"
                      aria-expanded={!isCollapsed}
                      aria-label={isCollapsed ? 'Hiện hồ sơ của giai đoạn' : 'Thu gọn giai đoạn'}
                      title={isCollapsed ? 'Hiện hồ sơ của giai đoạn' : 'Thu gọn giai đoạn'}
                      className="-mr-1 rounded-md p-0.5 text-muted-foreground hover:text-foreground"
                      onClick={() => togglePhaseCollapse(phase.id)}
                    >
                      <ChevronDown
                        className={cn('size-4 transition-transform', isCollapsed && '-rotate-90')}
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
                      <button
                        type="button"
                        className="rounded-md p-1 text-muted-foreground hover:text-foreground"
                        title="Sửa giai đoạn"
                        onClick={() => setPhaseDialog({ phase })}
                      >
                        <Pencil className="size-3.5" />
                      </button>
                    )}
                  </div>

                  {isCollapsed ? null : phaseDocs.length === 0 ? (
                    <p className="pl-8 text-xs text-muted-foreground">Chưa có hồ sơ.</p>
                  ) : (
                    <div className="space-y-1.5">
                      {phaseDocs.map((doc) => (
                        <ReportDocRow
                          key={doc.id}
                          doc={doc}
                          report={report}
                          docsById={docsById}
                          canEdit={canEdit}
                          busy={busy}
                          onToggle={() =>
                            actions.setDocStatus.mutate({
                              docId: doc.id,
                              status: isReportDocDone(doc) ? REPORT_DOC_DOING : REPORT_DOC_DONE,
                            })
                          }
                          onEdit={() => setDocDialog({ doc })}
                        />
                      ))}
                    </div>
                  )}

                </div>
              )
            })}
              </div>
              <SurveyReportTracking
                report={report}
                itemFilter={activeFilter}
                className="hidden lg:block"
              />
            </div>
          </>
        )}
      </CardContent>

      <SurveyReportDocDialog
        open={docDialog !== null}
        onOpenChange={(open) => {
          if (!open) setDocDialog(null)
        }}
        doc={docDialog?.doc ?? null}
        report={report}
        defaultPhaseId={report.phases[0]?.id ?? 0}
        defaultItemId={activeFilter === REPORT_FILTER_ALL ? 0 : activeFilter}
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

interface FilterChipProps {
  active: boolean
  label: string
  onClick: () => void
  /** Có mặt = hiện bút chì sửa NGAY TRONG khung của nút (một khối liền). */
  onEdit?: () => void
  editTitle?: string
}

/**
 * Một nút lọc của dãy nút dòng hàng. Nhãn và bút chì sửa nằm CHUNG một khung —
 * hai nút HTML riêng (bấm nhãn để lọc, bấm bút chì để sửa) nhưng đọc ra một khối.
 */
function FilterChip({ active, label, onClick, onEdit, editTitle }: FilterChipProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md transition-colors',
        active ? 'bg-primary shadow-sm' : 'hover:bg-background/60',
      )}
    >
      <button
        type="button"
        aria-pressed={active}
        className={cn(
          'rounded-md py-1 pl-3 text-xs font-medium transition-colors',
          onEdit ? 'pr-1.5' : 'pr-3',
          active ? 'text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
        )}
        onClick={onClick}
      >
        {label}
      </button>
      {onEdit && (
        <button
          type="button"
          title={editTitle}
          className={cn(
            'rounded-md py-1.5 pr-2 pl-0.5 transition-colors',
            active
              ? 'text-primary-foreground/80 hover:text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground',
          )}
          onClick={onEdit}
        >
          <Pencil className="size-3" />
        </button>
      )}
    </span>
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

const EXPIRY_TONE_CLASS: Record<ExpiryTone, string> = {
  overdue: 'bg-destructive/10 text-destructive',
  soon: 'bg-warning/15 text-warning',
  normal: 'bg-muted text-muted-foreground',
}

/** Báo cáo TỔNG THỂ của nút đang chọn: tổng · đã xong · hết hiệu lực gần nhất. */
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

function ReportSummary({ docs }: { docs: SurveyReportDoc[] }) {
  const total = docs.length
  const expiry = nearestExpiry(docs)
  const meta = expiry ? expiryMeta(expiry) : null
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
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
    </div>
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
  report: { items: SurveyReportItem[] }
  docsById: Map<number, SurveyReportDoc>
  canEdit: boolean
  busy: boolean
  onToggle: () => void
  onEdit: () => void
}

function ReportDocRow({ doc, report, docsById, canEdit, busy, onToggle, onEdit }: ReportDocRowProps) {
  const done = isReportDocDone(doc)
  const locked = isReportDocLocked(doc, docsById)
  const waiting = pendingDepends(doc, docsById)
  const itemName = doc.item_id
    ? (report.items.find((item) => item.id === doc.item_id)?.name ?? '')
    : ''
  const isLink = /^https?:\/\//i.test(doc.file_note)

  //  MỘT DÒNG cho mỗi hồ sơ: tiêu đề + tag bên trái, mô tả co giãn ở giữa
  //  (cắt bớt, rê chuột đọc đủ), khóa tiên quyết / đính kèm / trạng thái / sửa
  //  dồn phải — đính kèm và sửa chỉ còn icon. Chi tiết đầy đủ nằm ở hộp Sửa.
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border border-l-4 bg-card py-1.5 pr-1.5 pl-3',
        STATUS_BORDER[doc.status] ?? STATUS_BORDER[0],
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

      <span className="max-w-[45%] shrink-0 truncate text-sm font-medium" title={doc.title}>
        {doc.title}
      </span>
      <span
        title={itemName || 'Chung'}
        className={cn(
          'max-w-36 shrink-0 truncate rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
          doc.item_id ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground',
        )}
      >
        {itemName || 'Chung'}
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
      )}
    </div>
  )
}
