import { Handle, Position, type NodeProps } from '@xyflow/react'
import {
  CheckCheck,
  Clock,
  Copy,
  Eye,
  FileSignature,
  GitBranch,
  MoreHorizontal,
  Plus,
  Send,
  Trash2,
  UserCheck,
  Users,
} from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import type { ApprovalNode } from '../../../types/approval'

export interface ApprovalStepNodeData {
  node: ApprovalNode
  isDefaultBranch?: boolean
  hasBranching?: boolean
  branchIndex?: number
  totalBranches?: number
  onSelect?: (nodeId: number) => void
  onDelete?: (nodeId: number) => void
  onDuplicate?: (node: ApprovalNode) => void
  onAddParallel?: (seq: number) => void
  [key: string]: unknown
}

export function ApprovalStepNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as ApprovalStepNodeData
  const node = nodeData.node

  if (!node) return null

  const isCC = node.node_kind === 2
  const isSign = node.flow_role === 2 // Ký duyệt
  const isReview = node.flow_role === 1 // Xem xét

  // Dynamic theme colors per role
  const theme = isCC
    ? {
        headerBg: 'bg-sky-500/10 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border-sky-500/20',
        icon: Send,
        handleColor: '!bg-sky-500',
      }
    : isSign
      ? {
          headerBg: 'bg-amber-500/10 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-500/20',
          icon: FileSignature,
          handleColor: '!bg-amber-500',
        }
      : isReview
        ? {
            headerBg: 'bg-purple-500/10 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border-purple-500/20',
            icon: Eye,
            handleColor: '!bg-purple-500',
          }
        : {
            headerBg: 'bg-blue-500/10 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-500/20',
            icon: UserCheck,
            handleColor: '!bg-blue-600',
          }

  const IconComponent = theme.icon

  return (
    <div
      onClick={() => nodeData.onSelect?.(node.id)}
      className={cn(
        'group relative w-[280px] cursor-pointer rounded-2xl border bg-card text-card-foreground shadow-xs transition-all duration-200 hover:shadow-md select-none',
        selected
          ? 'border-primary ring-4 ring-primary/15 shadow-lg scale-[1.02]'
          : 'border-border/80 hover:border-primary/50',
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className={cn(
          '!size-3 !-top-1.5 !border-2 !border-card transition-transform group-hover:scale-125',
          theme.handleColor,
        )}
      />

      {/* Header */}
      <div
        className={cn(
          'flex items-center justify-between border-b px-3.5 py-2.5 rounded-t-2xl',
          theme.headerBg,
        )}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="flex size-6 shrink-0 items-center justify-center rounded-lg bg-background/80 shadow-2xs">
            <IconComponent className="size-3.5" />
          </div>
          <div className="min-w-0 flex items-center gap-1.5">
            <span className="truncate text-xs font-bold tracking-tight">
              {node.flow_role_label || (isCC ? 'Thông báo (CC)' : 'Phê duyệt')}
            </span>
            <span className="rounded-md bg-background/60 px-1.5 py-0.2 text-[10px] font-semibold text-muted-foreground">
              #{node.seq}
            </span>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon"
              className="size-6 shrink-0 opacity-70 hover:opacity-100 hover:bg-background/60 rounded-md transition-opacity"
            >
              <MoreHorizontal className="size-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48 rounded-xl shadow-lg">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                nodeData.onAddParallel?.(node.seq)
              }}
              className="gap-2 text-xs font-medium text-purple-600 focus:text-purple-600 dark:text-purple-400"
            >
              <GitBranch className="size-3.5" />
              Thêm nhánh song song
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                nodeData.onDuplicate?.(node)
              }}
              className="gap-2 text-xs"
            >
              <Copy className="size-3.5" />
              Nhân bản bước
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="gap-2 text-xs text-destructive focus:text-destructive"
              onClick={(e) => {
                e.stopPropagation()
                nodeData.onDelete?.(node.id)
              }}
            >
              <Trash2 className="size-3.5" />
              Xóa bước này
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Body */}
      <div className="space-y-2.5 p-3.5">
        <div>
          <div className="flex items-center justify-between gap-1">
            <p className="text-sm font-semibold text-foreground leading-snug tracking-tight truncate">
              {node.name || `Bước ${node.seq}`}
            </p>
            {nodeData.hasBranching && (
              <span className="shrink-0 rounded-md bg-purple-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-purple-700 dark:text-purple-300">
                Nhánh {nodeData.branchIndex}/{nodeData.totalBranches}
              </span>
            )}
          </div>
          <div className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
            <Users className="size-3.5 shrink-0 text-muted-foreground/70" />
            <span className="truncate font-medium">
              {node.approver_names || node.approver_kind_label || 'Chưa phân công'}
            </span>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap items-center gap-1.5 pt-0.5 border-t border-border/40">
          {node.multi_mode_label && (
            <span className="inline-flex items-center gap-1 rounded-md bg-muted/60 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              <CheckCheck className="size-2.5" />
              {node.multi_mode_label}
            </span>
          )}

          {node.sla_hours > 0 && (
            <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-300">
              <Clock className="size-2.5" />
              {node.sla_hours}h
            </span>
          )}

          {node.condition && (
            <span className="inline-flex items-center gap-1 rounded-md bg-purple-500/10 px-2 py-0.5 text-[10px] font-medium text-purple-700 dark:text-purple-300">
              <GitBranch className="size-2.5" />
              Điều kiện
            </span>
          )}

          {node.is_default_branch && (
            <span className="inline-flex items-center rounded-md bg-muted/80 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
              Mặc định
            </span>
          )}
        </div>
      </div>

      {/* Hover Quick Action: + Nhánh song song */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          nodeData.onAddParallel?.(node.seq)
        }}
        title="Thêm nhánh duyệt song song với bước này"
        className="absolute -right-3 top-1/2 -translate-y-1/2 flex size-6 items-center justify-center rounded-full border border-purple-300 bg-card text-purple-600 opacity-0 shadow-md transition-all duration-200 hover:scale-125 hover:border-purple-600 hover:bg-purple-600 hover:text-white group-hover:opacity-100 z-10 dark:border-purple-800 dark:text-purple-400"
      >
        <Plus className="size-3.5 stroke-[2.5]" />
      </button>

      <Handle
        type="source"
        position={Position.Bottom}
        className={cn(
          '!size-3 !-bottom-1.5 !border-2 !border-card transition-transform group-hover:scale-125',
          theme.handleColor,
        )}
      />
    </div>
  )
}
