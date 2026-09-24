import { Folder, Pencil, Star } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { useSetDocumentFolders } from '../hooks/use-document-folders'
import type { DocumentFolderRef } from '../types/document-folder'
import { FolderPicker } from './folder-picker'

interface DocumentFoldersCardProps {
  documentId: number
  /** Pháp nhân BAN HÀNH của văn bản — lọc thư mục chọn thêm đúng pháp nhân đó. */
  companyId: number
  folders: DocumentFolderRef[]
  /** Ai sửa được văn bản thì mới sắp xếp lại thư mục — cùng cờ với các thẻ khác. */
  canWrite: boolean
}

/**
 * THẺ «THƯ MỤC» ở tab Thông tin của trang chi tiết (phase 06, duoc-CR-476).
 *
 * Cố ý đứng NGOÀI `DocumentRecordForm`/`documentRecordSchema` — đổi thư mục đi
 * qua cửa RIÊNG `PUT /api/documents/{id}/folders`
 * (`documentFolderApi.setDocumentFolders`), không qua nút "Lưu thông tin" hay
 * autosave của form chính. Nhờ vậy đổi thư mục **không bị khóa theo trạng thái
 * văn bản** (đã ban hành vẫn sắp xếp lại được, khác các ô của bộ trường chung
 * bị `fieldset disabled` khi `readOnly`), và autosave của form chính không bao
 * giờ có cơ hội gửi lại `folder_ids` cũ đè lên thay đổi làm ở đây — trường này
 * không tồn tại trong `documentRecordSchema` nên `formToPayload` không đụng tới.
 */
export function DocumentFoldersCard({
  documentId,
  companyId,
  folders,
  canWrite,
}: DocumentFoldersCardProps) {
  const { can } = usePermission()
  //  Sửa thư mục phải DUYỆT ĐƯỢC cây (`FolderPicker` bên trong hộp thoại gọi
  //  `/api/doc-folders/tree`) — thiếu `doc_folder.read` thì ẩn hẳn nút, danh
  //  sách thư mục hiện tại vẫn hiện bình thường vì nó đọc từ chính văn bản,
  //  không qua API thư mục (H4, rà soát 23/09/2026).
  const canEditFolders = canWrite && can('doc_folder', 'read')
  const [open, setOpen] = useState(false)
  const [draftIds, setDraftIds] = useState<number[]>([])
  const [draftPrimary, setDraftPrimary] = useState<number | null>(null)
  const setFolders = useSetDocumentFolders(documentId)
  //  Chặn BẤM ĐÚP (CR-317) — `disabled={setFolders.isPending}` chỉ đúng ở lượt
  //  render SAU, bấm liền tay hai cái trước đó vẫn lọt cả hai lệnh PUT.
  const runOnce = useSingleFlight()

  function openEditor() {
    setDraftIds(folders.map((folder) => folder.id))
    setDraftPrimary(folders.find((folder) => folder.is_primary)?.id ?? folders[0]?.id ?? null)
    setOpen(true)
  }

  async function save() {
    await setFolders.mutateAsync({ folder_ids: draftIds, primary_id: draftPrimary })
    setOpen(false)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Folder className="size-4 text-muted-foreground" />
          Thư mục ({folders.length})
        </CardTitle>
        {canEditFolders && (
          <Button type="button" variant="outline" size="sm" onClick={openEditor}>
            <Pencil className="size-4" />
            Sửa thư mục
          </Button>
        )}
      </CardHeader>

      <CardContent>
        {folders.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa gắn thư mục nào — bấm «Sửa thư mục» để chọn.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {folders.map((folder) => (
              <li key={folder.id} className="flex min-w-0 items-center gap-2 text-sm">
                {folder.is_primary && (
                  <Star
                    className="size-3.5 shrink-0 fill-amber-400 text-amber-500"
                    aria-label="Thư mục chính"
                  />
                )}
                {/*  Đường dẫn bấm được → trang Quản lý cây thư mục (phase 05),
                     đã mở sẵn đúng thư mục qua `?folder=<id>`. */}
                <Link
                  to={appRoutes.document.folderDetail(folder.id)}
                  className="min-w-0 truncate text-primary hover:underline"
                >
                  {folder.name}
                </Link>
                {folder.is_primary && (
                  <Badge variant="outline" className="shrink-0 font-normal">
                    Chính
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sửa thư mục</DialogTitle>
            <DialogDescription>
              Gỡ thư mục cuối cùng thì văn bản tự quay về thư mục mang tên pháp nhân.
            </DialogDescription>
          </DialogHeader>

          <FolderPicker
            companyId={companyId}
            folderIds={draftIds}
            primaryFolderId={draftPrimary}
            onChange={(ids, primary) => {
              setDraftIds(ids)
              setDraftPrimary(primary)
            }}
            showEmptyHint
          />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Hủy
            </Button>
            <Button type="button" onClick={() => void runOnce(save)} disabled={setFolders.isPending}>
              Lưu
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
