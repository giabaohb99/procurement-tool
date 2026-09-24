import { TreeView } from '@/shared/tree/tree-view'
import type { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import type { TreeNode } from '@/shared/tree/tree-types'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import { FolderNodeIcon } from './folder-tree-item'
import type { DocFolderSearchResult, DocFolderTreeNode } from '../types/document-folder'

interface FolderPickerResultsProps {
  query: string
  onQueryChange: (value: string) => void
  treeNodes: TreeNode<DocFolderTreeNode>[]
  searchResults: DocFolderSearchResult[]
  selectedIds: number[]
  multiple: boolean
  expansion: ReturnType<typeof useTreeExpansion>
  onPick: (id: number) => void
}

/**
 * Nội dung popover của `folder-picker.tsx` — ô tìm + (gõ thì DANH SÁCH PHẲNG
 * kèm đường dẫn, không gõ thì CÂY). Tách riêng vì đây là phần dài nhất của ô
 * chọn thư mục, giữ tệp chính dưới 200 dòng.
 */
export function FolderPickerResults({
  query,
  onQueryChange,
  treeNodes,
  searchResults,
  selectedIds,
  multiple,
  expansion,
  onPick,
}: FolderPickerResultsProps) {
  return (
    <>
      <div className="border-b p-2">
        <Input
          autoFocus
          placeholder="Gõ tên thư mục…"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
        />
      </div>

      <div className="max-h-64 overflow-y-auto p-1">
        {query.trim() ? (
          searchResults.length === 0 ? (
            <p className="px-2 py-4 text-center text-sm text-muted-foreground">
              Không tìm thấy thư mục nào.
            </p>
          ) : (
            searchResults.map((result) => (
              <button
                key={result.id}
                type="button"
                onClick={() => onPick(result.id)}
                className={cn(
                  'flex w-full flex-col items-start gap-0.5 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                  selectedIds.includes(result.id) && 'bg-accent/50',
                )}
              >
                <span className="font-medium">{result.name}</span>
                <span className="text-xs text-muted-foreground">{result.path_display}</span>
              </button>
            ))
          )
        ) : treeNodes.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">
            Chưa có thư mục nào bạn đủ quyền chọn.
          </p>
        ) : (
          <TreeView
            nodes={treeNodes}
            ariaLabel="Cây thư mục văn bản"
            selectedId={!multiple ? (selectedIds[0] ?? null) : undefined}
            onSelect={(node) => node.data && onPick(node.data.id)}
            expandedIds={expansion.expandedIds}
            onToggleExpand={expansion.toggle}
            renderIcon={(node) => (
              <span className="shrink-0">
                {/*  Cùng icon với cây chính — mọi thư mục như nhau (chốt 24/09/2026). */}
                <FolderNodeIcon data={node.data} className="size-3.5" />
              </span>
            )}
            renderBadge={(node) =>
              node.data && multiple && selectedIds.includes(node.data.id) ? (
                <span className="text-xs text-primary" aria-hidden>
                  ✓
                </span>
              ) : null
            }
          />
        )}
      </div>
    </>
  )
}
