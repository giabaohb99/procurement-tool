import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import type { OrgPersonNode } from '../types/org-chart'

interface OrgChartPersonTreeProps {
  people: readonly OrgPersonNode[]
  /** Độ sâu hiện tại (đệ quy nội bộ) — quyết định có đường kẻ thụt vào hay không. */
  depth?: number
}

/** Cây quản lý trực tiếp trong một phòng: cấp dưới thụt vào dưới người quản lý. */
export function OrgChartPersonTree({ people, depth = 0 }: OrgChartPersonTreeProps) {
  if (people.length === 0) return null
  return (
    <ul className={depth === 0 ? 'space-y-1' : 'mt-1 space-y-1 border-l pl-4'}>
      {people.map((person) => (
        <li key={person.id}>
          <div className="flex flex-wrap items-center gap-x-2 text-sm">
            <Link
              to={appRoutes.hr.employeeDetail(person.id)}
              className="font-medium hover:underline"
            >
              {person.fullName}
            </Link>
            {person.isHead && <Badge variant="secondary">Trưởng phòng</Badge>}
            {person.position && (
              <span className="text-muted-foreground">{person.position}</span>
            )}
            <span className="text-muted-foreground text-xs">{person.code}</span>
          </div>
          <OrgChartPersonTree people={person.reports} depth={depth + 1} />
        </li>
      ))}
    </ul>
  )
}
