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
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
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
        //  ⚠️ Dòng mô tả ẩn ở khổ hẹp **CHỈ Ở TAB THÔNG TIN**, và cái điều kiện
        //  đó không phải để cho chặt chẽ:
        //  - tab *Thông tin* bày đúng hai thứ này thành ô nhập ngay bên dưới
        //    (*Loại văn bản*, *Trạng thái sử dụng*), nên ở đây nó chỉ nói lại; mà
        //    tab này lại là tab GHIM dải, nên mỗi dòng là chỗ đứng yên vĩnh viễn
        //    — riêng nó ăn 22px, kéo dải từ 146px lên **172px = 22%** màn 796px;
        //  - tab *Soạn mẫu* thì ngược lại: cả màn chỉ có trang giấy, **không chỗ
        //    nào khác nói mẫu này thuộc loại gì và còn dùng hay không**. Ẩn ở đó
        //    là xóa thông tin, không phải dọn chỗ.
        description={
          isCreating ? (
            'Soạn nội dung mẫu và bổ sung thông tin trước khi lưu.'
          ) : (
            <span
              className={cn(
                'flex flex-wrap items-center gap-x-2',
                tab === 'info' && 'max-md:hidden',
              )}
            >
              <span>
                {template?.doc_type_code} · {template?.doc_type_name}
              </span>
              <span aria-hidden>·</span>
              <Badge variant={template?.is_active ? 'default' : 'secondary'}>
                {template?.is_active ? 'Đang dùng' : 'Ngừng sử dụng'}
              </Badge>
            </span>
          )
        }
        formId={FORM_ID}
        isCreating={isCreating}
        backTo={backTo}
        isMissing={!isCreating && !isLoading && !template}
        missingTitle="Không tìm thấy văn bản mẫu"
        audit={template ? { entity: 'document_template', id: template.id } : undefined}
        showHistory={tab === 'info'}
        //  ⚠️ **Chỉ tab Thông tin mới ghim dải tiêu đề**, giống chi tiết Văn bản
        //  (duoc-CR-366). Hai tab cuộn bằng hai cơ chế khác nhau: tab *Thông tin*
        //  là biểu mẫu cộng nhật ký nên CẢ TRANG cuộn, còn tab *Soạn mẫu* có
        //  khung cuộn riêng bên trong trang giấy (`.doc-canvas`, đo được 1166px
        //  nội dung trong khe 840px). Ghim ở tab soạn thì dải chỉ ăn mất chiều
        //  cao của chính chỗ đang gõ mà không giữ lại được gì — nút Lưu ở đó
        //  không trôi đi theo nhịp cuộn của trang giấy.
        stickyHeader={tab === 'info'}
        onDelete={
          template
            ? () =>
                remove.mutate(template.id, {
                  onSuccess: () => navigate(backTo),
                })
            : undefined
        }
        deleteConfirmDescription="Văn bản đã tạo từ mẫu này vẫn giữ nguyên nội dung. Thao tác xóa mẫu không hoàn tác được."
        //  Khổ hẹp cụm nút dồn TRÁI. Mặc định `justify-end` đúng khi chỉ một hai
        //  nút; ở đây cụm tràn nhiều hàng nên mỗi hàng lại bắt đầu ở một mốc khác
        //  nhau — đọc ra như mấy nút rơi vãi chứ không ra một cụm.
        actionsClassName="max-md:justify-start"
        //  ⚠️ *Nhập tệp* vào nhóm PHỤ: khổ hẹp nó gom vào nút `⋯` cùng với Xóa,
        //  nhường chỗ cho nút Lưu. Đây là lệnh dùng thưa (mỗi mẫu vài lần lúc
        //  dựng), trong khi Lưu là việc lặp suốt buổi soạn.
        //  Chỉ tab *Soạn mẫu* mới có nó — tab Thông tin không có gì để nhập vào.
        secondaryActions={
          tab === 'compose' ? (
            <DocumentImportButton
              hasContent={() => editorRef.current?.hasContent() ?? false}
              onInsert={(html, mode) =>
                editorRef.current?.insertContent(html, mode) ?? Promise.resolve(false)
              }
              onNavigateToTrace={(importId, page) =>
                editorRef.current?.focusImportedPage(importId, page) ?? false
              }
            />
          ) : undefined
        }
        actions={
          <>
            {/*  ⚠️ **Dải tab phải là `ScrollableTabsList` và phải chiếm TRỌN một
                 hàng** — bốn lớp dưới đây đi kèm nhau, bài học đã trả giá ở chi
                 tiết Văn bản (duoc-CR-366), chép nguyên vì cùng một cấu trúc:
                 - `basis-full` để dải không chen chung hàng với nút lệnh;
                 - `min-w-0` vì ô flex mặc định `min-width:auto`, thiếu nó thì
                   khung nở theo dải bên trong và `overflow-x-auto` **không có gì
                   để cuộn**, `justify-end` lại đẩy cả khối sang toạ độ ÂM;
                 - `grow` để nuốt đúng 32px mà lề âm `-mx-4` của
                   `ScrollableTabsList` chừa ra, nếu không dải bắt đầu ở `x = 32`
                   và mất phần chạm mép trái;
                 - `order-first` vì dải tab là thứ ĐIỀU HƯỚNG, nó thuộc về ngay
                   dưới tiêu đề chứ không kẹt giữa mấy nút lệnh.
                 Từ `md` trở lên mọi lớp `max-md:*` tắt, dải về đúng `TabsList`
                 nền xám cũ nằm cạnh tiêu đề — bố cục desktop không đổi. */}
            <ScrollableTabsList
              value={tab}
              className="max-md:order-first max-md:min-w-0 max-md:grow max-md:basis-full"
            >
              <TabsTrigger value="compose" className={TAB_TRIGGER_UNDERLINE}>
                <FileText className="size-4" />
                Soạn mẫu
              </TabsTrigger>
              <TabsTrigger value="info" className={TAB_TRIGGER_UNDERLINE}>
                <Info className="size-4" />
                Thông tin
              </TabsTrigger>
            </ScrollableTabsList>

            {/*  `max-md:flex-1` — Lưu là việc chính của trang, cho nó trải hết
                 phần còn lại của hàng thay vì co theo chữ rồi chừa một khoảng
                 trống dài bên cạnh nút `⋯`.

                 ⚠️ `md:order-last` để TRẢ LẠI thứ tự cũ trên màn rộng. Dời *Nhập
                 tệp* sang `secondaryActions` cũng dời luôn chỗ nó được dựng: khung
                 chung vẽ nhóm phụ SAU `actions`, nên không có lớp này thì desktop
                 thành «… Lưu nội dung · Nhập tệp» — việc chính không còn đứng
                 cuối, chỗ mắt quen tìm nút cần bấm. */}
            <Button
              type="submit"
              form={FORM_ID}
              disabled={save.isPending}
              className="max-md:flex-1 md:order-last"
            >
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
