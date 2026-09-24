import {
  ChevronsDownUp,
  FolderPlus,
  House,
  MoreHorizontal,
  PanelLeftClose,
  RefreshCw,
  Search,
} from 'lucide-react'

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { useState, type DragEvent } from 'react'

import { cn } from '@/shared/utils/cn'

interface FolderTreePanelHeaderProps {
  /** Có thư mục đang chọn để tạo con vào đó không — chưa chọn gì thì tắt nút. */
  canCreate: boolean
  onCreate: () => void
  onCollapseAll: () => void
  onRefresh: () => void
  refreshing: boolean
  /** Chỉ có ở bản DESKTOP (`folder-tree-panel-shell.tsx`) — bản trong `Sheet` không cần, tự có nút đóng riêng. */
  onCollapsePanel?: () => void
  /** Ô lọc nhỏ đang mở/đóng — nút "Tìm" chỉ TOGGLE, `folder-tree-panel.tsx` giữ state thật. */
  searchOpen: boolean
  onToggleSearch: () => void
  includeArchived: boolean
  onIncludeArchivedChange: (value: boolean) => void
  /** «Hiện văn bản trong cây» (duoc-CR-476) — tắt thì cây chỉ còn thư mục, không tự nạp lá văn bản. */
  showDocuments: boolean
  onShowDocumentsChange: (value: boolean) => void
  /**
   * Về GỐC — bỏ chọn thư mục, khung phải hiện «Thư mục của bạn». Không có
   * đường này thì lỡ bấm vào một pháp nhân là KẸT ở đó: cây không còn chỗ nào
   * để bỏ chọn (phản hồi 24/09/2026). Bỏ trống = nhãn chỉ là chữ như cũ.
   */
  onSelectRoot?: () => void
  /** Đang đứng ở gốc (chưa chọn thư mục nào) — tô nhãn như dòng đang chọn. */
  atRoot?: boolean
  /**
   * Nhãn gốc là ĐÍCH THẢ: kéo thư mục vào đây = đưa ra gốc cây (24/09/2026).
   * Bỏ trống = nhãn không nhận thả.
   */
  rootDrop?: {
    canDrop: (event: DragEvent<HTMLElement>) => boolean
    onDrop: (event: DragEvent<HTMLElement>) => void
  }
}

/**
 * Tiêu đề khung cây kiểu VS Code Explorer: nhãn HOA nhỏ "THƯ MỤC" + nút icon
 * chỉ hiện khi rê chuột qua cả khối tiêu đề — *Tìm* (bật/tắt ô lọc gọn dưới
 * tiêu đề, `folder-tree-panel.tsx` tự vẽ ô đó), *Thư mục mới*, *Thu gọn tất
 * cả*, *Làm mới*, và menu `⋯` gom "Hiện thư mục ngừng dùng" (yêu cầu 23/09/2026
 * — bỏ ô tìm to + công tắc to luôn hiện, đúng mật độ VS Code). Tách khỏi
 * `folder-tree-panel.tsx` để tệp đó giữ dưới 200 dòng.
 */
export function FolderTreePanelHeader({
  canCreate,
  onCreate,
  onCollapseAll,
  onRefresh,
  refreshing,
  onCollapsePanel,
  searchOpen,
  onToggleSearch,
  includeArchived,
  onIncludeArchivedChange,
  showDocuments,
  onShowDocumentsChange,
  onSelectRoot,
  atRoot = false,
  rootDrop,
}: FolderTreePanelHeaderProps) {
  const [rootDragOver, setRootDragOver] = useState(false)
  return (
    <div className="group/header flex items-center justify-between gap-1 px-2 pt-2">
      {onSelectRoot ? (
        <IconTooltip label="Về «Thư mục của bạn»">
          <button
            type="button"
            onClick={onSelectRoot}
            aria-current={atRoot ? 'page' : undefined}
            onDragOver={(event) => {
              if (!rootDrop?.canDrop(event)) return
              event.preventDefault()
              setRootDragOver(true)
            }}
            onDragLeave={() => setRootDragOver(false)}
            onDrop={(event) => {
              setRootDragOver(false)
              if (!rootDrop?.canDrop(event)) return
              event.preventDefault()
              rootDrop.onDrop(event)
            }}
            className={cn(
              '-mx-1 flex items-center gap-1 rounded px-1 py-0.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase hover:bg-muted hover:text-foreground',
              atRoot && 'bg-accent text-foreground',
              rootDragOver && 'bg-accent text-foreground ring-2 ring-primary',
            )}
          >
            <House className="size-3.5" />
            Thư mục
          </button>
        </IconTooltip>
      ) : (
        <span className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          Thư mục
        </span>
      )}
      <div
        className={cn(
          'flex items-center gap-0.5 opacity-0 transition-opacity',
          //  Nút "Tìm" ĐANG BẬT thì giữ cả cụm hiện luôn (đỡ tự ẩn ngay dưới
          //  mũi con trỏ khi người dùng vừa bấm xong rồi rời chuột khỏi tiêu đề).
          (searchOpen || refreshing) && 'opacity-100',
          'group-focus-within/header:opacity-100 group-hover/header:opacity-100',
        )}
      >
        <IconTooltip label={searchOpen ? 'Đóng ô tìm' : 'Tìm thư mục'}>
          <button
            type="button"
            aria-label="Tìm thư mục"
            aria-pressed={searchOpen}
            onClick={onToggleSearch}
            className={cn(
              'flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted',
              searchOpen && 'bg-muted',
            )}
          >
            <Search className="size-3.5" />
          </button>
        </IconTooltip>
        <IconTooltip label={canCreate ? 'Thư mục mới' : 'Không có quyền tạo thư mục ở đây'}>
          <button
            type="button"
            disabled={!canCreate}
            aria-label="Thư mục mới"
            onClick={onCreate}
            className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted disabled:pointer-events-none disabled:opacity-40"
          >
            <FolderPlus className="size-3.5" />
          </button>
        </IconTooltip>
        <IconTooltip label="Thu gọn tất cả">
          <button
            type="button"
            aria-label="Thu gọn tất cả"
            onClick={onCollapseAll}
            className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
          >
            <ChevronsDownUp className="size-3.5" />
          </button>
        </IconTooltip>
        <IconTooltip label="Làm mới">
          <button
            type="button"
            aria-label="Làm mới"
            onClick={onRefresh}
            className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
          >
            <RefreshCw className={cn('size-3.5', refreshing && 'animate-spin')} />
          </button>
        </IconTooltip>

        <DropdownMenu>
          <IconTooltip label="Thêm">
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Thêm tùy chọn"
                className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
              >
                <MoreHorizontal className="size-3.5" />
              </button>
            </DropdownMenuTrigger>
          </IconTooltip>
          <DropdownMenuContent align="end">
            <DropdownMenuCheckboxItem
              checked={showDocuments}
              onCheckedChange={onShowDocumentsChange}
              onSelect={(event) => event.preventDefault()}
            >
              Hiện văn bản trong cây
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={includeArchived}
              onCheckedChange={onIncludeArchivedChange}
              onSelect={(event) => event.preventDefault()}
            >
              Hiện thư mục ngừng dùng
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {onCollapsePanel && (
          <IconTooltip label="Thu gọn khung thư mục">
            <button
              type="button"
              aria-label="Thu gọn khung thư mục"
              onClick={onCollapsePanel}
              className="flex size-6 shrink-0 items-center justify-center rounded hover:bg-muted"
            >
              <PanelLeftClose className="size-3.5" />
            </button>
          </IconTooltip>
        )}
      </div>
    </div>
  )
}
