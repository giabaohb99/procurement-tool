import {
  ArrowLeft,
  Ban,
  Check,
  CheckCheck,
  ClipboardCheck,
  CornerUpLeft,
  FileCheck,
  FilePlus,
  Loader2,
  Plus,
  Save,
  Send,
} from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import type { AuthUser } from '@/core/auth/auth-types'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
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
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { purchaseRequestSupportApi } from '../api/purchase-request-support-api'
import { surveyRequestApi } from '../api/survey-request-api'
import { StatusBadge } from '../components/document-status-badge'
import { DocumentComments } from '../components/document-comments'
import { SurveyRequestInfoCard } from '../components/survey-request-info-card'
import { SurveyRequestLineDialog } from '../components/survey-request-line-dialog'
import {
  EMPTY_SURVEY_REQUEST_LINE,
  SurveyRequestLinesTable,
} from '../components/survey-request-lines-table'
import { SurveyRequestResultCard } from '../components/survey-request-result-card'
import {
  shiftPendingAfterInsert,
  shiftPendingAfterRemove,
  type PendingLineFiles,
} from '../helpers/pending-line-files'
import {
  useAssignSurveyLine,
  useChooseSurveyOption,
  useCreatePurchaseRequestsFromSurvey,
  useDeleteSurveyRequest,
  useSaveSurveyRequest,
  useSetSurveyLineStatus,
  useSurveyRequest,
  useSurveyRequestAction,
  useSurveyRequestResult,
} from '../hooks/use-survey-request'
import { SR_STATUS_LABELS } from '../types/purchase-document'
import {
  LINE_STATUS_RESURVEY,
  hasSurveyResult,
  isSurveyRequestEditable,
  isSurveyRequestLocked,
  type SurveyRequestDetail,
  type SurveyRequestLine,
} from '../types/survey-request-detail'
import { parseAssistantDraft, type AssistantDraft } from '../utils/assistant-draft'
import { validateSurveyRequest } from '../utils/required-fields'

/** Tệp đính kèm của DÒNG khảo sát — đầu phiếu YCBG không có khu đính kèm riêng. */
const LINE_ATTACHMENT_ENTITY = 'survey_request_line'

/** Từ trạng thái này trở đi mới bấm "Tạo yêu cầu mua" được. */
const CREATE_PR_STATUSES = ['processing', 'survey_done', 'pr_created', 'done']

type ReasonAction = 'reject' | 'cancel'
type ConfirmAction = 'createPrs' | 'finalize'

const REASON_ACTIONS: Record<ReasonAction, { title: string; description: string }> = {
  reject: {
    title: 'Trả về cho người yêu cầu',
    description: 'Phiếu chuyển sang Bị trả lại để người yêu cầu sửa rồi gửi duyệt lại.',
  },
  cancel: {
    title: 'Từ chối phiếu',
    description: 'Phiếu bị khóa hẳn, không sửa lại được — muốn làm tiếp phải lập phiếu mới.',
  },
}

const CONFIRM_ACTIONS: Record<ConfirmAction, { title: string; description: string }> = {
  createPrs: {
    title: 'Tạo Yêu cầu mua hàng?',
    description:
      'Sinh YCMH từ các phương án đã chọn, gom theo nhà cung cấp. Dòng chưa chọn phương án sẽ bỏ qua.',
  },
  finalize: {
    title: 'Chuyển phiếu sang Hoàn thành?',
    description: 'Sau khi hoàn thành, phiếu không chỉnh sửa được nữa.',
  },
}

/**
 * Chi tiết phiếu YÊU CẦU BÁO GIÁ (YCBG).
 *
 * Ba khung nhìn chồng lên nhau trên cùng một trang:
 * - NGƯỜI YÊU CẦU soạn dòng cần khảo sát, rồi chọn phương án ở khu Kết quả;
 * - NGƯỜI DUYỆT bấm Duyệt / Trả về / Từ chối;
 * - THU MUA (quyền `process`) thấy thêm cột Ngày tiếp nhận + NSTM phụ trách.
 *
 * Trang KHÔNG có nút "Sửa": phiếu nháp/bị trả lại là sửa được ngay, phiếu đã gửi
 * duyệt thì khóa — giữ đúng thói quen của bản cũ.
 */
export function SurveyRequestDetailPage() {
  const { id } = useParams()
  // Route tạo mới là route tĩnh `/new` nên `useParams()` trả `undefined`; vẫn nhận
  // cả chuỗi 'new' để trang an toàn nếu sau này hai route được gộp.
  const isNew = !id || id === 'new'
  const surveyRequestId = isNew ? 0 : Number(id)
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()
  const { can } = usePermission()

  // Bản nháp do Trợ lý AI soạn, truyền qua `location.state` khi bấm nút trong chat.
  // Chỉ ĐIỀN SẴN form — người dùng rà lại rồi tự bấm Tạo, phiếu không tự sinh ra.
  const assistantDraft = isNew
    ? parseAssistantDraft((location.state as { assistantDraft?: unknown } | null)?.assistantDraft)
    : null

  const { data: serverData, isLoading, isError } = useSurveyRequest(surveyRequestId)
  const { data: result } = useSurveyRequestResult(surveyRequestId, serverData?.status ?? '')
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })
  const { data: employeesData } = useEmployees({ page_size: 1000, is_active: true })
  const { data: departmentsData } = useDepartments({ page_size: 500 })

  const saveSurveyRequest = useSaveSurveyRequest()
  const runAction = useSurveyRequestAction(surveyRequestId)
  const deleteSurveyRequest = useDeleteSurveyRequest()
  const assignLine = useAssignSurveyLine(surveyRequestId)
  const setLineStatus = useSetSurveyLineStatus(surveyRequestId)
  const chooseOption = useChooseSurveyOption(surveyRequestId)
  const createPurchaseRequests = useCreatePurchaseRequestsFromSurvey(surveyRequestId)

  const [draft, setDraft] = useState<SurveyRequestDetail | null>(() =>
    isNew ? applyAssistantDraft(createEmptySurveyRequest(user), assistantDraft) : null,
  )
  const [lineIndex, setLineIndex] = useState<number | null>(null)
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [reason, setReason] = useState('')
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null)
  const [resurveyLineId, setResurveyLineId] = useState<number | null>(null)
  const [showCreatedPrs, setShowCreatedPrs] = useState(false)
  /** Hình chọn cho dòng CHƯA lưu — xem `helpers/pending-line-files.ts`. */
  const [pendingFiles, setPendingFiles] = useState<PendingLineFiles>({})

  // Tạo mới -> dựng phiếu rỗng; xem phiếu có sẵn -> nạp dữ liệu server.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook sau không chạy.
  const isNewChanged = useHasChanged(isNew)
  const serverDataChanged = useHasChanged(serverData)
  const userChanged = useHasChanged(user)
  if (isNewChanged || serverDataChanged || userChanged) {
    setDraft(
      isNew
        ? (current) => current ?? applyAssistantDraft(createEmptySurveyRequest(user), assistantDraft)
        : (serverData ?? null),
    )
  }

  // Hồ sơ nhân sự tải sau, mà chỉ ở đó mới có `department_id` (CR-086) — bù thêm
  // một nhịp cho phiếu mới, để phiếu neo phòng bằng id chứ không bằng tên.
  const employeesChanged = useHasChanged(employeesData)
  if (isNew && employeesChanged && draft?.requester_id && !draft.department_id) {
    const me = (employeesData?.items ?? []).find((employee) => employee.id === draft.requester_id)
    if (me?.department_id) {
      const departmentId = me.department_id
      const departmentName = me.department_name || ''
      setDraft((current) =>
        current ? { ...current, department_id: departmentId, department: departmentName } : current,
      )
    }
  }

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
        title="Không mở được phiếu"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.surveyRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  // Biến ổn định để các callback bên dưới giữ được kiểu non-null sau nhánh lỗi.
  const data = serverData ?? draft ?? createEmptySurveyRequest(user)
  const loadedDraft = draft ?? data
  const status = data.status

  /**
   * Người YC = người TẠO phiếu, hoặc người được ghi là "người yêu cầu" trên phiếu.
   * Hai nguồn khác nhau: `created_by` là id TÀI KHOẢN, `requester_id` là id NHÂN SỰ.
   */
  const isRequester =
    (!!data.created_by && data.created_by === user?.id) ||
    (!!data.requester_id && data.requester_id === user?.employee_id)
  /** Người thường (không duyệt, không xóa) — không xem được danh mục Nhân sự. */
  const isStaff = !can('survey_request', 'approve') && !can('survey_request', 'delete')
  const editable =
    (isNew || isSurveyRequestEditable(status)) &&
    (isNew || can('survey_request', 'write') || isRequester)

  const canViewNstm = can('survey_request', 'process')
  const locked = isSurveyRequestLocked(status)
  const canAssignNstm = canViewNstm && !locked
  const showNstmColumns = canViewNstm && !isNew
  const showStatus = !isNew

  const canFinalize =
    (can('survey_request', 'process') && can('survey_request', 'approve')) ||
    isRequester ||
    can('survey_request', 'delete')
  const canCreatePr = isRequester || can('survey_request', 'delete')
  const canSetLineStatus =
    canCreatePr && ['processing', 'survey_done', 'pr_created'].includes(status)
  const canChooseOption = CREATE_PR_STATUSES.includes(status) && canCreatePr

  const resultLines = result?.lines ?? []
  const anyChosen = resultLines.some((line) => (line.options ?? []).some((o) => o.is_chosen))
  const hasAnyOptions = resultLines.some((line) => (line.options ?? []).length > 0)
  // Phiếu vừa chuyển sang "Đang xử lý" thì khu Kết quả còn rỗng — chờ có phương
  // án đầu tiên mới hiện, khỏi để người dùng nhìn một cái thẻ trắng.
  const showResult =
    !isNew && !!result && hasSurveyResult(status) && (status !== 'processing' || hasAnyOptions)

  /**
   * NSTM chọn được: nhân sự phòng thu mua. Ô hiện TÊN nhưng lưu MÃ nhân sự.
   * Bổ sung người đã gán ở từng dòng dù họ nằm ngoài phạm vi danh mục tải về —
   * không thì bảng hiện mã trần thay vì tên.
   */
  const purchasers = (() => {
    const options = (employeesData?.items ?? [])
      .filter((employee) => (employee.department_name || '').toLowerCase().includes('thu mua'))
      .map((employee) => ({ code: employee.code, name: employee.full_name }))
    for (const line of data.lines) {
      if (line.assignee && !options.some((option) => option.code === line.assignee)) {
        options.push({ code: line.assignee, name: line.assignee_name || line.assignee })
      }
    }
    return options
  })()

  /** YCMH đã sinh — gom từ `ycmh_list` của mọi phương án, khử trùng theo id phiếu. */
  const createdPrs = (() => {
    const byId = new Map<number, { code: string; date: string; status: string; items: string[] }>()
    resultLines.forEach((line, index) => {
      for (const option of line.options ?? []) {
        for (const pr of option.ycmh_list ?? []) {
          const entry = byId.get(pr.id) ?? {
            code: pr.code,
            date: pr.date,
            status: pr.status,
            items: [],
          }
          const label = `SP ${index + 1} (${option.display_label || `Option ${option.public_id}`})`
          if (!entry.items.includes(label)) entry.items.push(label)
          byId.set(pr.id, entry)
        }
      }
    })
    return Array.from(byId.entries()).map(([prId, entry]) => ({ prId, ...entry }))
  })()

  const selectedLine = lineIndex === null ? null : (loadedDraft.lines[lineIndex] ?? null)

  function patch(changes: Partial<SurveyRequestDetail>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  /** Đẩy hình chờ lên đúng dòng vừa được server trả về (khớp theo thứ tự dòng). */
  async function flushPendingFiles(savedLines: SurveyRequestLine[]) {
    const buckets = Object.entries(pendingFiles)
    if (!buckets.length) return
    for (const [key, files] of buckets) {
      const lineId = savedLines[Number(key)]?.id ?? 0
      if (!lineId || !files.length) continue
      await purchaseRequestSupportApi.uploadAttachments(LINE_ATTACHMENT_ENTITY, lineId, files)
    }
    setPendingFiles({})
  }

  async function handleSave(submitAfterSave = false) {
    const message = validateSurveyRequest(loadedDraft, submitAfterSave)
    if (message) {
      toast.error(message)
      return
    }
    const saved = await saveSurveyRequest.mutateAsync({
      id: isNew ? undefined : surveyRequestId,
      payload: {
        company_id: loadedDraft.company_id,
        requester: loadedDraft.requester,
        requester_id: loadedDraft.requester_id,
        requester_position: loadedDraft.requester_position,
        department_id: loadedDraft.department_id,
        department: loadedDraft.department,
        head_of_dept_id: loadedDraft.head_of_dept_id,
        head_of_dept: loadedDraft.head_of_dept,
        purpose: loadedDraft.purpose,
        request_date: loadedDraft.request_date,
        note: loadedDraft.note,
        lines: loadedDraft.lines,
      },
    })
    await flushPendingFiles(saved.lines ?? [])
    if (submitAfterSave) {
      try {
        await surveyRequestApi.submit(saved.id)
        toast.success('Đã gửi duyệt')
      } finally {
        // Phiếu đã tạo xong: luôn sang bản ghi thật để người dùng không bấm lại
        // và vô tình tạo trùng nếu bước gửi duyệt lỗi.
        if (isNew) navigate(appRoutes.procurement.surveyRequestDetail(saved.id), { replace: true })
      }
      return
    }
    if (isNew) navigate(appRoutes.procurement.surveyRequestDetail(saved.id), { replace: true })
  }

  /** Đổi NSTM ngay trên bảng / trong popup — ghi thẳng xuống server, không chờ nút Lưu. */
  function handleAssigneeChange(line: SurveyRequestLine, assignee: string) {
    if (!line.id) return
    void assignLine.mutateAsync({ lineId: line.id, assignee })
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách yêu cầu báo giá">
          <Link to={appRoutes.procurement.surveyRequests}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {isNew ? 'Tạo Yêu cầu báo giá mới' : data.code || 'Phiếu nháp'}
        </h1>
        {!isNew && <StatusBadge status={status} labels={SR_STATUS_LABELS} />}

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {editable && (
            <>
              <Button onClick={() => void handleSave()} disabled={saveSurveyRequest.isPending}>
                {saveSurveyRequest.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                Lưu
              </Button>
              <Button
                variant="outline"
                onClick={() => void handleSave(true)}
                disabled={saveSurveyRequest.isPending}
              >
                <Send />
                Gửi duyệt
              </Button>
            </>
          )}

          {!isNew && status === 'submitted' && can('survey_request', 'approve') && (
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
                title="Trả về để người yêu cầu sửa và gửi lại"
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

          {/*
            Còn thiếu so với bản cũ: "Xử lý khảo sát" — màn đó chưa dựng ở v2 nên
            nút sẽ dẫn vào trang trống. Gắn lại ngay khi `survey-request-process-page` lên.
          */}

          {/* Chỉ nhân sự thu mua, và chỉ khi phiếu ĐANG XỬ LÝ — đúng lúc đó mới
              biết cần khảo sát cái gì. Mã YCBG đưa sang theo URL để phiếu khảo sát
              mới neo sẵn về phiếu nguồn. */}
          {!isNew && status === 'processing' && can('survey_request', 'process') && (
            <PermissionGate entity="survey" action="create">
              <Button
                variant="outline"
                onClick={() =>
                  navigate(
                    `${appRoutes.procurement.surveyNew}?sr=${data.id}&sr_code=${encodeURIComponent(data.code)}`,
                  )
                }
              >
                <ClipboardCheck />
                Tạo phiếu khảo sát
              </Button>
            </PermissionGate>
          )}

          {!isNew && CREATE_PR_STATUSES.includes(status) && canCreatePr && (
            <Button
              disabled={!anyChosen || createPurchaseRequests.isPending}
              title={anyChosen ? '' : 'Chọn ít nhất 1 phương án ở phần Kết quả khảo sát'}
              onClick={() => setConfirmAction('createPrs')}
            >
              <FilePlus />
              Tạo yêu cầu mua
            </Button>
          )}

          {!isNew && ['survey_done', 'pr_created'].includes(status) && canFinalize && (
            <Button variant="outline" onClick={() => setConfirmAction('finalize')}>
              <CheckCheck />
              Chuyển Hoàn thành
            </Button>
          )}

          {createdPrs.length > 0 && (
            <Button
              variant="outline"
              className="text-success hover:text-success"
              onClick={() => setShowCreatedPrs(true)}
            >
              <FileCheck />
              Đã tạo {createdPrs.length} phiếu YCMH
            </Button>
          )}

          {!isNew && ['draft', 'rejected', 'cancelled'].includes(status) && (
            <PermissionGate entity="survey_request" action="delete">
              <DeleteConfirmButton
                recordName={data.code || `#${data.id}`}
                pending={deleteSurveyRequest.isPending}
                warning="Phiếu và các dòng cần khảo sát kèm theo sẽ bị xóa."
                onConfirm={async () => {
                  await deleteSurveyRequest.mutateAsync(data.id)
                  navigate(appRoutes.procurement.surveyRequests)
                }}
              />
            </PermissionGate>
          )}
        </div>
      </div>

      {!isNew && !!data.reject_reason && ['rejected', 'cancelled'].includes(status) && (
        <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <b>{status === 'cancelled' ? 'Lý do từ chối:' : 'Lý do trả đơn:'}</b> {data.reject_reason}
        </div>
      )}

      <div className="min-w-0 space-y-4">
        <SurveyRequestInfoCard
          data={loadedDraft}
          editing={editable}
          isNew={isNew}
          companies={companiesData?.items}
          employees={employeesData?.items}
          departments={departmentsData?.items}
          lockRequester={isStaff}
          onChange={patch}
        />

        <Card className="gap-4 py-4">
          <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">
              Danh sách Sản phẩm cần Khảo sát
            </CardTitle>
            {editable ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  patch({ lines: [...loadedDraft.lines, { ...EMPTY_SURVEY_REQUEST_LINE }] })
                }
              >
                <Plus />
                Thêm dòng
              </Button>
            ) : (
              showNstmColumns && (
                <span className="text-xs text-muted-foreground">
                  Thay đổi nhân sự phụ trách được lưu ngay, không cần bấm Lưu.
                </span>
              )
            )}
          </CardHeader>
          <CardContent className="px-4">
            <SurveyRequestLinesTable
              lines={loadedDraft.lines}
              editing={editable}
              showNstmColumns={showNstmColumns}
              showStatus={showStatus}
              canAssignNstm={canAssignNstm}
              purchasers={purchasers}
              onChange={(lines) => patch({ lines })}
              onOpenDetail={setLineIndex}
              onAssigneeChange={handleAssigneeChange}
              onLineRemoved={(index) =>
                setPendingFiles((current) => shiftPendingAfterRemove(current, index))
              }
              onLineDuplicated={(index) =>
                setPendingFiles((current) => shiftPendingAfterInsert(current, index))
              }
            />
          </CardContent>
        </Card>

        {showResult && result && (
          <SurveyRequestResultCard
            result={result}
            canChoose={canChooseOption}
            canSetLineStatus={canSetLineStatus}
            showCreatePrHint={canCreatePr && !anyChosen}
            showWaitFinalizeHint={status === 'pr_created' && !canFinalize}
            onChooseOption={(lineId, optionId) =>
              void chooseOption.mutateAsync({ lineId, optionId })
            }
            onRequestResurvey={setResurveyLineId}
          />
        )}

        {!isNew && (
          <>
            <DocumentComments entity="survey_request" entityId={surveyRequestId} />
            <AuditTimeline entity="survey_request" entityId={surveyRequestId} showMessage dense />
          </>
        )}
      </div>

      <SurveyRequestLineDialog
        line={selectedLine}
        lineNumber={(lineIndex ?? 0) + 1}
        open={lineIndex !== null}
        editing={editable}
        showNstmFields={showNstmColumns}
        showStatus={showStatus}
        canAssignNstm={canAssignNstm}
        purchasers={purchasers}
        pendingFiles={lineIndex === null ? [] : (pendingFiles[lineIndex] ?? [])}
        onPendingFilesChange={(files) => {
          if (lineIndex === null) return
          setPendingFiles((current) => ({ ...current, [lineIndex]: files }))
        }}
        onOpenChange={(open) => {
          if (!open) setLineIndex(null)
        }}
        onChange={(line) => {
          if (lineIndex === null) return
          patch({
            lines: loadedDraft.lines.map((current, index) => (index === lineIndex ? line : current)),
          })
        }}
        onAssigneeChange={handleAssigneeChange}
      />

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

      <AlertDialog
        open={confirmAction !== null}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirmAction ? CONFIRM_ACTIONS[confirmAction].title : ''}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmAction ? CONFIRM_ACTIONS[confirmAction].description : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (confirmAction === 'createPrs') void createPurchaseRequests.mutateAsync()
                if (confirmAction === 'finalize') void runAction.mutateAsync({ action: 'finalize' })
                setConfirmAction(null)
              }}
            >
              Đồng ý
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={resurveyLineId !== null}
        onOpenChange={(open) => !open && setResurveyLineId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cần khảo sát lại</AlertDialogTitle>
            <AlertDialogDescription>
              {resultLines
                .find((line) => line.id === resurveyLineId)
                ?.options?.some((option) => option.is_chosen)
                ? 'Dòng này đang chọn 1 phương án. Đánh dấu "Cần khảo sát lại" sẽ BỎ CHỌN phương án đó và chờ NSTM khảo sát lại.'
                : 'Đánh dấu dòng này "Cần khảo sát lại"? NSTM sẽ khảo sát lại phương án cho sản phẩm này.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (resurveyLineId !== null) {
                  void setLineStatus.mutateAsync({
                    lineId: resurveyLineId,
                    lineStatus: LINE_STATUS_RESURVEY,
                  })
                }
                setResurveyLineId(null)
              }}
            >
              Cần khảo sát lại
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={showCreatedPrs} onOpenChange={setShowCreatedPrs}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Đã tạo {createdPrs.length} phiếu yêu cầu mua hàng</DialogTitle>
            <DialogDescription>Bấm mã phiếu để mở chi tiết.</DialogDescription>
          </DialogHeader>
          <ul className="max-h-[55dvh] space-y-2 overflow-y-auto">
            {createdPrs.map((pr) => (
              <li key={pr.prId} className="rounded-lg border p-3">
                <Link
                  className="font-semibold text-primary hover:underline"
                  to={appRoutes.procurement.purchaseRequestDetail(pr.prId)}
                >
                  {pr.code}
                </Link>
                <span className="ml-2 text-xs text-muted-foreground">
                  {formatDate(pr.date)}
                  {pr.status ? ` · ${pr.status}` : ''}
                </span>
                <p className="mt-1 text-xs text-muted-foreground">Bao gồm: {pr.items.join(', ')}</p>
              </li>
            ))}
          </ul>
        </DialogContent>
      </Dialog>
    </PageContainer>
  )
}

/** Trả về chuỗi lỗi đầu tiên gặp phải, rỗng nghĩa là hợp lệ. */
function createEmptySurveyRequest(user?: AuthUser | null): SurveyRequestDetail {
  return {
    id: 0,
    code: '',
    company_id: user?.company_id ?? 0,
    requester: user?.full_name ?? '',
    requester_id: user?.employee_id ?? 0,
    requester_position: user?.position ?? '',
    // Tên phòng lấy tạm từ tài khoản; id được bù khi danh mục Nhân sự tải xong,
    // và backend cũng tự tra lại theo tên nếu id vẫn rỗng lúc lưu (CR-086).
    department_id: 0,
    department: user?.department_name ?? '',
    // Trưởng bộ phận do backend điền theo `Department.manager_id` lúc lưu.
    head_of_dept_id: 0,
    head_of_dept: '',
    purpose: '',
    request_date: new Date().toISOString().slice(0, 10),
    status: 'draft',
    note: '',
    reject_reason: '',
    created_at: new Date().toISOString(),
    created_by: user?.id ?? 0,
    lines: [],
  }
}

/**
 * Điền bản nháp của Trợ lý AI lên phiếu rỗng: mục đích, ghi chú và các dòng hàng.
 * Dòng dựng từ `EMPTY_SURVEY_REQUEST_LINE` để đủ mọi trường phụ (mốc thu mua, trạng thái...).
 */
function applyAssistantDraft(
  base: SurveyRequestDetail,
  draft: AssistantDraft | null,
): SurveyRequestDetail {
  if (!draft) return base
  return {
    ...base,
    purpose: draft.purpose,
    note: draft.note,
    // Người dùng nói mua cho pháp nhân khác thì trợ lý đã khớp danh mục -> đè công ty
    // mặc định (công ty của người hỏi); không nói thì giữ nguyên.
    company_id: draft.company_id > 0 ? draft.company_id : base.company_id,
    lines: draft.lines.map((line) => ({ ...EMPTY_SURVEY_REQUEST_LINE, ...line })),
  }
}
