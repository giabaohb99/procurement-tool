import { Navigate, useOutletContext, useParams } from 'react-router-dom'

import { Skeleton } from '@/components/ui/skeleton'
import type { PortalOutletContext } from '@/layouts/portal-layout'
import { useSlugIndex } from '@/lib/help-slug'
import { findNode } from '@/lib/help-tree'
import PortalArticle from './portal-article'
import PortalCategory from './portal-category'

// Một đường dẫn /:slug phục vụ 2 loại trang (giống MISA: /ac/... là danh mục, /kb/... là bài viết):
//   - node CÓ bài con   -> trang danh mục (danh sách bài bên trong)
//   - node KHÔNG có con -> trang chi tiết bài viết
// Cây tài liệu tải ở PortalLayout nên ở đây chỉ cần tra cứu. Slug -> id tra qua SlugIndex,
// tham số dạng số vẫn nhận (link /7 cũ vẫn vào đúng bài).

export default function PortalNode() {
  const { slug } = useParams()
  const { tree } = useOutletContext<PortalOutletContext>()
  const { idOf, pathOf } = useSlugIndex()

  const nodeId = idOf(slug)
  const node = nodeId && tree.length > 0 ? findNode(tree, nodeId) : null

  // Cây chưa tải xong: chưa tra được slug, cũng chưa biết là danh mục hay bài viết
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

  // Link cũ dạng /7 -> đổi ngay sang /bao-cao-mua-hang cho thanh địa chỉ sạch
  if (node && slug && /^\d+$/.test(slug)) return <Navigate to={pathOf(node.id)} replace />

  return node?.children?.length ? <PortalCategory node={node} /> : <PortalArticle nodeId={nodeId} />
}
