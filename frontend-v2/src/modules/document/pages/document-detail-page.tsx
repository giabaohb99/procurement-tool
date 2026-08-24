import { zodResolver } from '@hookform/resolvers/zod'
import {
  Ban,
  Check,
  ChevronDown,
  FileDown,
  FileText,
  GitBranch,
  Info,
  Link2,
  Loader2,
  PanelTop,
  Pencil,
  Printer,
  Save,
  Scissors,
  ShieldCheck,
  Send,
  Undo2,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useEntityApproval } from '@/modules/approval/hooks/use-approvals'
import { INSTANCE_STATUS } from '@/modules/approval/types/approval'
import { downloadFile } from '@/core/api'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { mmToPx, RichTextEditor, type RichTextEditorHandle } from '@/shared/ui/rich-text-editor'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentAmendedBanner } from '../components/document-amended-banner'
import { DocumentApprovalBanner } from '../components/document-approval-banner'
import { DocumentApprovalTab } from '../components/document-approval-tab'
import { DocumentAccessCard } from '../components/document-access-card'
import { DocumentScopeCard } from '../components/document-scope-card'
import { DocumentSignatureCard } from '../components/document-signature-card'
import { DocumentAttachmentList } from '../components/document-attachment-list'
import { DocumentAutosaveStatus } from '../components/document-autosave-status'
import { DocumentCopyAction } from '../components/document-copy-action'
import { DocumentRecordForm } from '../components/document-record-form'
import { DocumentVersionBanner } from '../components/document-version-banner'
import { DocumentVersionTab } from '../components/document-version-tab'
import { DocumentLinkTab } from '../components/document-link-tab'
import { DocumentExcerptDialog } from '../components/document-excerpt-dialog'
import { DocumentImportButton } from '../components/document-import-button'
import { DocumentIssueDialog } from '../components/document-issue-dialog'
import { DocumentNeedsReviewBanner } from '../components/document-needs-review-banner'
import { DocumentReviewDialog } from '../components/document-review-dialog'
import { DocumentPageFrameDialog } from '../components/document-page-frame-dialog'
import { DocumentSubmittedLockNotice } from '../components/document-submitted-lock-notice'
import { useCreateExcerpt } from '../hooks/use-document-links'
import { ManualIssueNumberDialog } from '../components/manual-issue-number-dialog'
import { documentToForm, emptyDocumentForm, formToPayload } from '../helpers/document-form-defaults'
import { effectiveLabel } from '../helpers/document-status'
import { fillPageMarkers } from '../helpers/page-marker'
import { useDocumentPermissions } from '../hooks/use-document-access'
import { useDocumentAutosave } from '../hooks/use-document-autosave'
import { useDocumentPageMargins } from '../hooks/use-document-page-margins'
import {
  useDocumentVersion,
  useDocumentVersions,
  useSaveVersionAutoNumber,
  useSaveVersionContent,
  useSaveVersionPageFrame,
} from '../hooks/use-document-versions'
import {
  useDeleteDocument,
  useDocument,
  useDocumentWorkflow,
  useSaveDocument,
  useUpdateDocumentIssueNumber,
} from '../hooks/use-documents'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'
import { DOCUMENT_STATUS, VERSION_STATUS } from '../types/document-record'

const FORM_ID = 'document-record-form'

/**
 * Trang CHI TIẾT một văn bản, ba tab:
 *  - **Soạn thảo** — trang giấy trắng kiểu Word, tự động lưu trong lúc gõ;
 *  - **Thông tin** — bộ trường chung C01, tệp đính kèm, bảng quyền truy cập;
 *  - **Phiên bản** — danh sách các bản, mở bản mới, xem lại bản cũ.
 *
 * Mặc định mở bản ĐANG SỬA ĐƯỢC nếu có (bản nháp), không thì bản đang dùng —
 * người vào trang gần như luôn muốn một trong hai.
 */
export function DocumentDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const readonlyFromLink = searchParams.get('readonly') === '1'
  const [tab, setTab] = useUrlParamState('tab', 'compose')
  const editorRef = useRef<RichTextEditorHandle>(null)

  const documentId = Number(id)
  //  Đọc phiên duyệt TRƯỚC để biết văn bản có đang chạy trong bộ máy không —
  //  chỉ lúc đó mới cần hỏi lại bản ghi theo nhịp (xem `useDocument`).
  const { data: approvalData } = useEntityApproval('document', documentId)
  const approval = approvalData ?? null
  const dangDuyetNhieuBuoc =
    approval?.status === INSTANCE_STATUS.running || approval?.status === INSTANCE_STATUS.blocked

  const {
    data: record,
    isLoading,
    isError: mucKhongDocDuoc,
  } = useDocument(documentId, { dangDuyet: dangDuyetNhieuBuoc })
  const { data: versions = [] } = useDocumentVersions(documentId)
  const { data: permissions } = useDocumentPermissions(documentId)

  // Bản người dùng tự chọn; `null` = để hệ chọn. TÍNH RA `versionId` chứ không
  // đồng bộ bằng effect: mở bản mới xong danh sách đổi, effect sẽ chạy lại và
  // kéo màn hình về bản khác ngay dưới tay người đang xem.
  const [pickedVersionId, setPickedVersionId] = useState<number | null>(null)
  //  Hộp hỏi lý do đang mở cho việc gì (`null` = đang đóng). Hai việc dùng
  //  chung một hộp vì chỉ khác chữ.
  const [reasonFor, setReasonFor] = useState<'revoke' | 'reject' | null>(null)
  //  Rà lại KHÔNG dùng chung hộp hỏi lý do: nó còn phải hỏi kết luận rà ra là
  //  giữ nguyên hay phải sửa, và ở vế "phải sửa" thì mở luôn phiên bản mới.
  const [reviewOpen, setReviewOpen] = useState(false)
  const [numberDialogOpen, setNumberDialogOpen] = useState(false)
  const autoVersion =
    versions.find((item) => !item.is_locked) ??
    versions.find((item) => item.is_current) ??
    versions[0]
  const versionId =
    pickedVersionId && versions.some((item) => item.id === pickedVersionId)
      ? pickedVersionId
      : (autoVersion?.id ?? null)

  const { data: version } = useDocumentVersion(documentId, versionId)

  const save = useSaveDocument()
  const remove = useDeleteDocument()
  const workflow = useDocumentWorkflow(documentId)
  const updateIssueNumber = useUpdateDocumentIssueNumber(documentId)
  const saveContent = useSaveVersionContent(documentId, versionId)
  const createExcerpt = useCreateExcerpt(documentId)
  const [excerptOpen, setExcerptOpen] = useState(false)
  const [issueOpen, setIssueOpen] = useState(false)

  //  ⚠️ `dangDuyetNhieuBuoc` khai ở ĐẦU hàm (cạnh `useEntityApproval`) vì
  //  `useDocument` cần nó để bật nhịp hỏi lại. Đang chạy nhiều bước thì hai nút
  //  của luồng MỘT BƯỚC cũ phải biến mất: lỗi đã xảy ra là văn bản nằm ở chặng 1
  //  chờ trưởng bộ phận, người có quyền `document.approve` bấm «Duyệt và ban
  //  hành» là văn bản được cấp số và chuyển hiệu lực ngay, còn phiên duyệt vẫn
  //  chạy tiếp trên một văn bản đã ban hành. Backend nay cũng chặn
  //  (`approval_bridge.chan_duong_cu`) — ẩn nút ở đây là để người dùng không
  //  thấy một cái nút chỉ để nhận lỗi.

  //  MẤT QUYỀN GIỮA CHỪNG thì đá ra, đừng để họ ngồi lại (CR-114).
  //
  //  Ca thật: văn bản đang chờ A duyệt, người quản trị đổi người duyệt của bước
  //  đó sang B. A không còn việc nào ở phiếu này, mà khe đọc của A vốn mở ra
  //  CHÍNH VÌ việc đó (xem `doc_reader` ở backend) — nên từ nhịp hỏi lại kế
  //  tiếp, API trả 404. Không xử ở đây thì A ngồi trong một trang đã chết, với
  //  nút «Duyệt» sáng trưng, bấm vào chỉ nhận lỗi.
  useEffect(() => {
    if (!mucKhongDocDuoc) return
    //  Hai nguyên nhân, nói cả hai: văn bản vừa bị BÃI BỎ (bãi bỏ thu hồi luôn
    //  quyền xem — `revoke_access.py`), hoặc việc duyệt đã chuyển người. Câu cũ
    //  chỉ nói vế thứ hai nên người bị đá ra vì bãi bỏ đọc xong càng khó hiểu.
    toast.error(
      'Bạn không còn quyền xem văn bản này — văn bản có thể vừa bị bãi bỏ, hoặc việc duyệt đã chuyển sang người khác.',
    )
    navigate(appRoutes.document.documentsTab('outgoing'), { replace: true })
  }, [mucKhongDocDuoc, navigate])

  const { can } = usePermission()
  //  Ký là hành vi PHÊ DUYỆT, không phải sửa nội dung — gác bằng `approve` đúng
  //  như backend làm.
  const canApprove = !readonlyFromLink && can('document', 'approve')
  const canCreate = !readonlyFromLink && can('document', 'create')
  const canWrite = !readonlyFromLink && (permissions?.write ?? false)
  const canDelete = !readonlyFromLink && (permissions?.delete ?? false)

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: emptyDocumentForm(),
  })

  // Nạp bản ghi vào form một lần khi có dữ liệu. `reset` chứ không phải
  // `defaultValues`: query trả về sau lần render đầu.
  useEffect(() => {
    if (record) form.reset(documentToForm(record))
  }, [record, form])

  const handleSaveContent = useCallback(
    async (content: string, options: { silent: boolean }) => {
      await saveContent.mutateAsync({ content_html: content })
      if (!options.silent) toast.success('Đã lưu nội dung văn bản')
    },
    [saveContent],
  )

  const autosave = useDocumentAutosave({ onSave: handleSaveContent })
  //  Buông tay khỏi thước lề → ghi ngay xuống phiên bản (xem hook).
  const pageMargins = useDocumentPageMargins(documentId, versionId)
  const saveAutoNumber = useSaveVersionAutoNumber(documentId, versionId)
  const savePageFrame = useSaveVersionPageFrame(documentId, versionId)
  const [pageFrameOpen, setPageFrameOpen] = useState(false)

  //  Thay sẵn những thẻ mà lúc soạn đã biết. Số trang thì để nhãn ngắn: trang
  //  giấy trong trình soạn thảo chưa biết mình là tờ thứ mấy của bản in.
  const veKhungTrang = (mau: string) =>
    fillPageMarkers(mau, {
      trang: '#',
      tongTrang: 'N',
      soHieu: record?.display_code || '',
      tenVanBan: record?.title || '',
      ngay: new Date().toLocaleDateString('vi-VN'),
    })

  function handleSubmitForm(values: DocumentRecordFormValues) {
    save.mutate({ id: documentId, values: formToPayload(values) })
  }

  const isNumbered = Boolean(record?.doc_code || record?.issue_number)
  //  Backend chỉ cho xóa văn bản CÒN LÀ NHÁP và CHƯA cấp số (`service.py`
  //  `delete_document`). Nút xóa phải bám đúng hai điều kiện đó, không thì
  //  người có quyền vẫn thấy nút rồi bấm vào chỉ nhận lỗi 400.
  const isRemovable = record?.status === DOCUMENT_STATUS.draft && !isNumbered
  //  Đã ban hành: đã duyệt (chờ tới ngày) hoặc đang có hiệu lực.
  const isIssued =
    record?.status === DOCUMENT_STATUS.approved || record?.status === DOCUMENT_STATUS.effective
  const isLocked = version?.is_locked ?? true
  const label = record ? effectiveLabel(record) : null

  // Bản đang mở (nháp hoặc đang duyệt)
  const openVersion = versions.find((item) => !item.is_locked)
  const isDraft = openVersion
    ? openVersion.status === VERSION_STATUS.draft
    : record?.status === DOCUMENT_STATUS.draft
  const isSubmitted = openVersion
    ? openVersion.status === VERSION_STATUS.submitted
    : record?.status === DOCUMENT_STATUS.submitted

  //  ĐANG TRÌNH DUYỆT thì đóng băng nội dung VÀ bộ trường chung (19/08/2026).
  //  Backend đã chặn (`version_service.chan_khi_dang_duyet`,
  //  `service.chan_sua_khi_dang_duyet`) — khóa ở đây để người dùng không gõ cả
  //  đoạn rồi mới nhận 409, và để tự động lưu không bắn lỗi theo từng nhịp gõ.
  const khoaVietVi = isSubmitted

  return (
    // `Tabs` bọc CẢ khung trang để hàng tab nằm cạnh tiêu đề — trang soạn thảo
    // cần từng dòng chiều cao, để tab thành một hàng riêng là đẩy tờ giấy xuống
    // thêm một nấc nữa.
    <Tabs value={tab} onValueChange={setTab}>
      <DetailPageShell
        title={record?.title ?? ''}
        description={
          record && (
            <>
              <span>
                {record.display_code || 'Chưa cấp số'} · {record.doc_type_name}
                {record.book_number_display && ` · sổ ${record.book_number_display}`}
                {version && ` · bản ${version.version_no}`}
              </span>
              {label && (
                <>
                  <span aria-hidden>·</span>
                  <Badge variant={label.variant}>{label.text}</Badge>
                </>
              )}
              {readonlyFromLink && <Badge variant="outline">Chỉ đọc</Badge>}
              {/*  Chỉ nói "tự lưu" với người THẬT SỰ sửa được. Người duyệt nay
                   mở được văn bản để đọc — nói với họ là trang đang tự lưu thì
                   họ tưởng mình vừa động vào bài của người khác. */}
              {tab === 'compose' && !isLocked && canWrite && !khoaVietVi && (
                <>
                  <span aria-hidden>·</span>
                  <DocumentAutosaveStatus
                    dirty={autosave.dirty}
                    saving={autosave.saving}
                    savedAt={autosave.savedAt}
                  />
                </>
              )}
            </>
          )
        }
        formId={FORM_ID}
        isCreating={false}
        backTo={appRoutes.document.documentsTab('outgoing')}
        isMissing={!isLoading && !record}
        missingTitle="Không tìm thấy văn bản"
        audit={{ entity: 'document', id: documentId }}
        // Tab soạn thảo là màn làm việc toàn màn hình — sổ nhật ký để ở tab
        // Thông tin, chỗ người dùng đang rà soát bản ghi.
        showHistory={tab === 'info'}
        //  Chỉ tab Thông tin mới dính tiêu đề: form dài, nút Lưu ở trên đầu.
        //  Tab Soạn thảo cuộn bên trong trang giấy, tab Phiên bản thì ngắn.
        stickyHeader={tab === 'info'}
        actions={
          <>
            <TabsList>
              <TabsTrigger value="compose">
                <FileText className="size-4" />
                Soạn thảo
              </TabsTrigger>
              <TabsTrigger value="info">
                <Info className="size-4" />
                Thông tin
              </TabsTrigger>
              <TabsTrigger value="versions">
                <GitBranch className="size-4" />
                Phiên bản
              </TabsTrigger>
              <TabsTrigger value="links">
                <Link2 className="size-4" />
                Quan hệ
              </TabsTrigger>
              <TabsTrigger value="approval">
                <ShieldCheck className="size-4" />
                Phê duyệt
              </TabsTrigger>
            </TabsList>

            {/*  MỘT MENU cho cả nhóm lệnh tệp thay vì bốn nút rời.
                 Trang này có tới tám lệnh; xếp hết ra ngoài thì cụm nút đẩy
                 rộng cả trang và sinh thanh cuộn ngang — đã gặp thật. Ở ngoài
                 chỉ giữ lệnh dùng theo nhịp soạn (Nhập tệp, Lưu, Gửi duyệt). */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button type="button" variant="outline">
                  <FileText className="size-4" />
                  Tệp
                  <ChevronDown className="size-4 opacity-60" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuItem
                  //  Lề vừa kéo còn đang ghi thì chưa mở bản in: tab in đọc
                  //  thẳng bản ghi, mở sớm là in ra lề cũ.
                  disabled={pageMargins.dangLuu}
                  onSelect={() =>
                    window.open(
                      `${appRoutes.document.documentPrint(documentId)}${versionId ? `?version=${versionId}` : ''}`,
                      '_blank',
                      'noopener',
                    )
                  }
                >
                  <Printer className="size-4" />
                  In / Xuất PDF
                </DropdownMenuItem>

                {/* Xuất .docx để người nhận sửa tiếp bằng Word — khác bản in PDF
                    là bản chốt để ký. Tải qua `downloadFile` vì cần token. */}
                <DropdownMenuItem
                  onSelect={() =>
                    void downloadFile(
                      `/api/documents/${documentId}/export/docx${versionId ? `?version_id=${versionId}` : ''}`,
                      `${record?.display_code || 'van-ban'}.docx`,
                    ).catch(() => toast.error('Không xuất được tệp Word'))
                  }
                >
                  <FileDown className="size-4" />
                  Xuất Word
                </DropdownMenuItem>

                {tab === 'compose' && canWrite && !isLocked && !khoaVietVi && (
                  <DropdownMenuItem onSelect={() => setPageFrameOpen(true)}>
                    <PanelTop className="size-4" />
                    Đầu/chân trang
                  </DropdownMenuItem>
                )}

                {/*  C19 — chỉ trích được từ văn bản ĐÃ BAN HÀNH: trích từ một
                     bản nháp là chia ra ngoài thứ chưa ai duyệt.
                     Kèm `canCreate`: bản trích là một VĂN BẢN MỚI, backend đòi
                     `document: create` (`link_controller.create_excerpt`). Người
                     chỉ có quyền đọc mà thấy mục này thì gõ xong cả nội dung
                     trích mới nhận 403 — mất công vô ích. */}
                {isIssued && canCreate && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onSelect={() => setExcerptOpen(true)}>
                      <Scissors className="size-4" />
                      Tạo bản trích
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            {/*  Nhập tệp (Word/PDF/Markdown/HTML) CÓ ở đây, không chỉ ở màn dựng
                 mẫu: phần lớn văn bản đã được soạn sẵn ngoài Word rồi mới đưa
                 vào hệ. Chèn tại con trỏ nên vẫn ghép được vào bản đang gõ dở.
                 Điều kiện hiện nút bám đúng điều kiện SỬA ĐƯỢC (bản chưa khóa +
                 có quyền ghi) — như nút Lưu nội dung bên cạnh. */}
            {tab === 'compose' && canWrite && !isLocked && !khoaVietVi && (
              <>
                <DocumentImportButton
                  hasContent={() => editorRef.current?.hasContent() ?? false}
                  onInsert={(html, mode) =>
                    editorRef.current?.insertContent(html, mode) ?? Promise.resolve(false)
                  }
                  onNavigateToTrace={(importId, page) =>
                    editorRef.current?.focusImportedPage(importId, page) ?? false
                  }
                />
                <Button type="button" onClick={autosave.saveNow} disabled={autosave.saving}>
                  {autosave.saving ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Save className="size-4" />
                  )}
                  Lưu nội dung
                </Button>
              </>
            )}

            {tab === 'info' && canWrite && !khoaVietVi && (
              <Button type="submit" form={FORM_ID} disabled={save.isPending}>
                <Save className="size-4" />
                Lưu thông tin
              </Button>
            )}

            {record?.allow_manual_number && canWrite && (
              <Button type="button" variant="outline" onClick={() => setNumberDialogOpen(true)}>
                <Pencil className="size-4" />
                Sửa số hiệu
              </Button>
            )}

            <DocumentCopyAction documentId={documentId} canCreate={canCreate} />

            {/* Luồng duyệt MỘT BƯỚC tạm thời — P3 thay bằng bộ máy chung. */}
            {isDraft && canWrite && (
              <Button
                type="button"
                variant="outline"
                onClick={() => workflow.submit.mutate()}
                disabled={workflow.submit.isPending}
              >
                <Send className="size-4" />
                Gửi duyệt
              </Button>
            )}

            {/* Văn bản ĐÃ ban hành không xóa được (số đã vào sổ) — lối gỡ bỏ
                duy nhất là bãi bỏ, giữ nguyên dòng và số. */}
            {isIssued && (
              <PermissionGate entity="document" action="cancel">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setReasonFor('revoke')}
                  disabled={workflow.revoke.isPending}
                >
                  <Ban className="size-4" />
                  Bãi bỏ
                </Button>
              </PermissionGate>
            )}

            {isSubmitted && !dangDuyetNhieuBuoc && (
              <PermissionGate entity="document" action="approve">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setReasonFor('reject')}
                  disabled={workflow.reject.isPending}
                >
                  <Undo2 className="size-4" />
                  Trả lại
                </Button>
                <Button
                  type="button"
                  onClick={() => setIssueOpen(true)}
                  disabled={workflow.approve.isPending}
                >
                  <Check className="size-4" />
                  Duyệt và ban hành
                </Button>
              </PermissionGate>
            )}
          </>
        }
        onDelete={
          record && canDelete && isRemovable
            ? () =>
                remove.mutate(record.id, {
                  onSuccess: () => navigate(appRoutes.document.documentsTab('outgoing')),
                })
            : undefined
        }
        deleteConfirmDescription="Chỉ xóa được văn bản còn là nháp và chưa cấp số. Văn bản đã ban hành thì bãi bỏ, không xóa."
      >
        {/*  J10 — đặt NGOÀI mọi `TabsContent` để hiện ở mọi tab. Cảnh báo bắt
             buộc mà giấu sau một cú bấm thì cũng như không có. */}
        <DocumentAmendedBanner documentId={documentId} />
        {/*  Cũng đặt NGOÀI mọi tab: người soạn cần biết phiếu đang chờ ai, và
             nhất là biết khi nó kẹt — dù họ đang đứng ở tab nào. */}
        <DocumentApprovalBanner instance={approval} documentId={documentId} />

        <TabsContent value="compose" className="mt-0">
          <DocumentSubmittedLockNotice submitted={khoaVietVi} />

          {record && (
            <DocumentNeedsReviewBanner
              needsReview={record.needs_review}
              note={record.needs_review_note}
              //  Bản riêng của pháp nhân con thì biết ngay bản gốc là ai; ca
              //  khác (văn bản con theo quan hệ) phải tự tìm ở tab Quan hệ.
              sourceDocumentId={record.source_document_id}
              canWrite={canWrite}
              pending={workflow.confirmReviewed.isPending}
              onConfirm={() => setReviewOpen(true)}
            />
          )}

          {record && version && (
            <DocumentVersionBanner
              document={record}
              version={version}
              onGoToCurrent={() => setPickedVersionId(record.current_version_id)}
            />
          )}

          {/* `key` theo phiên bản: đổi sang bản khác thì dựng lại trình soạn
              thảo để nó nạp đúng nội dung mới. */}
          {version && (
            <RichTextEditor
              key={version.id}
              ref={editorRef}
              showOutline
              editable={canWrite && !isLocked && !khoaVietVi}
              defaultContent={version.content_html ?? ''}
              onChange={autosave.handleChange}
              //  Lề đi theo PHIÊN BẢN: kéo thước xong là ghi xuống bản ghi, mở
              //  lại đúng như lúc đóng — và bản in dùng lại đúng bộ số này.
              defaultMargins={{
                left: mmToPx(version.margin_left_mm),
                right: mmToPx(version.margin_right_mm),
              }}
              onMarginsChange={pageMargins.luu}
              //  Đánh số mục tự động: cờ của chính phiên bản này, bấm là ghi ngay.
              autoNumber={version.auto_heading_number}
              onAutoNumberChange={(bat) => saveAutoNumber.mutate(bat)}
              pageFrame={{
                headerLeft: veKhungTrang(version.header_left),
                headerRight: veKhungTrang(version.header_right),
                footerLeft: veKhungTrang(version.footer_left),
                footerRight: veKhungTrang(version.footer_right),
              }}
            />
          )}
        </TabsContent>

        <TabsContent value="info" className="mt-0 space-y-4">
          <DocumentSubmittedLockNotice submitted={khoaVietVi} />

          <DocumentRecordForm
            formId={FORM_ID}
            form={form}
            isNumbered={isNumbered}
            documentId={documentId}
            readOnly={khoaVietVi || readonlyFromLink}
            onSubmit={handleSubmitForm}
          >
            <DocumentAttachmentList
              versionId={versionId}
              readOnly={!canWrite || isLocked || khoaVietVi}
              documentCode={record?.display_code}
            />
            {/*  Phạm vi áp dụng (F01–F04) khác QUYỀN TRUY CẬP: phạm vi trả lời
                 "văn bản này áp cho ai phải làm theo", quyền trả lời "ai được
                 mở ra đọc". Hai câu hỏi khác nhau, để cạnh nhau cho dễ đối chiếu. */}
            {/*  Chữ ký gắn với PHIÊN BẢN đang mở — ký được sau khi bản đó đã
                 duyệt và khóa lại. */}
            <DocumentSignatureCard
              documentId={documentId}
              versionId={versionId}
              isLocked={isLocked}
              canApprove={canApprove}
            />
            {/*  Chỉ còn PHẠM VI ở đây. Thẻ «Bản clone ở pháp nhân con» đã bỏ:
                 nơi nhận bản riêng nay SUY từ chính khối phạm vi này, nên nó
                 chỉ lặp lại cùng một danh sách bằng một cách nói khác. Muốn
                 xem bản riêng đã sinh ra chưa, ai đang lệch bản — mở tab
                 «Quan hệ», thẻ Cây tài liệu liệt kê đủ kèm tên pháp nhân. */}
            <DocumentScopeCard
              documentId={documentId}
              canWrite={canWrite}
              isClone={Boolean(record?.source_document_id)}
            />
            <DocumentAccessCard documentId={documentId} canWrite={canWrite} />
          </DocumentRecordForm>
        </TabsContent>

        <TabsContent value="versions" className="mt-0">
          {record && (
            <DocumentVersionTab
              document={record}
              activeVersionId={versionId}
              canWrite={canWrite}
              onSelect={(picked) => {
                setPickedVersionId(picked.id)
                setTab('compose')
              }}
            />
          )}
        </TabsContent>

        <TabsContent value="approval" className="mt-0">
          <DocumentApprovalTab instance={approval} documentId={documentId} />
        </TabsContent>

        <TabsContent value="links" className="mt-0">
          <DocumentLinkTab documentId={documentId} canWrite={canWrite} />
        </TabsContent>

        {/*  F13 — chốt lần cuối trước khi ban hành. Cơ chế áp dụng KHÔNG hỏi ở
             đây nữa mà suy từ phạm vi đã khai; hộp thoại chỉ nói rõ điều đó. */}
        {record && (
          <DocumentIssueDialog
            documentId={documentId}
            open={issueOpen}
            onOpenChange={setIssueOpen}
            issuerCompanyId={record.company_id}
            isPending={workflow.approve.isPending}
            onConfirm={(applyMode) =>
              workflow.approve.mutate(applyMode, { onSuccess: () => setIssueOpen(false) })
            }
          />
        )}

        {version && (
          <DocumentPageFrameDialog
            open={pageFrameOpen}
            onOpenChange={setPageFrameOpen}
            pending={savePageFrame.isPending}
            value={{
              header_left: version.header_left,
              header_right: version.header_right,
              footer_left: version.footer_left,
              footer_right: version.footer_right,
            }}
            onSubmit={(giaTri) =>
              savePageFrame.mutate(giaTri, { onSuccess: () => setPageFrameOpen(false) })
            }
          />
        )}

        {/* C19 — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn. */}
        {record && (
          <DocumentExcerptDialog
            open={excerptOpen}
            onOpenChange={setExcerptOpen}
            sourceSecrecy={record.secrecy_level}
            sourceTitle={record.title}
            //  Thân bản ĐANG XEM: hộp thoại cắt ra mục lục để tick, khỏi bôi đen dán tay.
            sourceHtml={version?.content_html ?? ''}
            isPending={createExcerpt.isPending}
            onSubmit={(values) =>
              createExcerpt.mutate(values, { onSuccess: () => setExcerptOpen(false) })
            }
          />
        )}

        {/* Lý do đi vào nhật ký thao tác và người khác sẽ đọc lại, nên hỏi bằng
            hộp thoại của hệ thống — bắt buộc điền, gõ được nhiều dòng. */}
        <ReasonConfirmDialog
          open={reasonFor !== null}
          onOpenChange={(open) => !open && setReasonFor(null)}
          title={reasonFor === 'revoke' ? 'Bãi bỏ văn bản?' : 'Trả lại bản nháp?'}
          description={
            reasonFor === 'revoke'
              ? `${record?.display_code || 'Văn bản'} chuyển sang trạng thái "Bãi bỏ" và hết hiệu lực kể từ hôm nay. Số hiệu vẫn giữ nguyên trong sổ, không xóa được.`
              : 'Người soạn nhận lại bản nháp kèm lý do bên dưới để sửa tiếp.'
          }
          placeholder={
            reasonFor === 'revoke'
              ? 'Ví dụ: đã thay bằng công văn 05/2026/CV-DEGO'
              : 'Ví dụ: thiếu căn cứ ở mục 2'
          }
          confirmText={reasonFor === 'revoke' ? 'Bãi bỏ' : 'Trả lại'}
          destructive={reasonFor === 'revoke'}
          pending={reasonFor === 'revoke' ? workflow.revoke.isPending : workflow.reject.isPending}
          onConfirm={(reason) => {
            const action = reasonFor === 'revoke' ? workflow.revoke : workflow.reject
            action.mutate(reason, { onSuccess: () => setReasonFor(null) })
          }}
        />

        {/*  RÀ LẠI theo bản gốc. Hộp thoại tự giữ hai mutation của nó (gỡ dấu +
             mở phiên bản) để chạy đúng thứ tự và giữ câu lỗi 409 ở lại tại chỗ. */}
        {record && (
          <DocumentReviewDialog
            documentId={documentId}
            open={reviewOpen}
            onOpenChange={setReviewOpen}
            note={record.needs_review_note}
            sourceDocumentId={record.source_document_id}
          />
        )}
        {record && (
          <ManualIssueNumberDialog
            open={numberDialogOpen}
            currentNumber={record.issue_number}
            pending={updateIssueNumber.isPending}
            onOpenChange={setNumberDialogOpen}
            onConfirm={(values) =>
              updateIssueNumber.mutate(values, {
                onSuccess: () => setNumberDialogOpen(false),
              })
            }
          />
        )}
      </DetailPageShell>
    </Tabs>
  )
}
