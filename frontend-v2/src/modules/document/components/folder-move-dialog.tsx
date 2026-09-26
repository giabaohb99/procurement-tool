import { House, TriangleAlert } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

import { TreeView } from '@/shared/tree/tree-view'
import { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import type { TreeNode } from '@/shared/tree/tree-types'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { buildFolderTree } from '../helpers/build-folder-tree'
import {
  deepestDescendantDepth,
  isValidFolderDropTarget,
  MAX_FOLDER_DEPTH,
} from '../helpers/folder-drop-target'
import { ROOT_PARENT_ID } from '../helpers/insert-temp-tree-node'
import { useMoveDocFolder } from '../hooks/use-document-folders'
import { FolderNodeIcon } from './folder-tree-item'
import type { DocFolderTreeNode } from '../types/document-folder'

interface FolderMoveDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Thư mục đang chuyển. */
  folder: DocFolderTreeNode
  /** TOÀN BỘ danh sách phẳng đang có trên cây — dùng để dựng cây đích và tính cấp sâu nhất. */
  rows: DocFolderTreeNode[]
}

/**
 * «CHUYỂN TỚI…» — chọn cha mới bằng chính cây thư mục, KHÔNG dùng dạng kéo
 * thả: đây là lối THAY THẾ cho kéo thả (xem "Rủi ro" ở phase-05), dành cho
 * bàn phím và cho lúc đích nằm ngoài màn hình đang cuộn tới.
 *
 * Đích không hợp lệ (chính nó · con cháu · khác pháp nhân · vượt 6 cấp · mức
 * dưới Đóng góp) hiện mờ và không bấm được — dùng ĐÚNG MỘT hàm thuần
 * (`isValidFolderDropTarget`) với kéo thả thật trên cây, để hai đường không
 * bao giờ lệch luật nhau.
 */
export function FolderMoveDialog({ open, onOpenChange, folder, rows }: FolderMoveDialogProps) {
  const [destinationId, setDestinationId] = useState<number | null>(null)
  const expansion = useTreeExpansion({ defaultExpandedIds: [folder.parent_id] })
  const move = useMoveDocFolder()
  const submitting = useRef(false)

  const tree = useMemo(() => buildFolderTree(rows), [rows])
  const source = useMemo(
    () => ({
      id: folder.id,
      path: folder.path,
      depth: folder.depth,
      deepestDescendantDepth: deepestDescendantDepth(rows, folder),
    }),
    [folder, rows],
  )

  const isValid = (node: TreeNode<DocFolderTreeNode>) => {
    if (!node.data) return false
    return isValidFolderDropTarget(source, {
      id: node.data.id,
      path: node.data.path,
      depth: node.data.depth,
      myLevel: node.data.my_level,
    })
  }

  //  Đích đã hợp lệ (kể cả GỐC cây, `0`), nhánh đang chuyển có văn bản mình
  //  xem được → phải hỏi lại trước khi bấm hẳn (bảng "Thấy một phần", phase-04).
  const needsConfirm = destinationId != null && folder.document_count_branch > 0
  const folderLabel = folder.display_name || folder.name
  //  Đã nằm ở gốc thì «ra gốc» là không đổi gì — khóa lựa chọn đó.
  const canMoveToRoot = folder.parent_id !== ROOT_PARENT_ID

  function reset() {
    setDestinationId(null)
  }

  function handleConfirm() {
    if (submitting.current || destinationId == null) return
    submitting.current = true
    move.mutate(
      { id: folder.id, newParentId: destinationId },
      {
        onSuccess: () => {
          submitting.current = false
          reset()
          onOpenChange(false)
        },
        onError: () => {
          submitting.current = false
        },
      },
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) reset()
        onOpenChange(next)
      }}
    >
      <DialogContent className="flex max-h-[80dvh] flex-col sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Chuyển «{folderLabel}» tới…</DialogTitle>
          <DialogDescription>
            Chọn thư mục cha mới, hoặc «Gốc cây» để đưa ra ngoài cùng. Thư mục ghi «không hợp lệ» là
            chính nó, con cháu của nó, vượt {MAX_FOLDER_DEPTH} cấp, hoặc bạn chưa đủ mức Đóng góp ở đó.
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-y-auto rounded-md border p-2">
          {/*  Mở 24/09/2026: chuyển được ra GỐC cây, không buộc theo pháp nhân. */}
          <button
            type="button"
            disabled={!canMoveToRoot}
            aria-pressed={destinationId === ROOT_PARENT_ID}
            onClick={() => setDestinationId(ROOT_PARENT_ID)}
            className={cn(
              'mb-1 flex w-full items-center gap-2 rounded px-2 py-1 text-left text-sm hover:bg-accent disabled:pointer-events-none disabled:opacity-50',
              destinationId === ROOT_PARENT_ID && 'bg-accent font-medium',
            )}
          >
            <House className="size-4 shrink-0" />
            Gốc cây
            {!canMoveToRoot && (
              <span className="ml-auto text-xs text-muted-foreground">đang ở đây</span>
            )}
          </button>
          <TreeView
            nodes={tree}
            ariaLabel="Chọn thư mục cha mới"
            selectedId={destinationId}
            expandedIds={expansion.expandedIds}
            onToggleExpand={expansion.toggle}
            onSelect={(node) => {
              if (isValid(node)) setDestinationId(Number(node.id))
            }}
            renderIcon={(node) => <FolderNodeIcon data={node.data} />}
            renderTrailing={(node) =>
              !isValid(node) ? (
                <span className="ml-auto shrink-0 text-xs text-muted-foreground">không hợp lệ</span>
              ) : null
            }
          />
        </div>

        {needsConfirm && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
            <span>
              {folder.document_count_branch} văn bản bạn xem được, và có thể còn văn bản bạn không
              xem được sẽ đi theo nhánh này.
            </span>
          </p>
        )}

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={destinationId == null || move.isPending}
          >
            Chuyển tới đây
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
