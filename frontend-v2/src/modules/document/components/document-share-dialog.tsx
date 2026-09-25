import { Copy, FileText, Info, ShieldAlert, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { useDocumentAccess, useDocumentPermissions } from '../hooks/use-document-access'
import { useDocumentAccessEditor } from '../hooks/use-document-access-editor'
import type { DocumentAccess } from '../types/document-access'
import type { DocumentRecord } from '../types/document-record'
import { DocumentAccessDialog } from './document-access-dialog'
import { DocumentShareAccessList } from './document-share-access-list'

/**
 * Chép đường dẫn TUYỆT ĐỐI tới trang chi tiết văn bản — cùng cách với nút của
 * hộp Chia sẻ thư mục. Liên kết không mở quyền: người nhận vẫn phải xem được.
 */
function copyDocumentLink(documentId: number) {
  const url = `${window.location.origin}${appRoutes.document.documentDetail(documentId)}`
  //  `navigator.clipboard` chỉ có ở https/localhost — mở bằng IP nội bộ qua http là không có.
  if (!navigator.clipboard) {
    toast.error('Trình duyệt không cho chép tự động — mở văn bản rồi chép địa chỉ trên thanh trình duyệt.')
    return
  }
  void navigator.clipboard
    .writeText(url)
    .then(() => toast.success('Đã sao chép liên kết'))
    .catch(() => toast.error('Không sao chép được liên kết — trình duyệt chặn quyền clipboard'))
}

interface DocumentShareDialogProps {
  document: DocumentRecord
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * HỘP «CHIA SẺ» của MỘT VĂN BẢN (yêu cầu 25/09/2026) — mở từ menu ⋮ / chuột
 * phải / nút chia sẻ trên dòng văn bản ở trang Thư mục. Bố cục cùng khuôn hộp
 * Chia sẻ của thư mục (kiểu Drive): ô mời trên cùng · danh sách người có quyền
 * riêng · ghi chú · «Sao chép liên kết» + «Xong» (bản đầu nhét nguyên thẻ «Quyền truy cập» của
 * trang chi tiết vào — đại ca chê khó nhìn).
 *
 * Quyền ghi hỏi trên ĐÚNG văn bản này (`/permissions`, một lượt gọi lúc mở
 * hộp): menu chỉ biết quyền theo vai trò, còn người bị CẤM đích danh hoặc văn
 * bản ngoài phạm vi thì ở đây chỉ còn xem. Backend vẫn tự gác lần nữa.
 */
export function DocumentShareDialog({ document, open, onOpenChange }: DocumentShareDialogProps) {
  const { data: permissions } = useDocumentPermissions(document.id)
  const { data: rows = [], isLoading } = useDocumentAccess(document.id)
  const editor = useDocumentAccessEditor(document.id)
  const [adding, setAdding] = useState(false)
  const [editing, setEditing] = useState<DocumentAccess | null>(null)
  const canWrite = Boolean(permissions?.write)
  const activeCount = rows.filter((row) => row.is_active).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[85dvh] flex-col overflow-hidden sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Chia sẻ văn bản</DialogTitle>
          <DialogDescription className="flex min-w-0 items-center gap-1.5 pr-6 font-medium text-foreground">
            <FileText className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate" title={document.title}>
              {document.title}
            </span>
          </DialogDescription>
        </DialogHeader>

        <div className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6">
          {canWrite ? (
            //  Trông như ô tìm của hộp Chia sẻ thư mục — bấm vào mở hộp khai
            //  quyền đầy đủ (nhiều đối tượng một lượt, cho phép / chặn, hạn, lý do).
            <button
              type="button"
              onClick={() => setAdding(true)}
              className="flex h-10 w-full items-center gap-2 rounded-md border border-input bg-background px-3 text-left text-sm text-muted-foreground shadow-xs transition-colors hover:bg-accent/50 focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
            >
              <UserPlus className="size-4 shrink-0" />
              Thêm người · phòng ban · pháp nhân · vai trò…
            </button>
          ) : (
            permissions && (
              <p className="flex items-start gap-2 rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                <ShieldAlert className="mt-0.5 size-4 shrink-0" />
                Bạn chỉ xem được ai đang có quyền — cần quyền sửa văn bản để chia thêm hoặc chặn.
              </p>
            )
          )}

          <div className="space-y-2">
            <h3 className="text-sm font-medium">
              Người có quyền riêng {!isLoading && `(${activeCount})`}
            </h3>
            {!isLoading && (
              <DocumentShareAccessList
                rows={rows}
                canWrite={canWrite}
                onEdit={setEditing}
                onRevoke={(row) =>
                  editor.revoke.mutate({ accessId: row.id, reason: 'Hủy từ hộp Chia sẻ' })
                }
              />
            )}
          </div>

          <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <span>
              Ngoài danh sách này, ai có phạm vi vai trò phù hợp vẫn xem được văn bản. Dòng{' '}
              <span className="font-medium text-destructive">Chặn</span> thắng mọi quyền khác.
            </span>
          </p>
        </div>

        <DialogFooter className="shrink-0 border-t pt-4 sm:justify-between">
          <Button type="button" variant="outline" onClick={() => copyDocumentLink(document.id)}>
            <Copy className="size-4" />
            Sao chép liên kết
          </Button>
          <Button type="button" onClick={() => onOpenChange(false)}>
            Xong
          </Button>
        </DialogFooter>
      </DialogContent>

      {adding && (
        <DocumentAccessDialog
          open
          onOpenChange={setAdding}
          pending={editor.grant.isPending}
          existing={rows
            .filter((row) => row.is_active)
            .map((row) => editor.toDraft(row))}
          onSubmit={async (drafts) => {
            await editor.grantAll(drafts)
            setAdding(false)
          }}
        />
      )}

      {editing && (
        <DocumentAccessDialog
          open
          onOpenChange={(next) => !next && setEditing(null)}
          pending={editor.pending}
          initial={editor.toDraft(editing)}
          onSubmit={async (drafts) => {
            await editor.saveEdit(editing, drafts)
            setEditing(null)
          }}
        />
      )}
    </Dialog>
  )
}
