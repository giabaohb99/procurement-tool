import { zodResolver } from '@hookform/resolvers/zod'
import {
  Check,
  FileText,
  GitBranch,
  Info,
  Loader2,
  Save,
  Send,
  Undo2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { RichTextEditor } from '@/shared/ui/rich-text-editor'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentAccessCard } from '../components/document-access-card'
import { DocumentAttachmentList } from '../components/document-attachment-list'
import { DocumentAutosaveStatus } from '../components/document-autosave-status'
import { DocumentRecordForm } from '../components/document-record-form'
import { DocumentVersionBanner } from '../components/document-version-banner'
import { DocumentVersionTab } from '../components/document-version-tab'
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
  const saveContent = useSaveVersionContent(documentId, versionId)

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
            </TabsList>

            {tab === 'compose' && canWrite && !isLocked && (
              <Button type="button" onClick={autosave.saveNow} disabled={autosave.saving}>
                {autosave.saving ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Save className="size-4" />
                )}
                Lưu nội dung
              </Button>
            )}

            {tab === 'info' && canWrite && (
              <Button type="submit" form={FORM_ID} disabled={save.isPending}>
                <Save className="size-4" />
                Lưu thông tin
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

            {record?.status === DOCUMENT_STATUS.submitted && (
              <PermissionGate entity="document" action="approve">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    const reason = window.prompt('Lý do trả lại bản nháp?')
                    if (reason?.trim()) workflow.reject.mutate(reason.trim())
                  }}
                >
                  <Undo2 className="size-4" />
                  Trả lại
                </Button>
                <Button
                  type="button"
                  onClick={() => workflow.approve.mutate()}
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
          record && canDelete
            ? () =>
                remove.mutate(record.id, {
                  onSuccess: () => navigate(appRoutes.document.documents),
                })
            : undefined
        }
        deleteConfirmDescription="Chỉ xóa được văn bản còn là nháp và chưa cấp số. Văn bản đã ban hành thì bãi bỏ, không xóa."
      >
        <TabsContent value="compose" className="mt-0">
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
      </DetailPageShell>
    </Tabs>
  )
}
