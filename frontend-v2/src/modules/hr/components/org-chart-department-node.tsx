import { ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import type { OrgDepartmentNode } from '../types/org-chart'
import { OrgChartPersonTree } from './org-chart-person-tree'

interface OrgChartDepartmentNodeProps {
  node: OrgDepartmentNode
  depth?: number
}

/** Một phòng ban: đầu thẻ (tên · trưởng phòng · quân số), thân thẻ là người và các phòng con. */
export function OrgChartDepartmentNode({ node, depth = 0 }: OrgChartDepartmentNodeProps) {
  //  Mở sẵn hai tầng đầu; sâu hơn thì thu lại cho sơ đồ gọn.
  const [open, setOpen] = useState(depth < 2)
  const hasBody = node.people.length > 0 || node.children.length > 0
  const Chevron = open ? ChevronDown : ChevronRight

  return (
    <div className={cn('rounded-lg border bg-card', depth > 0 && 'mt-2')}>
      <button
        type="button"
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
        aria-expanded={open}
        disabled={!hasBody}
        onClick={() => setOpen((value) => !value)}
      >
        <Chevron className={cn('size-4 shrink-0', !hasBody && 'opacity-30')} />
        <span className="font-semibold">{node.name}</span>
        {node.head ? (
          <span className="text-muted-foreground text-sm">
            Trưởng phòng: {node.head.fullName}
          </span>
        ) : null}
        <span className="text-muted-foreground ml-auto shrink-0 text-xs">
          {node.headcount} người
        </span>
      </button>
      {open && hasBody && (
        <div className="space-y-2 border-t px-3 py-2">
          <OrgChartPersonTree people={node.people} />
          {node.children.length > 0 && (
            <div className="border-l pl-3">
              {node.children.map((child) => (
                <OrgChartDepartmentNode key={child.id} node={child} depth={depth + 1} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
