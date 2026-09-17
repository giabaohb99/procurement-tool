import { Download, Eye, FileImage, FileText, File as FileIcon, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { downloadFile } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { AttachmentPreviewDialog } from '@/shared/attachments/attachment-preview-dialog'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatFileSize } from '@/shared/utils/format-file-size'
import {
  dossierAttachmentDownloadUrl,
  type DossierAttachment,
} from '../api/dossier-attachment-api'
import {
  useDeleteDossierAttachment,
  useDossierAttachments,
  useUploadDossierAttachments,
} from '../hooks/use-dossier-attachments'

/** Trần dung lượng MỘT tệp — khai ở `FILE_POLICY["dossier"]` của backend. */
const MAX_SIZE_MB = 50

function fileIcon(file: DossierAttachment) {
  const type = (file.content_type || '').toLowerCase()
  if (type.startsWith('image/')) return FileImage
  if (type.includes('pdf')) return FileText
  return FileIcon
}

/**
 * BẢN SCAN của một hồ sơ — tab «Tệp đính kèm» ở trang chi tiết.
 *
 * ⚠️ **Không dùng lại `DocumentAttachmentsCard` của Thu mua**, dù hai màn nhìn
 * gần giống nhau. Bản đó dựng quanh khái niệm THƯ MỤC theo danh mục `doc_type`
 * (Hợp đồng · Báo giá · Hóa đơn…) và kéo theo cả `useDocumentTypes`,
 * `DocumentStatusBadge`, tình trạng hồ sơ chứng từ của ĐMH — 563 dòng cho một
 * mô hình mà hồ sơ không có: ở đây **chính cái hồ sơ đã là thư mục**, chia nhỏ
 * thêm một cấp nữa là bắt người dùng phân loại hai lần cho cùng một tờ giấy.
 *
 * ⚠️ `dossier` nằm trong `PRIVATE_ENTITIES` nên backend **không trả `url`** đọc
 * thẳng kho lưu trữ. Mọi việc đọc nội dung đi qua `/api/attachments/{id}/view`
 * hoặc `/download` bằng `httpClient` — gắn thẳng `<img src>` / `<a href>` vào
 * API thì trình duyệt tự đi lấy và **không mang token**, tới nơi là 401.
 */
export function DossierAttachmentsCard({ dossierId }: { dossierId: number }) {
  const { can } = usePermission()
  //  Đính kèm ăn theo quyền của CHỨNG TỪ CHA (`FILE_POLICY`), nên gác bằng
  //  `dossier.write`/`create` chứ không có khóa riêng — đúng như backend kiểm.
  const canManage = can('dossier', 'write') || can('dossier', 'create')

  const { data: files, isLoading } = useDossierAttachments(dossierId)
  const uploadMutation = useUploadDossierAttachments(dossierId)
  const deleteMutation = useDeleteDossierAttachment(dossierId)
  const [previewing, setPreviewing] = useState<DossierAttachment | null>(null)

  const handleFiles = (picked: File[]) => {
    //  Chặn ngay tại đây cho khỏi tải lên rồi mới ăn 413: người dùng chờ hết một
    //  tệp 80MB rồi mới biết là không được thì đó là hai phút mất trắng.
    const tooBig = picked.filter((f) => f.size > MAX_SIZE_MB * 1024 * 1024)
    if (tooBig.length > 0) {
      toast.error(
        `Vượt quá ${MAX_SIZE_MB}MB: ${tooBig.map((f) => f.name).join(', ')}`,
      )
    }
    const ok = picked.filter((f) => f.size <= MAX_SIZE_MB * 1024 * 1024)
    if (ok.length > 0) uploadMutation.mutate(ok)
  }

  const handleDownload = async (file: DossierAttachment) => {
    try {
      await downloadFile(dossierAttachmentDownloadUrl(file.id), file.filename)
    } catch {
      toast.error(`Không tải được tệp «${file.filename}».`)
    }
  }

  return (
    <Card className="gap-4 p-3 sm:p-5">
      <div className="min-w-0">
        <h3 className="text-sm font-semibold">Bản scan đính kèm</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Bản chụp / bản quét của chính tờ giấy đang lưu. Tối đa {MAX_SIZE_MB}MB mỗi tệp.
        </p>
      </div>

      {canManage && (
        <FileDropzone
          onFiles={handleFiles}
          busy={uploadMutation.isPending}
          hint="Kéo tệp vào đây hoặc bấm để chọn"
        />
      )}

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : !files || files.length === 0 ? (
        //  ⚠️ Câu rỗng nói rõ CÓ THỂ LÀM GÌ, và nói khác nhau theo quyền: người
        //  không tải lên được mà đọc «Kéo tệp vào đây» thì đi tìm một vùng thả
        //  không tồn tại.
        <p className="rounded-lg border border-dashed px-3 py-6 text-center text-sm text-muted-foreground">
          {canManage
            ? 'Chưa có bản scan nào. Kéo tệp vào vùng trên để tải lên.'
            : 'Chưa có bản scan nào được đính kèm.'}
        </p>
      ) : (
        <ul className="space-y-2">
          {files.map((file) => {
            const Icon = fileIcon(file)
            return (
              <li
                key={file.id}
                className="flex items-center gap-3 rounded-lg border bg-card px-3 py-2"
              >
                <Icon className="size-5 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium" title={file.filename}>
                    {file.filename}
                  </p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                </div>

                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    title="Xem trước"
                    onClick={() => setPreviewing(file)}
                  >
                    <Eye className="size-4" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-8"
                    title="Tải về"
                    onClick={() => void handleDownload(file)}
                  >
                    <Download className="size-4" />
                  </Button>
                  {canManage && (
                    <ConfirmIconButton
                      icon={Trash2}
                      title="Gỡ tệp"
                      confirmTitle="Gỡ tệp đính kèm?"
                      confirmDescription={`Gỡ «${file.filename}» khỏi hồ sơ này? Tệp sẽ không mở lại được từ đây nữa.`}
                      destructive
                      disabled={deleteMutation.isPending}
                      onConfirm={() => deleteMutation.mutate(file.id)}
                    />
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <AttachmentPreviewDialog
        file={previewing}
        open={Boolean(previewing)}
        onOpenChange={(open) => !open && setPreviewing(null)}
      />
    </Card>
  )
}
