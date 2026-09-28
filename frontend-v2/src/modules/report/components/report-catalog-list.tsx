import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'

import type { ReportCatalogEntry } from '../config/report-catalog'

interface ReportCatalogListProps {
  /** Báo cáo người dùng ĐỌC ĐƯỢC — lọc quyền là việc của trang gọi. */
  reports: ReportCatalogEntry[]
}

/**
 * «Danh sách báo cáo» kiểu Haravan: mỗi phân hệ một thẻ, mỗi báo cáo một dòng
 * bấm được (biểu tượng · tên · mô tả · mũi tên).
 */
export function ReportCatalogList({ reports }: ReportCatalogListProps) {
  const groups = new Map<string, ReportCatalogEntry[]>()
  for (const r of reports) groups.set(r.group, [...(groups.get(r.group) ?? []), r])

  if (groups.size === 0) return null

  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-semibold text-navy dark:text-foreground">Danh sách báo cáo</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {[...groups].map(([group, items]) => (
          <Card key={group} className="min-w-0 gap-2">
            <CardHeader className="pb-0">
              <CardTitle className="text-base text-navy dark:text-foreground">{group}</CardTitle>
            </CardHeader>
            <CardContent className="px-2">
              <ul className="divide-y">
                {items.map((r) => (
                  <li key={r.path}>
                    <Link
                      to={r.path}
                      className="group flex items-center gap-3 rounded-md px-3 py-2.5 hover:bg-row-hover"
                    >
                      <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
                        <r.icon className="size-4" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block font-medium">{r.label}</span>
                        <span className="block truncate text-sm text-muted-foreground">
                          {r.description}
                        </span>
                      </span>
                      <ChevronRight className="size-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
                    </Link>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}
