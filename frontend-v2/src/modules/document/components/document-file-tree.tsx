import { FileText, Lock } from 'lucide-react'
import { useMemo } from 'react'

import { TreeView } from '@/shared/tree/tree-view'
import type { TreeNode } from '@/shared/tree/tree-types'
import { useTreeExpansion } from '@/shared/tree/use-tree-expansion'
import type { DocumentVersionFile } from '../api/document-api'
import { groupFilesByVersion } from '../helpers/group-files-by-version'

interface DocumentFileTreeProps {
  files: DocumentVersionFile[]
  selectedId: number | null
  onSelect: (file: DocumentVersionFile) => void
  /** id các tệp KHÔNG mở được (403 lúc xem) — đánh dấu KHÓA, không bỏ khỏi cây. */
  lockedIds?: Set<number>
  className?: string
}

function fileNode(file: DocumentVersionFile): TreeNode<DocumentVersionFile> {
  return { id: file.id, label: file.filename, data: file }
}

/**
 * CÂY TỆP của tab «Tệp» (phase 09) — nhóm theo phiên bản (*Bản 2.0 · đang
 * dùng* › tệp…; *Bản 1.0* › tệp…). Chỉ một phiên bản thì cây PHẲNG, không có
 * nút cha thừa (logic gom nằm ở `group-files-by-version.ts`, hàm thuần có
 * test riêng — component này chỉ vẽ).
 *
 * Dựng trên `shared/tree/tree-view` — cùng khối mà phase 05 (cây thư mục) sẽ
 * dùng lại, không có gì riêng của văn bản trong chính `TreeView`.
 */
export function DocumentFileTree({
  files,
  selectedId,
  onSelect,
  lockedIds,
  className,
}: DocumentFileTreeProps) {
  const grouped = useMemo(() => groupFilesByVersion(files), [files])

  const nodes = useMemo<TreeNode<DocumentVersionFile>[]>(
    () =>
      grouped.flat
        ? grouped.files.map(fileNode)
        : grouped.groups.map((group) => ({
            id: `version-${group.versionId}`,
            label: group.versionLabel,
            children: group.files.map(fileNode),
          })),
    [grouped],
  )

  //  Mở sẵn TOÀN BỘ nhánh phiên bản — số nhóm nhỏ (vài phiên bản là nhiều),
  //  không có lý do bắt người dùng bấm mở từng nhánh mới thấy tệp bên trong.
  //  `useTreeExpansion` chỉ đọc `defaultExpandedIds` ĐÚNG MỘT LẦN lúc dựng
  //  (nằm trong initializer của `useState`) nên không cần `useMemo` khóa deps
  //  ở đây — tính lại mỗi render cũng vô hại, chỉ giá trị của LẦN ĐẦU có tác dụng.
  const tree = useTreeExpansion({
    defaultExpandedIds: grouped.flat ? [] : grouped.groups.map((group) => `version-${group.versionId}`),
  })

  return (
    <TreeView
      nodes={nodes}
      ariaLabel="Cây tệp đính kèm theo phiên bản"
      selectedId={selectedId}
      onSelect={(node) => {
        if (node.data) onSelect(node.data)
      }}
      //  ↑↓ (và Home/End) ĐỔI THẲNG tệp đang xem, không đợi Enter — đúng yêu
      //  cầu «↑↓ chuyển tệp» của phase 09 (như danh sách thư/tệp quen thuộc).
      onFocusChange={(node) => {
        if (node.data) onSelect(node.data)
      }}
      expandedIds={tree.expandedIds}
      onToggleExpand={tree.toggle}
      renderIcon={(node) =>
        node.data ? (
          lockedIds?.has(node.data.id) ? (
            <Lock className="size-3.5 shrink-0 text-muted-foreground" />
          ) : (
            <FileText className="size-3.5 shrink-0 text-muted-foreground" />
          )
        ) : null
      }
      className={className}
    />
  )
}
