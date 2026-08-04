import { useOutletContext, useParams } from 'react-router-dom'

import { Skeleton } from '@/components/ui/skeleton'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { findNode } from '@/lib/help-tree'
import PortalArticle from './portal-article'
import PortalCategory from './portal-category'

// Một đường dẫn /:id phục vụ 2 loại trang (giống MISA: /ac/... là danh mục, /kb/... là bài viết):
//   - node CÓ bài con   -> trang danh mục (danh sách bài bên trong)
//   - node KHÔNG có con -> trang chi tiết bài viết
// Cây tài liệu tải ở PortalLayout nên ở đây chỉ cần tra cứu.

export default function PortalNode() {
  const { id } = useParams()
  const { tree } = useOutletContext<PortalOutletContext>()

  const nodeId = id ? parseInt(id, 10) : null
  const node = nodeId && tree.length > 0 ? findNode(tree, nodeId) : null

  // Cây chưa tải xong: chưa biết là danh mục hay bài viết
  if (tree.length === 0) {
    return (
      <div className="mx-auto max-w-7xl space-y-4 px-6 py-10">
        <Skeleton className="h-7 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    )
  }

  return node?.children?.length ? <PortalCategory node={node} /> : <PortalArticle />
}
