import { Building2, Copy, Lock, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { ErrorBoundary } from '@/shared/ui/error-boundary'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { appRoutes } from '@/shared/constants/app-routes'
import { useDocFolder, useUpdateDocFolder } from '../hooks/use-document-folders'
import { FOLDER_ACCESS_LEVEL, FOLDER_ACCESS_LEVEL_LABELS } from '../types/document-folder'
import { FolderShareInviteForm } from './folder-share-invite-form'
import { FolderSharePeopleList } from './folder-share-people-list'

interface FolderShareDialogProps {
  folderId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Bấm tên thư mục nguồn của một dòng KẾ THỪA — mở thư mục đó (đóng hộp hiện tại). */
  onNavigateToFolder?: (folderId: number) => void
}

/** «Sao chép liên kết» ở chân hộp (đặc tả §P7) — URL TUYỆT ĐỐI để dán ra ngoài (chat, email…) vẫn mở đúng thư mục. */
function copyFolderLink(folderId: number) {
  const url = `${window.location.origin}${appRoutes.document.folderDetail(folderId)}`
  void navigator.clipboard
    .writeText(url)
    .then(() => toast.success('Đã sao chép liên kết'))
    .catch(() => toast.error('Không sao chép được liên kết — trình duyệt chặn quyền clipboard'))
}

/**
 * HỘP «CHIA SẺ» kiểu Google Drive (đặc tả §C/§P7, làm lại UI 23/09/2026) — POPUP,
 * KHÔNG còn là một tab. Ba khối: mời (`folder-share-invite-form.tsx`, chỉ
 * hiện với mức Quản lý), «Người có quyền», «Quyền chung» (icon Khóa/Tòa nhà +
 * ô chọn HIỆN ĐÚNG giá trị đang khai). Ba lối vào: nút «Chia sẻ» ở thanh trên
 * khung nội dung, mục «Chia sẻ…» trong menu chuột phải, nút «Quản lý quyền» ở
 * khung chi tiết — cả ba mở ĐÚNG một component này.
 *
 * `my_level < Quản lý` → CHỈ ĐỌC: ẩn khối mời + ô «Quyền chung» (ghi), danh
 * sách quyền hiện đúng ĐÃ NẠP được (backend cố ý trả rỗng cho người dưới mức
 * Quản lý ở `effective_access` — xem `types/document-folder.ts`), kèm câu
 * nhắc vì sao có thể chưa thấy đủ.
 *
 * ⚠️ Thân hộp bọc `ErrorBoundary` RIÊNG (rà UI 23/09/2026 — lead báo một lần
 * lỗi render ở đây làm SẬP CẢ TRANG, `errorElement` của router thay hẳn route
 * bằng «Không mở được trang»): một lỗi dựng — vd dữ liệu thiếu trường không
 * đúng hợp đồng — giờ chỉ làm rỗng ĐÚNG phần thân, khung + nút «Xong» vẫn
 * đóng được bình thường.
 */
export function FolderShareDialog({ folderId, open, onOpenChange, onNavigateToFolder }: FolderShareDialogProps) {
  const { data: folder } = useDocFolder(folderId)
  const updateFolder = useUpdateDocFolder()
  const canManage = (folder?.my_level ?? 0) >= FOLDER_ACCESS_LEVEL.manage
  //  Phòng thủ (rà UI 23/09/2026): kiểu khai `effective_access: FolderAccessEntry[]`
  //  không rỗng-hoá được NULL/UNDEFINED thật sự lọt qua lúc chạy — một dòng dữ
  //  liệu lệch hợp đồng (vd cache cũ giữa hai lần đổi API) không được để nổ
  //  ngay tại `.length`/`.map`.
  const effectiveAccess = folder?.effective_access ?? []
  const displayName = folder?.display_name ?? folder?.name ?? '…'
  //  `undefined` = «chưa đặt» (kế thừa tổ tiên) — ô chọn để TRỐNG thay vì suy
  //  diễn thành Riêng tư, đúng ý nghĩa cột `default_access` (xem
  //  `types/document-folder.ts`). Icon Khóa chỉ khi ĐÃ đặt tường minh = Riêng tư.
  const defaultAccess = folder?.default_access ?? null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[85dvh] flex-col overflow-hidden sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Chia sẻ «{displayName}»</DialogTitle>
          <DialogDescription>
            {canManage
              ? 'Chọn người, phòng ban, pháp nhân hoặc vai trò rồi cấp CÙNG một mức quyền cho cả danh sách trong một lượt.'
              : 'Bạn xem được ai đang có quyền trên thư mục này — cần mức Quản lý để chỉnh.'}
          </DialogDescription>
        </DialogHeader>

        <ErrorBoundary
          fallback={(error, reset) => (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center">
              <p className="text-sm text-destructive">Không hiện được nội dung hộp Chia sẻ.</p>
              <p className="text-xs text-muted-foreground">{error.message}</p>
              <Button type="button" variant="outline" size="sm" onClick={reset}>
                Thử lại
              </Button>
            </div>
          )}
        >
          <div className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6">
            {canManage ? (
              <FolderShareInviteForm folderId={folderId} />
            ) : (
              <p className="flex items-start gap-2 rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                <ShieldAlert className="mt-0.5 size-4 shrink-0" />
                Không đủ quyền để mời thêm người hoặc đổi «Quyền chung» trên thư mục này.
              </p>
            )}

            {canManage && folder && (
              <div className="space-y-1.5">
                <Label>Quyền chung</Label>
                <div className="flex items-center gap-2">
                  {defaultAccess === FOLDER_ACCESS_LEVEL.private ? (
                    <Lock className="size-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <Building2 className="size-4 shrink-0 text-muted-foreground" />
                  )}
                  <Select
                    value={defaultAccess != null ? String(defaultAccess) : undefined}
                    onValueChange={(value) =>
                      updateFolder.mutate({ id: folderId, payload: { default_access: Number(value) } })
                    }
                  >
                    <SelectTrigger className="flex-1" aria-label="Quyền chung — mọi người trong pháp nhân">
                      <SelectValue placeholder="Chưa đặt — kế thừa từ thư mục cha" />
                    </SelectTrigger>
                    <SelectContent>
                      {[0, 1, 2].map((value) => (
                        <SelectItem key={value} value={String(value)}>
                          {FOLDER_ACCESS_LEVEL_LABELS[value]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <p className="text-xs text-muted-foreground">
                  Áp cho người thấy nhánh pháp nhân này mà chưa có dòng quyền riêng nào ở dưới.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <h3 className="text-sm font-medium">Người có quyền truy cập {folder ? `(${effectiveAccess.length})` : ''}</h3>
              {folder && (
                <FolderSharePeopleList
                  folderId={folderId}
                  rows={effectiveAccess}
                  canManage={canManage}
                  onNavigateToFolder={onNavigateToFolder}
                />
              )}
            </div>

            <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
              <ShieldAlert className="mt-0.5 size-3.5 shrink-0" />
              Quyền thư mục không cho đọc văn bản — người được cấp vẫn chỉ thấy văn bản họ có quyền xem.
            </p>
          </div>
        </ErrorBoundary>

        <DialogFooter className="shrink-0 border-t pt-4 sm:justify-between">
          <Button type="button" variant="outline" onClick={() => copyFolderLink(folderId)}>
            <Copy className="size-4" />
            Sao chép liên kết
          </Button>
          <Button type="button" onClick={() => onOpenChange(false)}>
            Xong
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
