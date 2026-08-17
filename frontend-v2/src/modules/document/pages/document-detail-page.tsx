import { zodResolver } from '@hookform/resolvers/zod'
import {
  Ban,
  Check,
  FileText,
  GitBranch,
  Info,
  Link2,
  Loader2,
  Pencil,
  Save,
  Scissors,
  Send,
  Undo2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { RichTextEditor } from '@/shared/ui/rich-text-editor'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentAmendedBanner } from '../components/document-amended-banner'
import { DocumentAccessCard } from '../components/document-access-card'
import { DocumentScopeCard } from '../components/document-scope-card'
import { DocumentSignatureCard } from '../components/document-signature-card'
import { DocumentAttachmentList } from '../components/document-attachment-list'
import { DocumentAutosaveStatus } from '../components/document-autosave-status'
import { DocumentRecordForm } from '../components/document-record-form'
import { DocumentVersionBanner } from '../components/document-version-banner'
import { DocumentVersionTab } from '../components/document-version-tab'
import { DocumentLinkTab } from '../components/document-link-tab'
import { DocumentExcerptDialog } from '../components/document-excerpt-dialog'
import { DocumentIssueDialog } from '../components/document-issue-dialog'
import { DocumentNeedsReviewBanner } from '../components/document-needs-review-banner'
import { useCreateExcerpt } from '../hooks/use-document-links'
import { ManualIssueNumberDialog } from '../components/manual-issue-number-dialog'
import { documentToForm, emptyDocumentForm, formToPayload } from '../helpers/document-form-defaults'
import { effectiveLabel } from '../helpers/document-status'
import { useDocumentPermissions } from '../hooks/use-document-access'
import { useDocumentAutosave } from '../hooks/use-document-autosave'
import {
  useDocumentVersion,
  useDocumentVersions,
  useSaveVersionContent,
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
import { DOCUMENT_STATUS } from '../types/document-record'

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
  const [tab, setTab] = useUrlParamState('tab', 'compose')

  const documentId = Number(id)
  const { data: record, isLoading } = useDocument(documentId)
  const { data: versions = [] } = useDocumentVersions(documentId)
  const { data: permissions } = useDocumentPermissions(documentId)

  // Bản người dùng tự chọn; `null` = để hệ chọn. TÍNH RA `versionId` chứ không
  // đồng bộ bằng effect: mở bản mới xong danh sách đổi, effect sẽ chạy lại và
  // kéo màn hình về bản khác ngay dưới tay người đang xem.
  const [pickedVersionId, setPickedVersionId] = useState<number | null>(null)
  //  Hộp hỏi lý do đang mở cho việc gì (`null` = đang đóng). Hai việc dùng
  //  chung một hộp vì chỉ khác chữ.
  const [reasonFor, setReasonFor] = useState<'revoke' | 'reject' | null>(null)
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

  const { can } = usePermission()
  //  Ký là hành vi PHÊ DUYỆT, không phải sửa nội dung — gác bằng `approve` đúng
  //  như backend làm.
  const canApprove = can('document', 'approve')
  const canWrite = permissions?.write ?? false
  const canDelete = permissions?.delete ?? false

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
              {tab === 'compose' && !isLocked && (
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
        backTo={appRoutes.document.documents}
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
            </TabsList>

            {/*  C19 — chỉ trích được từ văn bản ĐÃ BAN HÀNH: trích từ một bản
                 nháp là chia ra ngoài thứ chưa ai duyệt. */}
            {isIssued && (
              <Button type="button" variant="outline" onClick={() => setExcerptOpen(true)}>
                <Scissors className="size-4" />
                Tạo bản trích
              </Button>
            )}

            {/* KHÔNG có nút nhập tệp ở đây: nhập từ Word/Markdown chỉ dùng lúc
                dựng MẪU (`document-template-detail-page.tsx`). Văn bản thật soạn
                từ mẫu hoặc gõ thẳng, không đổ nguyên một tệp ngoài vào. */}
            {tab === 'compose' && canWrite && !isLocked && (
              <>
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

            {tab === 'info' && canWrite && (
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

            {/* Luồng duyệt MỘT BƯỚC tạm thời — P3 thay bằng bộ máy chung. */}
            {record?.status === DOCUMENT_STATUS.draft && canWrite && (
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

            {record?.status === DOCUMENT_STATUS.submitted && (
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
                  onSuccess: () => navigate(appRoutes.document.documents),
                })
            : undefined
        }
        deleteConfirmDescription="Chỉ xóa được văn bản còn là nháp và chưa cấp số. Văn bản đã ban hành thì bãi bỏ, không xóa."
      >
        {/*  J10 — đặt NGOÀI mọi `TabsContent` để hiện ở mọi tab. Cảnh báo bắt
             buộc mà giấu sau một cú bấm thì cũng như không có. */}
        <DocumentAmendedBanner documentId={documentId} />

        <TabsContent value="compose" className="mt-0">
          {record && (
            <DocumentNeedsReviewBanner
              needsReview={record.needs_review}
              note={record.needs_review_note}
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
              showOutline
              editable={canWrite && !isLocked}
              defaultContent={version.content_html ?? ''}
              onChange={autosave.handleChange}
            />
          )}
        </TabsContent>

        <TabsContent value="info" className="mt-0 space-y-4">
          <DocumentRecordForm
            formId={FORM_ID}
            form={form}
            isNumbered={isNumbered}
            documentId={documentId}
            onSubmit={handleSubmitForm}
          >
            <DocumentAttachmentList versionId={versionId} readOnly={!canWrite || isLocked} />
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
            <DocumentScopeCard documentId={documentId} canWrite={canWrite} />
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

        <TabsContent value="links" className="mt-0">
          <DocumentLinkTab documentId={documentId} canWrite={canWrite} />
        </TabsContent>

        {/*  F13 — hỏi cơ chế áp dụng TRƯỚC khi ban hành. Không hỏi thì mọi văn
             bản đi theo mặc định "gắn phạm vi", và người ban hành không bao giờ
             biết là có lựa chọn thứ hai. */}
        {record && (
          <DocumentIssueDialog
            documentId={documentId}
            open={issueOpen}
            onOpenChange={setIssueOpen}
            currentMode={record.apply_mode}
            isPending={workflow.approve.isPending}
            onConfirm={(applyMode) =>
              workflow.approve.mutate(applyMode, { onSuccess: () => setIssueOpen(false) })
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
