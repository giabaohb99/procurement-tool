import { AlertTriangle, CornerDownRight, FolderTree } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { useDocumentTree } from '../hooks/use-document-links'
import type { DocumentTreeNode } from '../types/document-link'

interface DocumentTreeCardProps {
  documentId: number
}

/**
 * CÂY TÀI LIỆU (E06) — mở một Quy trình thấy ngay các Hướng dẫn công việc và
 * Biểu mẫu thuộc nó, mỗi cái kèm trạng thái và phiên bản.
 *
 * Cây đi theo chiều NGƯỢC của quan hệ: "Biểu mẫu thuộc về Quy trình" ghi Biểu
 * mẫu là nguồn, nên con của Quy trình chính là những văn bản trỏ vào nó. Backend
 * dựng cây (tối đa 3 cấp, có chặn lặp), giao diện chỉ vẽ.
 */
export function DocumentTreeCard({ documentId }: DocumentTreeCardProps) {
  const { data: tree } = useDocumentTree(documentId)
  const children = tree?.children ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FolderTree className="size-4 text-muted-foreground" />
          Cây tài liệu
        </CardTitle>
      </CardHeader>
      <CardContent>
        {children.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa có văn bản nào thuộc về văn bản này.
          </p>
        ) : (
          <ul className="space-y-1">
            {children.map((node) => (
              <TreeNode key={node.id} node={node} level={0} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function TreeNode({ node, level }: { node: DocumentTreeNode; level: number }) {
  return (
    <li>
      {/*  Thụt lề bằng padding theo cấp, không lồng `<ul>` nhiều tầng: lồng sâu
           thì trên màn hẹp cây bị đẩy tràn ra ngoài khung. */}
      <div
        className="flex flex-wrap items-center gap-2 py-1.5 text-sm"
        style={{ paddingLeft: `${level * 20}px` }}
      >
        <CornerDownRight className="size-3.5 shrink-0 text-muted-foreground" />
        {node.relation_label && (
          <span className="text-xs text-muted-foreground">{node.relation_label}</span>
        )}
        <Link
          to={appRoutes.document.documentDetail(node.id)}
          className="font-medium hover:underline"
        >
          {node.display_code ? `${node.display_code} · ` : ''}
          {node.title}
        </Link>
        <Badge variant="outline">{node.status_label}</Badge>
        {node.version_no && (
          <span className="text-xs text-muted-foreground">Bản {node.version_no}</span>
        )}
        {(node.needs_review || node.is_outdated) && (
          <AlertTriangle className="size-3.5 text-amber-700" aria-label="Cần rà lại" />
        )}
      </div>

      {node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </ul>
      )}
    </li>
  )
}
