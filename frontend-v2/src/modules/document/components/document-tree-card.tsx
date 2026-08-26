import { FileText, FolderTree } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card'
import { useDocumentTree } from '../hooks/use-document-links'
import type { DocumentTreeNode } from '../types/document-link'
import { CloneLink, TreeNode } from './document-tree-node'

interface DocumentTreeCardProps {
  documentId: number
}

/**
 * CÂY TÀI LIỆU (E06) — mở một Quy trình thấy ngay các Hướng dẫn công việc và
 * Biểu mẫu thuộc nó, cùng các **bản riêng** đã tách cho pháp nhân con (F06).
 *
 * Cây đi theo chiều NGƯỢC của quan hệ: "Biểu mẫu thuộc về Quy trình" ghi Biểu
 * mẫu là nguồn, nên con của Quy trình chính là những văn bản trỏ vào nó. Backend
 * dựng cây (tối đa 3 cấp, có chặn lặp), giao diện chỉ vẽ.
 *
 * Hai nhánh tách thành hai NHÓM có tiêu đề riêng, không trộn chung một danh
 * sách: chúng trả lời hai câu khác hẳn nhau — *"văn bản nào thuộc về văn bản
 * này"* và *"văn bản này đã tách bản cho pháp nhân nào"*. Trộn lại thì mỗi dòng
 * phải tự giải thích mình thuộc loại gì, và cả khối thành một dải chữ dài.
 *
 * Cây bắt đầu bằng chính VĂN BẢN ĐANG MỞ. Trước đây cây vẽ thẳng từ các con:
 * mọi dòng đều thụt lề so với một cái gốc vô hình, nên không đọc ra được dòng
 * nào là con của dòng nào, mà cũng chẳng biết mình đang đứng ở đâu trong cây.
 */
export function DocumentTreeCard({ documentId }: DocumentTreeCardProps) {
  const { data: tree } = useDocumentTree(documentId)
  const children = tree?.children ?? []
  const quanHe = children.filter((node) => node.kind !== 'clone')
  const privateCopies = children.filter((node) => node.kind === 'clone')

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FolderTree className="size-4 text-muted-foreground" />
          Cây tài liệu
        </CardTitle>
        <CardDescription>
          Những văn bản nằm DƯỚI văn bản này — văn bản con theo quan hệ, và bản riêng đã tách
          cho pháp nhân con. Tối đa 3 cấp.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {tree && <TreeRoot node={tree} />}

        {children.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Chưa có văn bản nào thuộc về văn bản này, cũng chưa tách bản riêng cho pháp
            nhân con nào.
          </p>
        )}

        {quanHe.length > 0 && (
          <NhomCay tieuDe={`Văn bản thuộc về văn bản này (${quanHe.length})`}>
            {quanHe.map((node) => (
              <TreeNode key={node.id} node={node} level={0} />
            ))}
          </NhomCay>
        )}

        {privateCopies.length > 0 && (
          <NhomCay tieuDe={`Bản riêng ở pháp nhân con (${privateCopies.length})`}>
            {privateCopies.map((node) => (
              <CloneNode key={node.id} node={node} />
            ))}
          </NhomCay>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Dòng GỐC — chính văn bản đang mở, không bấm được vì bấm sẽ tự dẫn về đây.
 *
 * Có nó thì phần thụt lề bên dưới mới có mốc để so, và người dùng đọc ra ngay
 * "mình đang đứng ở đâu" thay vì phải đoán từ tiêu đề trang.
 */
function TreeRoot({ node }: { node: DocumentTreeNode }) {
  return (
    <div className="flex items-center gap-3 rounded-md border bg-muted/40 px-3 py-2">
      <FileText className="size-4 shrink-0 text-muted-foreground" />

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{node.title}</p>
        <p className="truncate text-xs text-muted-foreground">
          {[node.display_code || 'chưa cấp số', node.version_no && `bản ${node.version_no}`]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </div>

      <Badge variant="secondary" className="shrink-0 font-normal">
        đang mở
      </Badge>
    </div>
  )
}

/** Hai nhánh của cây có tiêu đề CÂN NHAU — trước đây chỉ nhánh bản riêng có. */
function NhomCay({ tieuDe, children }: { tieuDe: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1">
      <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {tieuDe}
      </h3>
      <ul className="space-y-0.5">{children}</ul>
    </section>
  )
}

/** Một BẢN RIÊNG: pháp nhân là thứ nhận diện, tiêu đề chép nguyên của gốc. */
function CloneNode({ node }: { node: DocumentTreeNode }) {
  return (
    <li>
      <CloneLink node={node} />
    </li>
  )
}
