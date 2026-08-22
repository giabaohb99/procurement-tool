import { AlertTriangle, Building2, CornerDownRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import type { DocumentTreeNode } from '../types/document-link'

/** Thụt lề mỗi cấp. Vạch dọc vẽ ở `TreeNode` bám theo đúng con số này. */
const BUOC_THUT_LE = 20

/**
 * Cảnh báo LỆCH BẢN, nói thẳng nghĩa thay vì hai chữ "lệch bản".
 *
 * Hai chữ đó là tiếng lóng nội bộ: người mở cây lần đầu không đoán được lệch
 * với cái gì, lệch thì sao, và có phải việc của mình không.
 */
function CanhBaoLechBan({ loi }: { loi: string }) {
  return (
    <span
      className="flex shrink-0 items-center gap-1 text-xs text-amber-700"
      title={loi}
    >
      <AlertTriangle className="size-3.5" />
      chưa theo bản mới
    </span>
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
export function CloneLink({ node }: { node: DocumentTreeNode }) {
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
        <CanhBaoLechBan loi="Bản gốc đã lên phiên bản mới — pháp nhân này chưa cập nhật theo." />
      )}

      <Badge variant="outline" className="shrink-0">
        {node.status_label}
      </Badge>
    </Link>
  )
}

/** Một văn bản CON theo quan hệ, đệ quy theo cấp. */
export function TreeNode({ node, level }: { node: DocumentTreeNode; level: number }) {
  return (
    <li>
      {/*  Thụt lề bằng padding theo cấp, không lồng `<ul>` nhiều tầng: lồng sâu
           thì trên màn hẹp cây bị đẩy tràn ra ngoài khung.
           Vạch dọc `border-l` để mắt lần được cấp nào thuộc cấp nào — chỉ thụt
           lề 20px thì ba cấp trông gần như một danh sách phẳng. */}
      <div
        style={{ marginLeft: level > 0 ? `${BUOC_THUT_LE}px` : undefined }}
        className={level > 0 ? 'border-l pl-2' : undefined}
      >
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
              {/*  Quan hệ để thành huy hiệu, tách khỏi số hiệu và số bản. Gộp cả
                   ba vào một dải chữ mờ thì "Hướng dẫn · DEGO-HDCV-001 · bản 1.0"
                   đọc ra như thể "Hướng dẫn" là LOẠI văn bản, trong khi nó là
                   QUAN HỆ với văn bản cha. */}
              <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                {node.relation_label && (
                  <Badge variant="secondary" className="font-normal">
                    {node.relation_label}
                  </Badge>
                )}
                <span className="truncate">
                  {[node.display_code || 'chưa cấp số', node.version_no && `bản ${node.version_no}`]
                    .filter(Boolean)
                    .join(' · ')}
                </span>
              </p>
            </div>

            {(node.needs_review || node.is_outdated) && (
              <CanhBaoLechBan loi="Văn bản cha đã đổi sau lần khai này — cần rà lại nội dung." />
            )}

            <Badge variant="outline" className="shrink-0">
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
