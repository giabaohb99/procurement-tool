import {
  ArrowLeft,
  Ban,
  Check,
  CheckCheck,
  CornerUpLeft,
  Loader2,
  Plus,
  Rows3,
  Save,
  Send,
  Trash2,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import type { AuthUser } from '@/core/auth/auth-types'
import { useAuth } from '@/core/auth/use-auth'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { SURVEY_APPROVE_STATUS, labelOf } from '@/shared/constants/statuses'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { purchaseRequestSupportApi } from '../api/purchase-request-support-api'
import type { SurveyLineApproveItem } from '../api/survey-api'
import { DocumentAttachmentsCard } from '../components/document-attachments-card'
import { DocumentComments } from '../components/document-comments'
import { StatusBadge } from '../components/document-status-badge'
import { SurveyInfoCard } from '../components/survey-info-card'
import { SurveyLineDialog } from '../components/survey-line-dialog'
import { SurveyLinesTable } from '../components/survey-lines-table'
import {
  shiftPendingAfterInsert,
  shiftPendingAfterRemove,
  type PendingLineFiles,
} from '../helpers/pending-line-files'
import { buildSurveyCatalog } from '../helpers/survey-catalog'
import {
  applyLineChange,
  lineHasContent,
  makeEmptyLine,
  prefillLineFromHeader,
  toPayloadLines,
  validateSurveySubmit,
} from '../helpers/survey-line'
import {
  useDeleteSurvey,
  useFillSurveyLine,
  useSaveSurvey,
  useSurvey,
  useSurveyAction,
  useSurveyLineApprove,
} from '../hooks/use-survey'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
} from '../hooks/use-purchase-request-support'
import { useSurveyRequests } from '../hooks/use-purchase-documents'
import { SURVEY_STATUS_LABELS } from '../types/purchase-document'
import {
  MANAGER_KEYS,
  SURVEY_TABLE_LABELS,
  isSurveyDeletable,
  isSurveyEditable,
  sectionsOf,
  type SurveyDetail,
  type SurveyLine,
  type SurveyTable,
} from '../types/survey-detail'

/** Đính kèm của ĐẦU phiếu và của TỪNG DÒNG là hai entity khác nhau ở backend. */
const HEAD_ATTACHMENT_ENTITY = 'survey'
const LINE_ATTACHMENT_ENTITY = 'survey_line'

const TABLES: SurveyTable[] = ['supplier', 'product']

type ReasonAction = 'reject' | 'cancel'

const REASON_ACTIONS: Record<ReasonAction, { title: string; description: string }> = {
  reject: {
    title: 'Trả về cho người khảo sát',
    description: 'Phiếu chuyển sang Bị trả lại để người khảo sát sửa rồi gửi duyệt lại.',
  },
  cancel: {
    title: 'Từ chối phiếu',
    description: 'Phiếu bị khóa hẳn, không sửa lại được — muốn làm tiếp phải lập phiếu mới.',
  },
}

/** Giỏ tệp chờ, tách theo bảng: hai bảng đánh số dòng riêng nên không dùng chung được. */
type PendingByTable = Record<SurveyTable, PendingLineFiles>

const EMPTY_PENDING: PendingByTable = { supplier: {}, product: {} }

interface OpenLine {
  table: SurveyTable
  index: number
  /** `fill` = phiếu đã gửi, TP/QL báo thiếu và người khảo sát điền bù đúng dòng đó. */
  mode: 'edit' | 'fill'
}

/**
 * Chi tiết PHIẾU KHẢO SÁT.
 *
 * Một phiếu gánh hai bảng dòng độc lập (NCC và Sản phẩm) và ba khung nhìn chồng
 * lên nhau:
 * - NGƯỜI KHẢO SÁT (NSPT) nhập dòng, lưu dở nhiều lần rồi mới gửi duyệt;
 * - TP/QL duyệt theo TỪNG DÒNG (bốn trạng thái) rồi mới chốt cả phiếu;
 * - Dòng bị đánh "Thiếu thông tin" vẫn phải điền bù được KHI PHIẾU ĐÃ GỬI — đó
 *   là đường `fill`, không phải sửa cả phiếu.
 *
 * Nội dung dòng khai báo thành dữ liệu ở `types/survey-detail.ts`; luật nghiệp vụ
 * (thành tiền, dòng rỗng, kiểm tra trước khi gửi) ở `helpers/survey-line.ts`.
 * Trang này chỉ còn phần trạng thái và điều phối.
 */
export function SurveyDetailPage() {
  const { id } = useParams()
  // Route tạo mới là route tĩnh `/new` nên `useParams()` trả `undefined`.
  const isNew = !id || id === 'new'
  const surveyId = isNew ? 0 : Number(id)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const { can } = usePermission()

  const { data: serverData, isLoading, isError } = useSurvey(surveyId)
  const { data: suppliersData } = useSuppliers(
    { page_size: 1000, is_active: true },
    { enabled: can('supplier', 'read') },
  )
  const { data: unitsData } = usePurchaseRequestUnits()
  const { data: itemGroupsData } = usePurchaseRequestItemGroups()
  const { data: surveyRequestsData } = useSurveyRequests({ page_size: 1000 })

  const saveSurvey = useSaveSurvey()
  const runAction = useSurveyAction(surveyId)
  const deleteSurvey = useDeleteSurvey()
  const saveLineApprove = useSurveyLineApprove(surveyId)
  const fillLine = useFillSurveyLine(surveyId)

  const [draft, setDraft] = useState<SurveyDetail | null>(() =>
    isNew ? createEmptySurvey(user, searchParams.get('sr'), searchParams.get('sr_code')) : null,
  )
  const [openLine, setOpenLine] = useState<OpenLine | null>(null)
  const [selected, setSelected] = useState<Record<SurveyTable, Set<number>>>({
    supplier: new Set(),
    product: new Set(),
  })
  const [invalid, setInvalid] = useState<Set<string>>(new Set())
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [reason, setReason] = useState('')
  const [bulkFor, setBulkFor] = useState<SurveyTable | null>(null)
  const [bulkCount, setBulkCount] = useState('3')
  const [pendingFiles, setPendingFiles] = useState<PendingByTable>(EMPTY_PENDING)

  // Tạo mới -> dựng phiếu rỗng; xem phiếu có sẵn -> nạp dữ liệu server.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook sau không chạy.
  const isNewChanged = useHasChanged(isNew)
  const serverDataChanged = useHasChanged(serverData)
  const userChanged = useHasChanged(user)
  if (isNewChanged || serverDataChanged || userChanged) {
    setDraft(
      isNew
        ? (current) =>
            current ??
            createEmptySurvey(user, searchParams.get('sr'), searchParams.get('sr_code'))
        : (serverData ?? null),
    )
  }

  // Mở từ nút "Tạo phiếu khảo sát" của YCBG: chép Mục đích khảo sát sang Nội dung
  // chính. Phải đợi danh mục YCBG tải xong mới có `purpose`, nên làm ở nhịp riêng.
  const surveyRequestsChanged = useHasChanged(surveyRequestsData)
  if (isNew && surveyRequestsChanged && draft?.survey_request_id && !draft.main_content) {
    const source = (surveyRequestsData?.items ?? []).find(
      (request) => request.id === draft.survey_request_id,
    )
    if (source?.purpose) {
      const purpose = source.purpose
      const code = source.code
      setDraft((current) =>
        current ? { ...current, main_content: purpose, sr_code: current.sr_code || code } : current,
      )
    }
  }

  const suppliers = useMemo(() => suppliersData?.items ?? [], [suppliersData])
  // Danh mục ĐVT / Nhóm hàng trả về bản ghi đầy đủ, nhưng chứng từ lưu TÊN.
  const unitNames = useMemo(() => (unitsData?.items ?? []).map((unit) => unit.name), [unitsData])
  const itemGroupNames = useMemo(
    () => (itemGroupsData?.items ?? []).map((group) => group.name),
    [itemGroupsData],
  )
  const catalog = useMemo(() => buildSurveyCatalog(suppliers, unitNames), [suppliers, unitNames])

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-20 w-full" />
        <Skeleton className="mb-4 h-72 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (!isNew && (isError || !serverData)) {
    return (
      <ErrorState
        title="Không mở được phiếu khảo sát"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.surveys)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  // Biến ổn định để các callback bên dưới giữ được kiểu non-null sau nhánh lỗi.
  const data =
    serverData ?? draft ?? createEmptySurvey(user, searchParams.get('sr'), searchParams.get('sr_code'))
  const loadedDraft = draft ?? data
  const status = data.status

  const editable =
    (isNew || isSurveyEditable(status)) && can('survey', isNew ? 'create' : 'write')
  const canApprove = can('survey', 'approve')
  /** Hai ô duyệt dòng mở sớm hơn nút Duyệt cả phiếu — TP/QL ghi nhận xét dần. */
  const canEditApprove = canApprove && (isNew || ['draft', 'rejected', 'submitted'].includes(status))
  /** Phiếu đang chờ duyệt: đổi ô duyệt dòng là ghi thẳng xuống server, không chờ Lưu. */
  const liveApprove = !isNew && status === 'submitted' && canApprove
  const canFill = can('survey', 'write')

  function patch(changes: Partial<SurveyDetail>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  function linesOf(table: SurveyTable): SurveyLine[] {
    return table === 'supplier' ? loadedDraft.supplier_lines : loadedDraft.product_lines
  }

  function setLines(table: SurveyTable, lines: SurveyLine[]) {
    patch(table === 'supplier' ? { supplier_lines: lines } : { product_lines: lines })
  }

  function setSelectedOf(table: SurveyTable, next: Set<number>) {
    setSelected((current) => ({ ...current, [table]: next }))
  }

  function setPendingOf(table: SurveyTable, next: PendingLineFiles) {
    setPendingFiles((current) => ({ ...current, [table]: next }))
  }

  /** Đổi một ô của dòng. Ô duyệt được ghi ngay khi phiếu đang chờ duyệt. */
  function changeLine(table: SurveyTable, index: number, changes: Partial<SurveyLine>) {
    const lines = linesOf(table)
    const nextLine = applyLineChange(lines[index], changes)
    setLines(
      table,
      lines.map((line, i) => (i === index ? nextLine : line)),
    )

    // Sửa ô nào thì bỏ tô đỏ ô đó — giữ lại là người dùng tưởng vẫn còn thiếu.
    setInvalid((current) => {
      if (!current.size) return current
      const next = new Set(current)
      for (const key of Object.keys(changes)) next.delete(`${table}-${index}-${key}`)
      return next.size === current.size ? current : next
    })

    const lineId = typeof nextLine.id === 'number' ? nextLine.id : 0
    if (liveApprove && lineId > 0 && 'line_approve' in changes) {
      void saveLineApprove.mutateAsync(approveOnlyPayload(table, [toApproveItem(nextLine, lineId)]))
    }
  }

  function addLines(table: SurveyTable, count: number) {
    const seed = prefillLineFromHeader(table, loadedDraft)
    const added = Array.from({ length: count }, () => ({ ...makeEmptyLine(table), ...seed }))
    setLines(table, [...linesOf(table), ...added])
  }

  function duplicateLine(table: SurveyTable, index: number) {
    const lines = linesOf(table)
    // Bản sao là dòng MỚI: bỏ id để backend chèn thêm chứ không ghi đè dòng gốc.
    const { id: _ignored, ...cloned } = lines[index]
    setLines(table, [
      ...lines.slice(0, index + 1),
      cloned as SurveyLine,
      ...lines.slice(index + 1),
    ])
    setPendingOf(table, shiftPendingAfterInsert(pendingFiles[table], index))
  }

  function removeLine(table: SurveyTable, index: number) {
    setLines(
      table,
      linesOf(table).filter((_, i) => i !== index),
    )
    setPendingOf(table, shiftPendingAfterRemove(pendingFiles[table], index))
    setSelectedOf(table, shiftSelectionAfterRemove(selected[table], index))
    if (openLine?.table === table && openLine.index === index) setOpenLine(null)
  }

  function removeSelected(table: SurveyTable) {
    const drop = selected[table]
    if (!drop.size) return
    setLines(
      table,
      linesOf(table).filter((_, i) => !drop.has(i)),
    )
    // Xóa nhiều dòng cùng lúc thì chỉ số dịch loạn — dọn sạch giỏ tệp chờ của
    // bảng đó còn hơn gắn nhầm hình sang dòng khác.
    setPendingOf(table, {})
    setSelectedOf(table, new Set())
    if (openLine?.table === table) setOpenLine(null)
  }

  /**
   * Gắn tệp chờ vào dòng vừa lưu.
   *
   * `toPayloadLines` BỎ dòng rỗng nên chỉ số dòng ở màn hình không khớp mảng
   * server trả về — phải dò lại theo đúng thứ tự dòng có nội dung.
   */
  async function flushPendingFiles(saved: SurveyDetail) {
    for (const table of TABLES) {
      const buckets = Object.entries(pendingFiles[table])
      if (!buckets.length) continue

      const savedLines = table === 'supplier' ? saved.supplier_lines : saved.product_lines
      const byIndex = new Map<number, SurveyLine>()
      let cursor = 0
      linesOf(table).forEach((line, index) => {
        if (!lineHasContent(line, table)) return
        const savedLine = savedLines[cursor]
        cursor += 1
        if (savedLine) byIndex.set(index, savedLine)
      })

      for (const [key, files] of buckets) {
        const lineId = byIndex.get(Number(key))?.id ?? 0
        if (!lineId || !files.length) continue
        await purchaseRequestSupportApi.uploadAttachments(LINE_ATTACHMENT_ENTITY, lineId, files)
      }
    }
    setPendingFiles(EMPTY_PENDING)
  }

  async function handleSave(submitAfterSave = false) {
    if (submitAfterSave) {
      const check = validateSurveySubmit(
        loadedDraft,
        loadedDraft.supplier_lines,
        loadedDraft.product_lines,
      )
      if (check.message) {
        setInvalid(check.invalid)
        toast.error(check.message)
        return
      }
      setInvalid(new Set())
    }

    const saved = await saveSurvey.mutateAsync({
      id: isNew ? undefined : surveyId,
      payload: {
        pr_code: loadedDraft.pr_code,
        survey_request_id: loadedDraft.survey_request_id,
        sr_code: loadedDraft.sr_code,
        received_date: loadedDraft.received_date,
        result_due_date: loadedDraft.result_due_date,
        item_group: loadedDraft.item_group,
        main_content: loadedDraft.main_content,
        requirement_detail: loadedDraft.requirement_detail,
        request_qty: Number(loadedDraft.request_qty) || 0,
        nspt: loadedDraft.nspt,
        has_product_code: loadedDraft.has_product_code,
        item_code: loadedDraft.item_code,
        item_name: loadedDraft.item_name,
        uom: loadedDraft.uom,
        proposed_rate: Number(loadedDraft.proposed_rate) || 0,
        supplier_lines: toPayloadLines(loadedDraft.supplier_lines, 'supplier'),
        product_lines: toPayloadLines(loadedDraft.product_lines, 'product'),
      },
    })
    await flushPendingFiles(saved)

    if (submitAfterSave) {
      try {
        await runAction.mutateAsync({ action: 'submit' })
      } finally {
        // Phiếu đã tạo xong: luôn sang bản ghi thật để người dùng không bấm lại
        // và vô tình tạo trùng nếu bước gửi duyệt lỗi.
        if (isNew) navigate(appRoutes.procurement.surveyDetail(saved.id), { replace: true })
      }
      return
    }
    if (isNew) navigate(appRoutes.procurement.surveyDetail(saved.id), { replace: true })
  }

  /** TP/QL chốt duyệt cả hai bảng trong một lượt — chỉ gửi dòng đã có id. */
  async function handleSaveAllApprove() {
    await saveLineApprove.mutateAsync({
      supplierLines: approveItemsOf(loadedDraft.supplier_lines),
      productLines: approveItemsOf(loadedDraft.product_lines),
    })
    setOpenLine(null)
  }

  /** Bổ sung MỘT dòng khi phiếu đã gửi: chỉ đẩy ô nội dung, không đụng ô duyệt. */
  async function handleSaveFill() {
    if (!openLine) return
    const line = linesOf(openLine.table)[openLine.index]
    const lineId = typeof line?.id === 'number' ? line.id : 0
    if (!lineId) {
      toast.error('Dòng chưa được lưu nên chưa bổ sung được — lưu phiếu trước.')
      return
    }
    await fillLine.mutateAsync({
      table: openLine.table,
      lineId,
      changes: contentOnly(line, openLine.table),
    })
    setOpenLine(null)
  }

  const selectedLine = openLine ? (linesOf(openLine.table)[openLine.index] ?? null) : null
  const isSaving = saveSurvey.isPending || runAction.isPending
  const canSubmit = !isNew && editable && loadedDraft.id > 0

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách phiếu khảo sát">
          <Link to={appRoutes.procurement.surveys}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {isNew ? 'Tạo Phiếu khảo sát mới' : data.code || 'Phiếu nháp'}
        </h1>
        {!isNew && <StatusBadge status={status} labels={SURVEY_STATUS_LABELS} />}

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {editable && (
            <Button onClick={() => void handleSave()} disabled={isSaving}>
              {saveSurvey.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Lưu
            </Button>
          )}
          {canSubmit && (
            <Button variant="outline" onClick={() => void handleSave(true)} disabled={isSaving}>
              <Send />
              Gửi duyệt
            </Button>
          )}

          {liveApprove && (
            <Button
              variant="outline"
              title="Ghi lại toàn bộ ô duyệt của hai bảng"
              disabled={saveLineApprove.isPending}
              onClick={() => void handleSaveAllApprove()}
            >
              <CheckCheck />
              Lưu duyệt dòng
            </Button>
          )}

          {!isNew && status === 'submitted' && canApprove && (
            <>
              <Button
                onClick={() => void runAction.mutateAsync({ action: 'approve' })}
                disabled={runAction.isPending}
              >
                <Check />
                Duyệt
              </Button>
              <Button
                variant="outline"
                className="text-warning hover:text-warning"
                title="Trả về để người khảo sát sửa và gửi lại"
                onClick={() => {
                  setReason('')
                  setReasonFor('reject')
                }}
              >
                <CornerUpLeft />
                Trả về
              </Button>
              <Button
                variant="outline"
                className="text-destructive hover:text-destructive"
                title="Khóa phiếu hẳn — không sửa được, phải lập phiếu mới"
                onClick={() => {
                  setReason('')
                  setReasonFor('cancel')
                }}
              >
                <Ban />
                Từ chối
              </Button>
            </>
          )}

          {!isNew && isSurveyDeletable(status) && (
            <PermissionGate entity="survey" action="delete">
              <DeleteConfirmButton
                recordName={data.code || `#${data.id}`}
                pending={deleteSurvey.isPending}
                warning="Phiếu và toàn bộ dòng khảo sát NCC / sản phẩm kèm theo sẽ bị xóa."
                onConfirm={async () => {
                  await deleteSurvey.mutateAsync(data.id)
                  navigate(appRoutes.procurement.surveys)
                }}
              />
            </PermissionGate>
          )}
        </div>
      </div>

      {!isNew && !!data.approve_note && ['rejected', 'cancelled'].includes(status) && (
        <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <b>{status === 'cancelled' ? 'Lý do từ chối:' : 'Lý do trả lại:'}</b> {data.approve_note}
        </div>
      )}
      {!isNew && !!data.approve_note && !['rejected', 'cancelled'].includes(status) && (
        <div className="mb-4 rounded-lg border bg-muted/40 px-4 py-3 text-sm">
          <b>Ghi chú duyệt:</b> {data.approve_note}
        </div>
      )}

      <div className="min-w-0 space-y-4">
        <SurveyInfoCard
          data={loadedDraft}
          editable={editable}
          surveyRequests={surveyRequestsData?.items ?? []}
          itemGroups={itemGroupNames}
          units={unitNames}
          onChange={patch}
        />

        {TABLES.map((table) => (
          <Card key={table} className="min-w-0 gap-4 py-4">
            <CardHeader className="flex min-h-9 flex-row flex-wrap items-center justify-between gap-3 border-b px-4 pb-3!">
              <CardTitle className="text-base text-navy dark:text-foreground">
                {SURVEY_TABLE_LABELS[table]}
              </CardTitle>
            </CardHeader>
            <CardContent className="min-w-0 px-4">
              <SurveyLinesTable
                table={table}
                lines={linesOf(table)}
                editable={editable}
                approveEditable={canEditApprove}
                invalid={invalid}
                catalog={catalog}
                selected={selected[table]}
                canFill={canFill}
                actions={
                  editable && (
                    <>
                      {selected[table].size > 0 && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => removeSelected(table)}
                        >
                          <Trash2 />
                          Xóa dòng đã chọn ({selected[table].size})
                        </Button>
                      )}
                      <Button variant="outline" size="sm" onClick={() => addLines(table, 1)}>
                        <Plus />
                        Thêm dòng
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setBulkCount('3')
                          setBulkFor(table)
                        }}
                      >
                        <Rows3 />
                        Thêm nhiều
                      </Button>
                    </>
                  )
                }
                onSelectedChange={(next) => setSelectedOf(table, next)}
                onChangeLine={(index, changes) => changeLine(table, index, changes)}
                onOpenLine={(index, mode) => setOpenLine({ table, index, mode })}
                onDuplicate={(index) => duplicateLine(table, index)}
                onRemove={(index) => removeLine(table, index)}
              />
            </CardContent>
          </Card>
        ))}

        {!isNew && (
          <>
            <DocumentAttachmentsCard
              entity={HEAD_ATTACHMENT_ENTITY}
              entityId={surveyId}
              canManage={editable}
            />
            <DocumentComments entity={HEAD_ATTACHMENT_ENTITY} entityId={surveyId} />
            <AuditTimeline entity={HEAD_ATTACHMENT_ENTITY} entityId={surveyId} showMessage dense />
          </>
        )}
      </div>

      <SurveyLineDialog
        open={openLine !== null}
        table={openLine?.table ?? 'supplier'}
        line={selectedLine}
        lineNumber={(openLine?.index ?? 0) + 1}
        mode={openLine?.mode ?? 'edit'}
        editable={editable}
        approveEditable={canEditApprove}
        liveApprove={liveApprove}
        invalidKeys={invalidKeysOf(invalid, openLine)}
        catalog={catalog}
        pendingFiles={openLine ? (pendingFiles[openLine.table][openLine.index] ?? []) : []}
        isSaving={fillLine.isPending || saveLineApprove.isPending}
        onPendingFilesChange={(files) => {
          if (!openLine) return
          setPendingOf(openLine.table, {
            ...pendingFiles[openLine.table],
            [openLine.index]: files,
          })
        }}
        onOpenChange={(open) => {
          if (!open) setOpenLine(null)
        }}
        onChange={(changes) => {
          if (!openLine) return
          changeLine(openLine.table, openLine.index, changes)
        }}
        onSaveFill={() => void handleSaveFill()}
        onSaveApprove={() => void handleSaveAllApprove()}
      />

      <Dialog open={bulkFor !== null} onOpenChange={(open) => !open && setBulkFor(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Thêm nhiều dòng</DialogTitle>
            <DialogDescription>
              Dòng mới được điền sẵn ngày và thông tin hàng theo phần Thông tin tiếp nhận.
            </DialogDescription>
          </DialogHeader>
          <Input
            type="number"
            min={1}
            max={50}
            value={bulkCount}
            onChange={(event) => setBulkCount(event.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkFor(null)}>
              Đóng
            </Button>
            <Button
              onClick={() => {
                const count = Math.min(Math.max(Number(bulkCount) || 0, 0), 50)
                if (bulkFor && count > 0) addLines(bulkFor, count)
                setBulkFor(null)
              }}
            >
              Thêm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={reasonFor !== null} onOpenChange={(open) => !open && setReasonFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{reasonFor ? REASON_ACTIONS[reasonFor].title : ''}</DialogTitle>
            <DialogDescription>
              {reasonFor ? REASON_ACTIONS[reasonFor].description : ''}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            rows={4}
            value={reason}
            placeholder="Nhập lý do bắt buộc..."
            onChange={(event) => setReason(event.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setReasonFor(null)}>
              Đóng
            </Button>
            <Button
              variant={reasonFor === 'cancel' ? 'destructive' : 'default'}
              disabled={!reason.trim() || runAction.isPending}
              onClick={async () => {
                if (!reasonFor) return
                await runAction.mutateAsync({ action: reasonFor, reason: reason.trim() })
                setReasonFor(null)
              }}
            >
              {runAction.isPending && <Loader2 className="animate-spin" />}
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageContainer>
  )
}

/** Ô còn thiếu của RIÊNG dòng đang mở popup, đã cắt tiền tố `${table}-${index}-`. */
function invalidKeysOf(invalid: Set<string>, openLine: OpenLine | null): Set<string> {
  if (!openLine) return new Set()
  const prefix = `${openLine.table}-${openLine.index}-`
  const keys = new Set<string>()
  for (const key of invalid) {
    if (key.startsWith(prefix)) keys.add(key.slice(prefix.length))
  }
  return keys
}

/** Bỏ dòng thứ `removed` khỏi ô tick, mọi chỉ số lớn hơn lùi một bậc. */
function shiftSelectionAfterRemove(selected: Set<number>, removed: number): Set<number> {
  const next = new Set<number>()
  for (const index of selected) {
    if (index === removed) continue
    next.add(index > removed ? index - 1 : index)
  }
  return next
}

function toApproveItem(line: SurveyLine, lineId: number): SurveyLineApproveItem {
  return {
    id: lineId,
    line_approve: String(line.line_approve ?? ''),
    line_approve_note: String(line.line_approve_note ?? ''),
  }
}

function approveItemsOf(lines: SurveyLine[]): SurveyLineApproveItem[] {
  return lines
    .filter((line): line is SurveyLine & { id: number } => typeof line.id === 'number' && line.id > 0)
    .map((line) => toApproveItem(line, line.id))
}

/** Payload chỉ đụng vào một bảng — bảng kia gửi rỗng để backend không sửa gì. */
function approveOnlyPayload(table: SurveyTable, items: SurveyLineApproveItem[]) {
  return table === 'supplier'
    ? { supplierLines: items, productLines: [] }
    : { supplierLines: [], productLines: items }
}

/** Ô NỘI DUNG của dòng (bỏ hai ô duyệt) — dùng cho đường bổ sung dòng. */
function contentOnly(line: SurveyLine, table: SurveyTable): SurveyLine {
  const managerKeys = MANAGER_KEYS as readonly string[]
  const changes: SurveyLine = {}
  for (const section of sectionsOf(table)) {
    for (const field of section.fields) {
      if (managerKeys.includes(field.key)) continue
      changes[field.key] = line[field.key]
    }
  }
  return changes
}

function createEmptySurvey(
  user: AuthUser | null | undefined,
  srId: string | null,
  srCode: string | null,
): SurveyDetail {
  return {
    id: 0,
    code: '',
    survey_type: '',
    pr_code: '',
    // Mở từ nút "Tạo phiếu khảo sát" trên YCBG thì liên kết sẵn về phiếu nguồn.
    survey_request_id: Number(srId) || 0,
    sr_code: srCode ?? '',
    received_date: new Date().toISOString().slice(0, 10),
    result_due_date: '',
    item_group: '',
    main_content: '',
    requirement_detail: '',
    request_qty: 0,
    // NSPT phụ trách mặc định là người đang lập phiếu; backend chốt lại lúc lưu.
    nspt: user?.full_name ?? '',
    has_product_code: false,
    item_code: '',
    item_name: '',
    uom: '',
    proposed_rate: 0,
    // Phiếu mới chưa ai xét duyệt — `pending` là MÃ cho tình trạng đó (B-04), không phải rỗng.
    approve_status: 'pending',
    approve_status_label: labelOf(SURVEY_APPROVE_STATUS, 'pending'),
    approve_note: '',
    status: 'draft',
    created_at: new Date().toISOString(),
    created_by: user?.id ?? 0,
    supplier_lines: [],
    product_lines: [],
    supplier_count: 0,
    product_count: 0,
    subtotal: 0,
    main: '',
  }
}
