import { Share2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { folderAccessLevelLabel } from '../types/document-folder'
import type { DocFolderDetail } from '../types/document-folder'
import { FolderNodeIcon } from './folder-tree-item'
import { FolderViewModeControls } from './folder-view-mode-controls'

interface FolderViewToolbarProps {
  folder: DocFolderDetail
  isGrid: boolean
  onToggleGrid: (grid: boolean) => void
  detailsOpen: boolean
  onToggleDetails: () => void
  /** Mở hộp «Chia sẻ» cho THƯ MỤC ĐANG XEM (đặc tả §C, chốt lead 23/09/2026 — bỏ tab «Phân quyền», thay bằng popup). */
  onShare: () => void
}

/**
 * HÀNG 1 kiểu Drive của khung nội dung (đặc tả §P3, chốt UI 23/09/2026) —
 * icon thư mục + tên (một dòng, cắt «…») + dòng phụ «Quyền · số văn bản» bên
 * trái, «Chia sẻ» · chuyển Lưới/Danh sách · `ⓘ` bên phải (làm lại 24/09/2026:
 * bỏ huy hiệu viền, cụm nút KHÔNG bao giờ rớt dòng). Trước đây tệp này còn ôm cả nút «+ Mới» và sắp xếp — «+ Mới»
 * đã dời lên đầu khung cây trái (`folder-tree-new-menu.tsx`, Drive không lặp
 * nút tạo mới ở mọi khung), sắp xếp dời sang Hàng 2
 * (`folder-documents-filter-toolbar.tsx`, cùng hàng với ô tìm/lọc).
 *
 * Tên PHÁP LÝ đầy đủ (`folder.name`) chỉ còn ở TOOLTIP của tiêu đề — tên hiện
 * ra là `display_name` (gọn, bỏ chữ hoa/tiền tố loại hình doanh nghiệp của
 * pháp nhân) để không lặp lại y hệt breadcrumb ngay phía trên (bug lead bắt
 * 23/09/2026, xem `folder-contents-panel.tsx`).
 *
 * Segmented Danh sách/Lưới + nút khung chi tiết dùng LẠI `FolderViewModeControls`
 * — cùng khối UI với Hàng 1 của gốc «Thư mục của bạn» (`folder-my-drive-panel.tsx`).
 */
export function FolderViewToolbar({
  folder,
  isGrid,
  onToggleGrid,
  detailsOpen,
  onToggleDetails,
  onShare,
}: FolderViewToolbarProps) {
  const displayName = folder.display_name ?? folder.name
  const levelLabel = folderAccessLevelLabel(folder.my_level)

  return (
    <div className="flex items-center gap-3 border-b pb-3">
      <FolderNodeIcon data={folder} className="size-6" />

      {/*  `min-w-0 flex-1` — tên pháp nhân dài (vd «CÔNG TY TNHH PHÂN BÓN NHẬP
          KHẨU AGRICARE») tự cắt «…» chứ KHÔNG đẩy cụm nút xuống dòng riêng
          như bản cũ (`flex-wrap`, lỗi người dùng chụp 24/09/2026). */}
      <div className="min-w-0 flex-1">
        <IconTooltip label={folder.name}>
          <h2 className="truncate text-base leading-tight font-semibold">{displayName}</h2>
        </IconTooltip>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
          {levelLabel && <span>Quyền: {levelLabel}</span>}
          {levelLabel && <span aria-hidden>·</span>}
          {/*  Số TRỰC TIẾP — khớp bảng bên dưới (mặc định không gồm thư mục con). */}
          <span>{folder.document_count} văn bản</span>
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onShare}>
          <Share2 className="size-4" />
          <span className="hidden sm:inline">Chia sẻ</span>
        </Button>

        <FolderViewModeControls
          isGrid={isGrid}
          onToggleGrid={onToggleGrid}
          detailsOpen={detailsOpen}
          onToggleDetails={onToggleDetails}
        />
      </div>
    </div>
  )
}
