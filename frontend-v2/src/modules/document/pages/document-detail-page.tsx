import { zodResolver } from '@hookform/resolvers/zod'
import { FileText, Info, Loader2, Save } from 'lucide-react'
import { useCallback, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { RichTextEditor } from '@/shared/ui/rich-text-editor'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentAttachmentList } from '../components/document-attachment-list'
import { DocumentAutosaveStatus } from '../components/document-autosave-status'
import { DocumentRecordForm } from '../components/document-record-form'
import { emptyDocumentForm } from '../helpers/document-form-defaults'
import { useDocumentAutosave } from '../hooks/use-document-autosave'
import { useDocument, useDocumentActions, useDocumentHistory } from '../hooks/use-documents'
import {
  documentRecordSchema,
  type DocumentRecordFormValues,
} from '../schemas/document-record-schema'
import { DIRECTION_LABELS, type DocumentAttachment } from '../types/document-record'

const FORM_ID = 'document-record-form'

/**
 * Trang CHI TIẾT một văn bản, chia hai tab:
 *  - "Soạn thảo": trang giấy trắng kiểu Word, tự động lưu trong lúc gõ.
 *  - "Thông tin": xem lại và sửa những gì đã khai lúc tạo.
 *
 * Mở lên vào thẳng tab soạn thảo vì tạo xong thì việc kế tiếp luôn là gõ nội
 * dung; tab đang xem ghi lên URL để gửi link cho người khác vẫn ra đúng chỗ.
 */
export function DocumentDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [tab, setTab] = useUrlParamState('tab', 'compose')

  const recordId = Number(id)
  const record = useDocument(recordId)
  const history = useDocumentHistory(recordId)
  const { save, saveContent, remove } = useDocumentActions()

  const form = useForm<DocumentRecordFormValues>({
    resolver: zodResolver(documentRecordSchema),
    defaultValues: { ...emptyDocumentForm(), ...record },
  })

  // Tệp đính kèm giữ ngoài react-hook-form: chúng không có ràng buộc nào để
  // kiểm, mà cho vào form thì mỗi lần thêm file lại chạy toàn bộ validate.
  const [attachments, setAttachments] = useState<DocumentAttachment[]>(
    record?.attachments ?? [],
  )


  const handleSaveContent = useCallback(
    (content: string, options: { silent: boolean }) => {
      saveContent(recordId, content, options)
      if (!options.silent) toast.success('Đã lưu nội dung văn bản')
    },
    [saveContent, recordId],
  )

  const autosave = useDocumentAutosave({ onSave: handleSaveContent })

  function handleSubmit(values: DocumentRecordFormValues) {
    save(
      {
        ...values,
        attachments,
        // Ba trường này do hệ cấp lúc tạo, sửa thì giữ nguyên.
        content: record?.content ?? '',
        code: record?.code ?? '',
        book_no: record?.book_no ?? 0,
        book_year: record?.book_year ?? 0,
      },
      recordId,
    )
    toast.success('Đã cập nhật văn bản')
  }

  return (
    // `Tabs` bọc CẢ khung trang để hàng tab nằm được trên đầu trang, cạnh tiêu
    // đề — trang soạn thảo cần từng dòng chiều cao, để tab thành một hàng riêng
    // là đẩy tờ giấy xuống thêm một nấc nữa.
    <Tabs value={tab} onValueChange={setTab}>
      <DetailPageShell
        title={record?.title ?? ''}
        description={
          record && (
            <>
              <span>
                {record.code} · {DIRECTION_LABELS[record.direction]} · số {record.book_no}/
                {record.book_year}
              </span>
              {/* Trạng thái tự lưu đứng ngay cạnh phụ đề, cùng chỗ mắt nhìn khi
                  ngước lên tìm nút Lưu. */}
              {tab === 'compose' && (
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
        isMissing={!record}
        missingTitle="Không tìm thấy văn bản"
        history={history}
        // Tab soạn thảo là màn làm việc toàn màn hình — sổ lịch sử để ở tab
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
            </TabsList>

            {tab === 'compose' && (
              // Khóa nút trong lúc lưu để không dồn hai lượt ghi chồng nhau;
              // chữ giữ nguyên để bề ngang nút không nhảy.
              <Button type="button" onClick={autosave.saveNow} disabled={autosave.saving}>
                {autosave.saving ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Save className="size-4" />
                )}
                Lưu nội dung
              </Button>
            )}

            {tab === 'info' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate(appRoutes.document.documents)}
                >
                  Hủy
                </Button>
                <Button type="submit" form={FORM_ID}>
                  <Save className="size-4" />
                  Lưu thông tin
                </Button>
              </>
            )}
          </>
        }
        onDelete={
          record
            ? () => {
                remove(record.id)
                toast.success(`Đã xóa văn bản ${record.code}`)
                navigate(appRoutes.document.documents)
              }
            : undefined
        }
      >
        <TabsContent value="compose" className="mt-0">
          {/* `key` theo id: đổi sang văn bản khác thì dựng lại trình soạn thảo
              để nó nạp đúng nội dung mới. */}
          <RichTextEditor
            key={recordId}
            showOutline
            defaultContent={record?.content ?? ''}
            onChange={autosave.handleChange}
          />
        </TabsContent>

        <TabsContent value="info" className="mt-0">
          <DocumentRecordForm formId={FORM_ID} form={form} isEditing onSubmit={handleSubmit}>
            <DocumentAttachmentList attachments={attachments} onChange={setAttachments} />
          </DocumentRecordForm>
        </TabsContent>
      </DetailPageShell>
    </Tabs>
  )
}
