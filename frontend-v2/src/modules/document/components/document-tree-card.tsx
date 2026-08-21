import { AlertTriangle, Building2, CornerDownRight, FolderTree } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { useDocumentTree } from '../hooks/use-document-links'
import type { DocumentTreeNode } from '../types/document-link'

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
 */
export function DocumentTreeCard({ documentId }: DocumentTreeCardProps) {
  const { data: tree } = useDocumentTree(documentId)
  const children = tree?.children ?? []
  const quanHe = children.filter((node) => node.kind !== 'clone')
  const banRieng = children.filter((node) => node.kind === 'clone')

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FolderTree className="size-4 text-muted-foreground" />
          Cây tài liệu
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {children.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Chưa có văn bản nào thuộc về văn bản này, cũng chưa tách bản riêng cho pháp
            nhân con nào.
          </p>
        )}

        {quanHe.length > 0 && (
          <ul className="space-y-0.5">
            {quanHe.map((node) => (
              <TreeNode key={node.id} node={node} level={0} />
            ))}
          </ul>
        )}

        {banRieng.length > 0 && (
          <section className="space-y-1">
            <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Bản riêng ở pháp nhân con ({banRieng.length})
            </h3>
            <ul className="space-y-0.5">
              {banRieng.map((node) => (
                <CloneNode key={node.id} node={node} />
              ))}
            </ul>
          </section>
        )}
      </CardContent>
    </Card>
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

/**
 * Dòng BẢN RIÊNG — dùng ở CẢ hai chỗ: nhóm "Bản riêng" ở cấp một, và lẫn trong
 * cây ở cấp sâu.
 *
 * ⚠️ Trước 20/08/2026 chỉ cấp MỘT mới tách được bản riêng ra (`children.filter`
 * chạy đúng một lần ở gốc), còn `TreeNode` đệ quy thì không hề xét `kind`. Bản
 * clone nằm sâu vì thế bị vẽ như một quan hệ thường: lấy `title` — mà tiêu đề
 * chép nguyên của gốc nên trùng hệt — rồi `relation_label` và `display_code`
 * đều rỗng. Kết quả là mấy dòng **giống hệt nhau, không tên pháp nhân, không số
 * hiệu**, không ai đoán được là gì (người dùng bắt được trên cây của văn bản 204).
 */
function CloneLink({ node }: { node: DocumentTreeNode }) {
  return (
    <Link
        to={appRoutes.document.documentDetail(node.id)}
        className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted"
      >
        <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-violet-50 text-violet-600">
          <Building2 className="size-4" />
        </span>

        {/*  `min-w-0` là bắt buộc: tên pháp nhân dài (viết hoa toàn bộ) sẽ nong
             ô flex ra và đẩy huy hiệu trạng thái tràn khỏi thẻ. */}
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{node.company_name || node.title}</p>
          <p className="truncate text-xs text-muted-foreground">
            {[
              node.display_code || 'chưa cấp số',
              node.version_no && `bản ${node.version_no}`,
              node.clone_status_label,
            ]
              .filter(Boolean)
              .join(' · ')}
          </p>
        </div>

        {node.is_outdated && (
          <span className="flex shrink-0 items-center gap-1 text-xs text-amber-700">
            <AlertTriangle className="size-3.5" />
            lệch bản
          </span>
        )}

      <Badge variant="outline" className="shrink-0">
        {node.status_label}
      </Badge>
    </Link>
  )
}

/** Một văn bản CON theo quan hệ, đệ quy theo cấp. */
function TreeNode({ node, level }: { node: DocumentTreeNode; level: number }) {
  return (
    <li>
      {/*  Thụt lề bằng padding theo cấp, không lồng `<ul>` nhiều tầng: lồng sâu
           thì trên màn hẹp cây bị đẩy tràn ra ngoài khung. */}
      <div style={{ paddingLeft: `${level * 20}px` }}>
        {/*  Bản riêng ở CẤP SÂU vẫn phải đọc ra là bản riêng — xem `CloneLink`. */}
        {node.kind === 'clone' ? (
          <CloneLink node={node} />
        ) : (
        <Link
          to={appRoutes.document.documentDetail(node.id)}
          className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-muted"
        >
          <CornerDownRight className="size-4 shrink-0 text-muted-foreground" />

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{node.title}</p>
            <p className="truncate text-xs text-muted-foreground">
              {[
                node.relation_label,
                node.display_code,
                node.version_no && `bản ${node.version_no}`,
              ]
                .filter(Boolean)
                .join(' · ')}
            </p>
          </div>

          {(node.needs_review || node.is_outdated) && (
            <AlertTriangle
              className="size-3.5 shrink-0 text-amber-700"
              aria-label="Cần rà lại"
            />
          )}

          <Badge variant="outline" className={cn('shrink-0')}>
            {node.status_label}
          </Badge>
        </Link>
        )}
      </div>

      {node.children.length > 0 && (
        <ul className="space-y-0.5">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} />
          ))}
        </ul>
      )}
    </li>
  )
}
