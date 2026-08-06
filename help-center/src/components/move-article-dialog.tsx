import { useEffect, useState } from 'react'
import { FolderInput } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { moveArticle } from '@/lib/help-article-actions'
import { releaseBodyLock } from '@/lib/release-body-lock'
import { articleHeight, findNode, flattenTree, type HelpNode } from '@/lib/help-tree'

// Hộp thoại chuyển bài viết sang thư mục cha khác.
// Chỉ liệt kê thư mục cha HỢP LỆ để không phá cấu trúc 3 cấp và không tạo vòng lặp.

/** Cấp sâu nhất (0-based) — 0 mục gốc, 1 bài viết, 2 bài chi tiết. */
export const MAX_DEPTH = 2

const ROOT_VALUE = 'root'

/**
 * Thư mục cha hợp lệ cho `node`:
 * - không phải chính nó, cũng không phải bài con/cháu của nó (tránh vòng lặp)
 * - sau khi chuyển, nhánh của node vẫn không vượt quá 3 cấp
 */
export function validParents(tree: HelpNode[], node: HelpNode): { node: HelpNode; depth: number }[] {
  const height = articleHeight(node)
  return flattenTree(tree).filter(({ node: candidate, depth }) => {
    if (candidate.id === node.id) return false
    if (findNode(node.children || [], candidate.id)) return false
    return depth + 1 + height <= MAX_DEPTH
  })
}

export default function MoveArticleDialog({
  tree, node, open, onOpenChange, onMoved,
}: {
  tree: HelpNode[]
  node: HelpNode
  open: boolean
  onOpenChange: (open: boolean) => void
  onMoved: () => Promise<void> | void
}) {
  const [target, setTarget] = useState<string>(
    node.parent_id ? String(node.parent_id) : ROOT_VALUE,
  )
  const [saving, setSaving] = useState(false)

  // Hộp thoại không unmount khi đóng nữa nên phải tự đặt lại lựa chọn mỗi lần mở
  useEffect(() => {
    if (open) setTarget(node.parent_id ? String(node.parent_id) : ROOT_VALUE)
  }, [open, node.parent_id])

  const options = validParents(tree, node)
  const currentValue = node.parent_id ? String(node.parent_id) : ROOT_VALUE
  const canRoot = articleHeight(node) <= MAX_DEPTH

  const handleMove = async () => {
    const parentId = target === ROOT_VALUE ? null : parseInt(target, 10)
    if (parentId === node.parent_id) {
      onOpenChange(false)
      return
    }
    setSaving(true)
    // Đưa xuống cuối mục đích để không trùng sort_order với anh em sẵn có
    const targetSiblings = parentId === null ? tree : (findNode(tree, parentId)?.children || [])
    const ok = await moveArticle(node.id, parentId, targetSiblings.length)
    setSaving(false)
    if (ok) {
      await onMoved()
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => { onOpenChange(next); if (!next) releaseBodyLock() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderInput className="size-4 text-primary" /> Chuyển bài viết
          </DialogTitle>
          <DialogDescription>
            Chọn nơi đặt <b className="text-navy">{node.title}</b>. Danh sách chỉ hiện các mục
            không làm cấu trúc vượt quá 3 cấp.
          </DialogDescription>
        </DialogHeader>

        <Select value={target} onValueChange={setTarget}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Chọn thư mục cha..." />
          </SelectTrigger>
          <SelectContent>
            {canRoot && (
              <SelectItem value={ROOT_VALUE}>
                — Mục gốc (ngoài cùng) —
              </SelectItem>
            )}
            {options.map(({ node: candidate, depth }) => (
              <SelectItem key={candidate.id} value={String(candidate.id)}>
                {'  '.repeat(depth)}
                {depth > 0 && '└ '}
                {candidate.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {options.length === 0 && !canRoot && (
          <p className="text-sm text-muted-foreground">
            Không có nơi nào hợp lệ để chuyển bài này.
          </p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Hủy</Button>
          <Button disabled={saving || target === currentValue} onClick={handleMove}>
            {saving ? 'Đang chuyển…' : 'Chuyển'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
