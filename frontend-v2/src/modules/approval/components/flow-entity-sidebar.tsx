import { Plus } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { ENTITY_LABELS } from '../helpers/entity-link'
import { useApprovalFlows } from '../hooks/use-approvals'
import type { ApprovalFlow } from '../types/approval'

interface FlowEntitySidebarProps {
  /** Luồng đang mở — để tô sáng đúng dòng. */
  flowId?: number
  onTaoLuong: (entity: string) => void
}

/**
 * Cột trái: **loại chứng từ → các luồng của loại đó**.
 *
 * Đây là cách người dùng thật sự đi tìm: họ nghĩ "quy chế duyệt thế nào", không
 * nghĩ "luồng số 7 tên gì". Một danh sách phẳng toàn tên luồng bắt họ nhớ luồng
 * nào thuộc loại nào — mà đúng cái đó mới là câu họ đang hỏi.
 */
export function FlowEntitySidebar({ flowId, onTaoLuong }: FlowEntitySidebarProps) {
  const { data } = useApprovalFlows()
  const flows = data?.items ?? []

  return (
    <nav className="w-60 shrink-0 space-y-4 overflow-y-auto pr-1">
      {Object.entries(ENTITY_LABELS).map(([ma, nhan]) => {
        const cuaLoai = flows.filter((flow) => flow.entity === ma)
        return (
          <div key={ma}>
            <div className="mb-1 flex items-center justify-between gap-2">
              <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                {nhan}
              </p>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-6"
                title={`Tạo luồng cho ${nhan}`}
                aria-label={`Tạo luồng cho ${nhan}`}
                onClick={() => onTaoLuong(ma)}
              >
                <Plus className="size-3.5" />
              </Button>
            </div>

            {cuaLoai.length === 0 ? (
              <p className="px-2 text-xs text-muted-foreground">
                Chưa có luồng — chứng từ loại này đi theo đường duyệt cũ.
              </p>
            ) : (
              <ul className="space-y-0.5">
                {cuaLoai.map((flow) => (
                  <DongLuong key={flow.id} flow={flow} dangMo={flow.id === flowId} />
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </nav>
  )
}

function DongLuong({ flow, dangMo }: { flow: ApprovalFlow; dangMo: boolean }) {
  return (
    <li>
      <Link
        to={appRoutes.approval.flowDetail(flow.id)}
        className={cn(
          'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
          dangMo ? 'bg-accent font-medium' : 'hover:bg-muted',
        )}
      >
        <span className="min-w-0 flex-1 truncate">{flow.name}</span>
        <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
          {flow.node_count} bước
        </span>
        {!flow.is_active && (
          <Badge variant="outline" className="shrink-0 px-1 py-0 text-[10px] font-normal">
            Ngừng
          </Badge>
        )}
      </Link>
    </li>
  )
}
