import { ChevronsUpDown } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import { cn } from '@/shared/utils/cn'
import { buildFolderTree } from '../helpers/build-folder-tree'
import { defaultFolderHint } from '../helpers/default-folder-hint'
import { useDocFolderSearch, useDocFolderTree } from '../hooks/use-document-folders'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderChipList } from './folder-chip-list'
import { FolderPickerResults } from './folder-picker-results'
import { FolderQuickCreateForm } from './folder-quick-create-form'

interface FolderPickerProps {
  /** `0`/bỏ trống = không lọc theo pháp nhân (Thiết lập loại văn bản dùng chế độ này). */
  companyId?: number
  folderIds: number[]
  primaryFolderId: number | null
  onChange: (folderIds: number[], primaryFolderId: number | null) => void
  /** `false` = chỉ chọn MỘT thư mục, chọn tiếp thì THAY THẾ chứ không cộng dồn. Mặc định `true`. */
  multiple?: boolean
  /** Hiện câu «Không chọn → vào thư mục …» khi rỗng — chỉ có nghĩa ở chế độ nhiều. */
  showEmptyHint?: boolean
  /** Thư mục mặc định của LOẠI văn bản đang chọn — chỉ dùng để DỰNG CÂU gợi ý, không tự áp. */
  docTypeDefaultFolderId?: number | null
  disabled?: boolean
  placeholder?: string
  className?: string
}

/**
 * Ô «Lưu vào thư mục» — popover có ô tìm (gõ thì tìm phẳng kèm đường dẫn,
 * không gõ thì hiện CÂY, xem `folder-picker-results.tsx`), dùng ở màn tạo văn
 * bản (nhiều, lọc theo pháp nhân) và ở ô «Thư mục mặc định» của Thiết lập
 * loại văn bản (một, mọi pháp nhân).
 *
 * Chỉ liệt kê thư mục mức hiệu lực ≥ ĐÓNG GÓP — `my_level` đọc thẳng từ
 * `GET /tree`/`GET /search` (phase 06, gắn thêm ở backend), KHÔNG tự suy quyền
 * ở client (luật "giao diện không tự tính quyền" của phase 04).
 *
 * Component THUẦN KIỂM SOÁT (controlled): không tự theo dõi "người dùng đã tự
 * chọn hay chưa" — việc áp mặc định theo loại văn bản và gỡ thư mục khi đổi
 * pháp nhân do NƠI GỌI (`document-main-info-fields.tsx`) quyết định, vì chỉ nơi
 * đó biết được sự kiện "loại vừa đổi" / "pháp nhân vừa đổi" theo đúng nhịp.
 */
export function FolderPicker({
  companyId = 0,
  folderIds,
  primaryFolderId,
  onChange,
  multiple = true,
  showEmptyHint = false,
  docTypeDefaultFolderId,
  disabled,
  placeholder = 'Chọn thư mục…',
  className,
}: FolderPickerProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  const { can } = usePermission()
  //  Ô này đọc CẢ CÂY thư mục qua `/api/doc-folders/tree` — thiếu
  //  `doc_folder.read` (trên prod, D-018 — vai trò cũ chưa tự có quyền này)
  //  thì cuộc gọi ăn 403. Tắt hẳn truy vấn và ẩn cả ô, đúng luật CLAUDE.md "tab
  //  mượn dữ liệu phân hệ khác phải tự tắt khi thiếu quyền" (rà soát 23/09/2026, H4).
  const hasReadAccess = can('doc_folder', 'read')
  const { data: allFolders = [] } = useDocFolderTree(false, hasReadAccess)
  const { data: searchResults = [] } = useDocFolderSearch(query, hasReadAccess)
  const expansion = useTreeExpansion()

  //  Thư mục PHÁP NHÂN luôn mở sẵn — ô chọn này chỉ phục vụ soạn văn bản, không
  //  phải trang Quản lý cây thư mục (phase 05): bắt bấm thêm một cái chevron
  //  mới thấy thư mục con là thừa một thao tác cho việc làm thường xuyên nhất.
  //  Chỉ THÊM vào tập đang mở, không bao giờ tự đóng lại thư mục người dùng đã
  //  gập tay — `expand()` bỏ qua nếu id đã có trong tập, nên gọi lại mỗi khi
  //  `allFolders` đổi là an toàn.
  useEffect(() => {
    for (const folder of allFolders) {
      if (folder.kind === FOLDER_KIND.company) expansion.expand(folder.id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `expansion.expand` ổn định (useCallback không phụ thuộc)
  }, [allFolders])

  //  KHÔNG còn lọc theo pháp nhân của văn bản (bỏ 24/09/2026 — gắn văn bản vào
  //  thư mục nào cũng được, backend cũng đã nới). `companyId` chỉ còn dùng để
  //  mở sẵn gốc pháp nhân và gợi ý thư mục mặc định.
  const isSelectable = (f: { my_level: number }) => f.my_level >= FOLDER_ACCESS_LEVEL.contribute

  const treeNodes = useMemo(() => buildFolderTree(allFolders.filter(isSelectable)), [allFolders])
  const foldersById = useMemo(() => new Map(allFolders.map((f) => [f.id, f])), [allFolders])
  const matchedSearch = useMemo(() => searchResults.filter(isSelectable), [searchResults])

  //  Thiếu quyền đọc thư mục thì ẨN HẲN ô chọn — không có gì để duyệt, và
  //  không tự nói được văn bản sẽ vào thư mục nào (tên thư mục cũng nằm sau
  //  cùng API này) nên không có câu gợi ý nào thay được (H4). Đặt SAU mọi hook
  //  ở trên — luật hook không được gọi có điều kiện.
  if (!hasReadAccess) return null

  const companyRoot = companyId
    ? allFolders.find((f) => f.kind === FOLDER_KIND.company && f.company_id === companyId)
    : undefined
  const canCreateFolder = Boolean(companyRoot) && can('doc_folder', 'create')

  /** Gỡ MỘT thư mục khỏi lựa chọn — thư mục CHÍNH bị gỡ thì phần tử kế tiếp lên thay. */
  function removeFolder(id: number) {
    const nextIds = folderIds.filter((existing) => existing !== id)
    const nextPrimary = primaryFolderId === id ? (nextIds[0] ?? null) : primaryFolderId
    onChange(nextIds, nextPrimary)
  }

  /** Bấm một thư mục trong cây/kết quả tìm — chế độ MỘT thì THAY THẾ, chế độ NHIỀU thì bật/tắt. */
  function pick(id: number) {
    if (!multiple) {
      onChange([id], id)
      setOpen(false)
      return
    }
    if (folderIds.includes(id)) removeFolder(id)
    else onChange([...folderIds, id], primaryFolderId ?? id)
  }

  const chipItems = folderIds
    .map((id) => foldersById.get(id))
    .filter((f): f is DocFolderTreeNode => Boolean(f))
    .map((f) => ({ id: f.id, name: f.name }))

  const hint =
    showEmptyHint && folderIds.length === 0 && companyId
      ? defaultFolderHint(allFolders, companyId, docTypeDefaultFolderId)
      : null

  const triggerLabel =
    folderIds.length === 0
      ? placeholder
      : multiple
        ? `${folderIds.length} thư mục đã chọn`
        : (chipItems[0]?.name ?? placeholder)

  return (
    <div className={cn('space-y-2', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={disabled}
            className={cn(
              'w-full justify-between font-normal',
              folderIds.length === 0 && 'text-muted-foreground',
            )}
          >
            <span className="truncate">{triggerLabel}</span>
            <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>

        <PopoverContent align="start" className="w-(--radix-popover-trigger-width) min-w-72 p-0">
          <FolderPickerResults
            query={query}
            onQueryChange={setQuery}
            treeNodes={treeNodes}
            searchResults={matchedSearch}
            selectedIds={folderIds}
            multiple={multiple}
            expansion={expansion}
            onPick={pick}
          />

          {canCreateFolder && companyRoot && (
            <div className="border-t p-2">
              <FolderQuickCreateForm
                parentFolderId={companyRoot.id}
                onCreated={(created) =>
                  multiple
                    ? onChange([...folderIds, created.id], primaryFolderId ?? created.id)
                    : onChange([created.id], created.id)
                }
              />
            </div>
          )}
        </PopoverContent>
      </Popover>

      {chipItems.length > 0 && (
        <FolderChipList
          items={chipItems}
          primaryId={multiple ? primaryFolderId : null}
          disabled={disabled}
          onRemove={removeFolder}
          onSetPrimary={multiple ? (id) => onChange(folderIds, id) : undefined}
        />
      )}

      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  )
}
