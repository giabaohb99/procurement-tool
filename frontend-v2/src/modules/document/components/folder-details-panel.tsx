import { Folder, Shield, Users, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { useFolderDisplayNameLookup } from '../hooks/use-folder-display-name-lookup'
import { docCodeText, effectiveStatusBadge } from './outgoing-document-columns'
import { FOLDER_ACCESS_LEVEL, folderAccessLevelLabel } from '../types/document-folder'
import type { DocFolderDetail } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

export type FolderDetailsPanelItem =
  | { kind: 'folder'; folder: DocFolderDetail }
  | { kind: 'document'; document: DocumentRecord }
  | { kind: 'multiple'; count: number }
  | { kind: 'none' }

interface FolderDetailsPanelProps {
  item: FolderDetailsPanelItem
  onClose: () => void
  onManagePermissions?: () => void
  onOpenDocument?: () => void
}

/**
 * KHUNG CHI TIẾT bên phải kiểu Drive (đặc tả §B) — thư mục → đường dẫn, số
 * văn bản, mức quyền của tôi, tóm tắt «Ai có quyền»; văn bản → số hiệu, loại,
 * trạng thái, các thư mục chứa nó, người soạn.
 *
 * `effective_access` chỉ có nội dung khi `my_level >= Quản lý` (backend cố ý
 * để rỗng với người mức thấp hơn — xem `types/document-folder.ts`), nên khối
 * «Ai có quyền» tự ẩn khi không đủ mức thay vì hiện "0 người".
 */
export function FolderDetailsPanel({
  item,
  onClose,
  onManagePermissions,
  onOpenDocument,
}: FolderDetailsPanelProps) {
  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-l bg-card">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <h3 className="text-sm font-medium">Chi tiết</h3>
        <Button type="button" variant="ghost" size="icon-sm" onClick={onClose} aria-label="Đóng khung chi tiết">
          <X className="size-4" />
        </Button>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-3">
        {item.kind === 'none' && (
          <p className="text-sm text-muted-foreground">Chọn một thư mục hoặc văn bản để xem chi tiết.</p>
        )}

        {item.kind === 'multiple' && (
          <p className="text-sm text-muted-foreground">Đã chọn {item.count} mục.</p>
        )}

        {item.kind === 'folder' && <FolderDetails folder={item.folder} onManagePermissions={onManagePermissions} />}

        {item.kind === 'document' && (
          <DocumentDetails document={item.document} onOpenDocument={onOpenDocument} />
        )}
      </div>
    </aside>
  )
}

function FolderDetails({
  folder,
  onManagePermissions,
}: {
  folder: DocFolderDetail
  onManagePermissions?: () => void
}) {
  const canManage = folder.my_level >= FOLDER_ACCESS_LEVEL.manage
  //  Phòng thủ (rà UI 23/09/2026, cùng sự cố hộp Chia sẻ) — `effective_access`
  //  khai KHÔNG rỗng trong kiểu, nhưng dữ liệu lệch hợp đồng lúc chạy không
  //  được để `.filter` nổ thẳng ra ngoài `ErrorBoundary` gần nhất.
  const activeAccessCount = (folder.effective_access ?? []).filter((row) => row.is_active).length
  const getFolderDisplayName = useFolderDisplayNameLookup()
  const path =
    (folder.breadcrumb ?? []).map((crumb) => getFolderDisplayName(crumb.id, crumb.name)).join(' / ') ||
    (folder.display_name ?? folder.name)

  return (
    <>
      <div>
        <h4 className="flex items-center gap-1.5 font-medium" title={folder.name}>
          <Folder className="size-4 shrink-0 text-foreground" />
          <span className="truncate">{folder.display_name ?? folder.name}</span>
        </h4>
        <p className="mt-1 text-xs text-muted-foreground" title={path}>
          {path}
        </p>
      </div>

      <dl className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Số văn bản</dt>
          <dd className="tabular-nums">{folder.document_count_branch}</dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Mức quyền của tôi</dt>
          <dd>
            <Badge variant="outline">{folderAccessLevelLabel(folder.my_level)}</Badge>
          </dd>
        </div>
      </dl>

      {canManage && (
        <div className="space-y-2 rounded-md border p-2.5">
          <p className="flex items-center gap-1.5 text-sm font-medium">
            <Users className="size-4 shrink-0 text-muted-foreground" />
            Ai có quyền
          </p>
          <p className="text-xs text-muted-foreground">
            {activeAccessCount > 0
              ? `${activeAccessCount} người/nhóm đang có quyền trên nhánh này.`
              : 'Chưa khai dòng quyền riêng nào trên nhánh này.'}
          </p>
          <Button type="button" variant="outline" size="sm" className="w-full" onClick={onManagePermissions}>
            <Shield className="size-4" />
            Quản lý quyền
          </Button>
        </div>
      )}
    </>
  )
}

function DocumentDetails({
  document,
  onOpenDocument,
}: {
  document: DocumentRecord
  onOpenDocument?: () => void
}) {
  const folders = document.folders ?? []
  //  `DocumentFolderRef.name` LUÔN là tên PHÁP LÝ đầy đủ (backend chưa gộp
  //  `display_name` vào kiểu này) — tra qua cây đã nạp sẵn để khớp chữ ngắn
  //  đang dùng ở mọi nơi khác (chốt dọn gọn lead 24/09/2026 tối).
  const getFolderDisplayName = useFolderDisplayNameLookup()

  return (
    <>
      <div>
        <h4 className="line-clamp-2 font-medium">{document.title}</h4>
        <p className="mt-1 text-xs text-muted-foreground">{docCodeText(document)}</p>
      </div>

      <dl className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Loại</dt>
          <dd className="truncate">{document.doc_type_name}</dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Trạng thái</dt>
          <dd>{effectiveStatusBadge(document)}</dd>
        </div>
        <div className="flex items-center justify-between">
          <dt className="text-muted-foreground">Người soạn</dt>
          <dd className="truncate">{document.drafter_name || '—'}</dd>
        </div>
      </dl>

      <div className="space-y-1.5">
        <p className="text-sm font-medium">Thư mục chứa</p>
        {folders.length === 0 ? (
          <p className="text-xs text-muted-foreground">Không thấy thư mục nào chứa văn bản này.</p>
        ) : (
          <ul className="space-y-1">
            {folders.map((f) => (
              <li key={f.id} className="flex items-center gap-1.5 text-xs">
                <Folder className="size-3.5 shrink-0 text-muted-foreground" />
                <span className="truncate">{getFolderDisplayName(f.id, f.name)}</span>
                {f.is_primary && (
                  <Badge variant="outline" className="shrink-0 font-normal">
                    Chính
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <Button type="button" size="sm" className="w-full" onClick={onOpenDocument}>
        Mở
      </Button>
    </>
  )
}
