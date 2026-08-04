import { Fragment } from 'react'
import { Link } from 'react-router-dom'

import {
  Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList,
  BreadcrumbPage, BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import type { HelpCrumb } from '@/lib/help-tree'

// Breadcrumb "Trang chủ > Danh mục > Bài viết" cho khu người dùng.

export default function HelpBreadcrumb({ crumbs }: { crumbs: HelpCrumb[] | null }) {
  return (
    <Breadcrumb>
      <BreadcrumbList className="sm:gap-2">
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link to="/">Trang chủ</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>

        {crumbs?.map((c, i) => (
          <Fragment key={c.id}>
            <BreadcrumbSeparator />
            <BreadcrumbItem className="min-w-0">
              {i === crumbs.length - 1 ? (
                <BreadcrumbPage className="truncate font-medium text-navy">{c.title}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink asChild className="truncate">
                  <Link to={`/${c.id}`}>{c.title}</Link>
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          </Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
