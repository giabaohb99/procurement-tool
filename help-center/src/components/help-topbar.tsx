import HelpBreadcrumb from '@/components/help-breadcrumb'
import HelpSearchBox from '@/components/help-search-box'
import type { HelpCrumb } from '@/lib/help-tree'

// Dải nền xám full-width dưới header: breadcrumb trái, ô tìm kiếm phải.
// Dùng ở trang danh mục và trang chi tiết bài viết.

export default function HelpTopBar({ crumbs }: { crumbs: HelpCrumb[] | null }) {
  return (
    <div className="border-b bg-muted/60">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-4 md:flex-row md:items-center md:gap-6">
        <div className="min-w-0 flex-1">
          <HelpBreadcrumb crumbs={crumbs} />
        </div>
        <HelpSearchBox className="w-full md:w-80" placeholder="Nhập nội dung tìm kiếm..." />
      </div>
    </div>
  )
}
