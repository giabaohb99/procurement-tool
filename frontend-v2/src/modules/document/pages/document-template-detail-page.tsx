import { FileText, Info, Loader2, Save } from 'lucide-react'
import { useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import type { RichTextEditorHandle } from '@/shared/ui/rich-text-editor'
import { Tabs, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DetailPageShell } from '../components/detail-page-shell'
import { DocumentTemplateForm } from '../components/document-template-form'
import { DocumentImportButton } from '../components/document-import-button'
import {
  useDeleteDocumentTemplate,
  useDocumentTemplate,
  useSaveDocumentTemplate,
} from '../hooks/use-document-templates'

const FORM_ID = 'document-template-form'

/** Trang tạo/sửa mẫu dùng cùng trình soạn thảo A4 với nội dung văn bản thật. */
export function DocumentTemplateDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [requestedTab, setTab] = useUrlParamState('tab', 'compose')
  const editorRef = useRef<RichTextEditorHandle>(null)
  const tab = requestedTab === 'info' ? 'info' : 'compose'
  const templateId = Number(id)
  const isCreating = !Number.isFinite(templateId)

  const { data: template, isLoading } = useDocumentTemplate(isCreating ? undefined : templateId)
  const save = useSaveDocumentTemplate()
  const remove = useDeleteDocumentTemplate()
  const backTo = appRoutes.document.settingsTab('templates')

  if (!isCreating && isLoading) {
    return (
      <PageContainer className="space-y-5">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-120 w-full" />
      </PageContainer>
    )
  }

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <DetailPageShell
        title={isCreating ? 'Tạo văn bản mẫu' : (template?.name ?? '')}
        description={
          isCreating ? (
            'Soạn nội dung mẫu và bổ sung thông tin trước khi lưu.'
          ) : (
            <>
              <span>
                {template?.doc_type_code} · {template?.doc_type_name}
              </span>
              <span aria-hidden>·</span>
              <Badge variant={template?.is_active ? 'default' : 'secondary'}>
                {template?.is_active ? 'Đang dùng' : 'Ngừng sử dụng'}
              </Badge>
            </>
          )
        }
        formId={FORM_ID}
        isCreating={isCreating}
        backTo={backTo}
        isMissing={!isCreating && !isLoading && !template}
        missingTitle="Không tìm thấy văn bản mẫu"
        audit={template ? { entity: 'document_template', id: template.id } : undefined}
        showHistory={tab === 'info'}
        onDelete={
          template
            ? () =>
                remove.mutate(template.id, {
                  onSuccess: () => navigate(backTo),
                })
            : undefined
        }
        deleteConfirmDescription="Văn bản đã tạo từ mẫu này vẫn giữ nguyên nội dung. Thao tác xóa mẫu không hoàn tác được."
        actions={
          <>
            <TabsList>
              <TabsTrigger value="compose">
                <FileText className="size-4" />
                Soạn mẫu
              </TabsTrigger>
              <TabsTrigger value="info">
                <Info className="size-4" />
                Thông tin
              </TabsTrigger>
            </TabsList>

            {tab === 'compose' && (
              <DocumentImportButton
                onInsert={(html) => editorRef.current?.insertContent(html) ?? false}
              />
            )}

            <Button type="submit" form={FORM_ID} disabled={save.isPending}>
              {save.isPending ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Save className="size-4" />
              )}
              {isCreating
                ? 'Tạo văn bản mẫu'
                : tab === 'compose'
                  ? 'Lưu nội dung'
                  : 'Lưu thông tin'}
            </Button>
          </>
        }
      >
        {(isCreating || template) && (
          <DocumentTemplateForm
            editorRef={editorRef}
            formId={FORM_ID}
            template={template}
            onInvalid={() => {
              setTab('info')
              toast.error('Còn thông tin bắt buộc chưa nhập')
            }}
            onSubmit={(values) =>
              save.mutate(
                { id: template?.id, values },
                {
                  onSuccess: (saved) => {
                    if (isCreating) {
                      navigate(appRoutes.document.templateDetail(saved.id), {
                        replace: true,
                      })
                    }
                  },
                },
              )
            }
          />
        )}
      </DetailPageShell>
    </Tabs>
  )
}
