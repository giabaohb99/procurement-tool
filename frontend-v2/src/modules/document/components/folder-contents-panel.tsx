import { useEffect } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
import { useDocFolder } from '../hooks/use-document-folders'
import { useFolderDisplayNameLookup } from '../hooks/use-folder-display-name-lookup'
import { FolderBreadcrumb } from './folder-breadcrumb'
import { FolderDocumentsTable } from './folder-documents-table'

interface FolderContentsPanelProps {
  folderId: number
  tab: string
  onTabChange: (tab: string) => void
  onSelectFolder: (id: number) => void
  /** Văn bản CÂY vừa chỉ tới (bấm một lá) — `FolderDocumentsTable` tự chọn + mở khung chi tiết + cuộn tới đúng dòng. `null` = không có gì đang chờ xử lý. */
  selectedDocumentId?: number | null
  /** Đã xử lý xong `selectedDocumentId` — trang cha xóa tham số `?doc=` khỏi URL. */
  onDocumentHandled?: () => void
}

/**
 * KHUNG PHẢI — thư mục đang chọn. Breadcrumb ĐẦY ĐỦ từ gốc pháp nhân tới
 * chính thư mục đang xem khi KHÔNG PHẢI gốc (đặc tả §4, duoc-CR-476; chốt dọn
 * gọn lead 24/09/2026 tối: tự ẩn ở gốc pháp nhân — tiêu đề `FolderViewToolbar`
 * ngay dưới đã đủ, xem `folder-breadcrumb.tsx`) rồi khung nội dung kiểu Drive
 * (`FolderDocumentsTable`, tự vẽ tiêu đề + huy hiệu mức quyền ở Hàng 1 vì nó
 * đã có sẵn `useDocFolder(folderId)` — không truyền lặp `folder.name`/
 * `my_level` qua đây).
 *
 * ⚠️ KHÔNG còn tab «Phân quyền» (chốt lead 23/09/2026) — phân quyền nay là
 * POPUP `FolderShareDialog`, mở từ nút «Chia sẻ» / menu chuột phải / khung
 * chi tiết, tất cả nằm trong `FolderDocumentsTable`. `tab`/`onTabChange` GIỮ
 * NGUYÊN chữ ký (trang cha, `document-folder-page.tsx`, vẫn truyền hai prop
 * này) chỉ để TƯƠNG THÍCH NGƯỢC với lối vào cũ từ cây bên trái
 * (`FolderTreePanel` → `onOpenAccessTab` → `?tab=access`) — `tab === 'access'`
 * giờ chỉ còn nghĩa "mở popup Chia sẻ cho thư mục đang xem", xem
 * `use-folder-share-target.ts`. Tệp NÀY tự dọn tham số `tab` khỏi URL bằng
 * effect riêng bên dưới — `FolderDocumentsTable` chỉ đọc `openShareOnMount` để
 * mở dialog, không cần báo ngược lại.
 */
export function FolderContentsPanel({
  folderId,
  tab,
  onTabChange,
  onSelectFolder,
  selectedDocumentId,
  onDocumentHandled,
}: FolderContentsPanelProps) {
  const { data: folder, isLoading } = useDocFolder(folderId)
  const getFolderDisplayName = useFolderDisplayNameLookup()

  useEffect(() => {
    if (tab === 'access') onTabChange('documents')
  }, [tab, onTabChange])

  if (isLoading || !folder) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-5 w-64" />
        <Skeleton className="h-8 w-96" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-3 p-4">
      {/*  `folder?.breadcrumb?.` — CẢ HAI dấu `?.`: `folder` có thể tồn tại mà
          `breadcrumb` vẫn thiếu (dữ liệu lệch hợp đồng, cache cũ giữa hai lần
          đổi API — rà UI 23/09/2026 sau sự cố hộp Chia sẻ). */}
      <FolderBreadcrumb
        crumbs={folder.breadcrumb ?? []}
        onNavigate={onSelectFolder}
        getDisplayName={getFolderDisplayName}
      />

      {folder.description && <p className="text-sm text-muted-foreground">{folder.description}</p>}

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        <FolderDocumentsTable
          folderId={folderId}
          folderName={folder.display_name ?? folder.name}
          onSelectFolder={onSelectFolder}
          openShareOnMount={tab === 'access'}
          selectedDocumentId={selectedDocumentId}
          onDocumentHandled={onDocumentHandled}
        />
      </div>
    </div>
  )
}
