import { ChevronsUpDown, FolderTree } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import { cn } from '@/shared/utils/cn'
import { buildFolderTree } from '../helpers/build-folder-tree'
import { useDocFolderSearch, useDocFolderTree } from '../hooks/use-document-folders'
import { FOLDER_KIND } from '../types/document-folder'
import { FolderPickerResults } from './folder-picker-results'

/** Sentinel «tất cả thư mục» — id thư mục thật luôn > 0, không dùng lại `0`
 * (CR-322: đừng lấy một giá trị id THẬT làm mốc "tất cả"). */
export const FOLDER_FILTER_ALL = -1

interface DocumentFolderFilterSelectProps {
  folderId: number
  onFolderIdChange: (id: number) => void
  /**
   * «Gồm cả thư mục con» — nằm Ở CHÂN popover chứ không đứng ngoài thanh công
   * cụ (đại ca chê 25/09/2026: công tắc ngoài thanh trông như đang bật trong
   * khi ô vẫn là «Tất cả thư mục», mà lúc đó nó chẳng có nghĩa gì). Bỏ trống
   * = không vẽ dòng này.
   */
  includeSubfolders?: boolean
  onIncludeSubfoldersChange?: (value: boolean) => void
  className?: string
}

/**
 * Ô LỌC «Thư mục» của bộ lọc nâng cao ở màn Văn bản (phase 06, duoc-CR-476) —
 * chọn MỘT thư mục từ CẢ CÂY (không giới hạn mức Đóng góp như `folder-picker.tsx`,
 * thứ đó phục vụ CHỌN NƠI LƯU lúc soạn văn bản; ở đây chỉ cần đọc được thư mục
 * là lọc được, đúng luật "quyền thư mục không mở quyền văn bản" — thấy thư mục
 * trong bộ lọc không có nghĩa đọc được văn bản trong đó, danh sách vẫn lọc
 * bằng quyền văn bản riêng).
 *
 * Tái dùng `FolderPickerResults` (khung tìm + cây) của `folder-picker.tsx` —
 * chỉ khác đầu vào KHÔNG lọc theo `my_level`/pháp nhân và có thêm dòng
 * «Tất cả thư mục» đứng đầu popover.
 */
export function DocumentFolderFilterSelect({
  folderId,
  onFolderIdChange,
  includeSubfolders,
  onIncludeSubfoldersChange,
  className,
}: DocumentFolderFilterSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const { can } = usePermission()
  //  Ô lọc đọc CẢ CÂY thư mục qua `/api/doc-folders/tree` — thiếu
  //  `doc_folder.read` (trên prod, D-018 — vai trò cũ chưa tự có quyền này)
  //  thì cuộc gọi ăn 403. Tắt hẳn truy vấn và ẩn ô, đúng luật CLAUDE.md "tab
  //  mượn dữ liệu phân hệ khác phải tự tắt khi thiếu quyền" (rà soát 23/09/2026, H4).
  const hasReadAccess = can('doc_folder', 'read')

  const { data: allFolders = [] } = useDocFolderTree(false, hasReadAccess)
  const { data: searchResults = [] } = useDocFolderSearch(query, hasReadAccess)
  const expansion = useTreeExpansion()

  const treeNodes = useMemo(() => buildFolderTree(allFolders), [allFolders])
  const foldersById = useMemo(() => new Map(allFolders.map((f) => [f.id, f])), [allFolders])

  if (!hasReadAccess) return null

  function pick(id: number) {
    onFolderIdChange(id)
    setOpen(false)
    setQuery('')
  }

  const selected = folderId !== FOLDER_FILTER_ALL ? foldersById.get(folderId) : undefined
  const triggerLabel = selected?.name ?? 'Tất cả thư mục'

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        //  Mở popover lần sau (không đóng bằng cách bấm chọn) thì xoá câu tìm
        //  cũ — không thì người dùng mở lại thấy danh sách phẳng của lần trước
        //  thay vì cây quen thuộc.
        if (!next) setQuery('')
        if (next) {
          for (const folder of allFolders) {
            if (folder.kind === FOLDER_KIND.company) expansion.expand(folder.id)
          }
        }
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Lọc theo thư mục"
          className={cn(
            'w-full justify-between font-normal md:w-48',
            folderId === FOLDER_FILTER_ALL && 'text-muted-foreground',
            className,
          )}
        >
          <span className="flex min-w-0 items-center gap-1.5">
            <FolderTree className="size-4 shrink-0" />
            <span className="truncate">{triggerLabel}</span>
            {selected && includeSubfolders && (
              <span className="shrink-0 text-xs text-muted-foreground">+ con</span>
            )}
          </span>
          <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-(--radix-popover-trigger-width) min-w-72 p-0">
        <button
          type="button"
          onClick={() => pick(FOLDER_FILTER_ALL)}
          className={cn(
            'flex w-full items-center rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
            folderId === FOLDER_FILTER_ALL && 'bg-accent/50 font-medium',
          )}
        >
          Tất cả thư mục
        </button>

        <FolderPickerResults
          query={query}
          onQueryChange={setQuery}
          treeNodes={treeNodes}
          searchResults={searchResults}
          selectedIds={folderId === FOLDER_FILTER_ALL ? [] : [folderId]}
          multiple={false}
          expansion={expansion}
          onPick={pick}
        />

        {onIncludeSubfoldersChange && (
          <label
            className={cn(
              'flex items-center gap-2 border-t px-3 py-2 text-sm',
              selected ? 'cursor-pointer' : 'text-muted-foreground',
            )}
          >
            <Checkbox
              checked={Boolean(includeSubfolders)}
              onCheckedChange={(checked) => onIncludeSubfoldersChange(checked === true)}
              //  Chưa chọn thư mục nào thì "gồm thư mục con" không có nghĩa gì cả.
              disabled={!selected}
            />
            Gồm cả văn bản trong thư mục con
          </label>
        )}
      </PopoverContent>
    </Popover>
  )
}
