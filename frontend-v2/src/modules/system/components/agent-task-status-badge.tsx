import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { agentTaskTone } from '../utils/agent-task-format'

/** Huy hiệu trạng thái việc của bot (ai-CR-036). Nhãn do backend dựng, màu theo nhóm nghĩa. */
export function AgentTaskStatusBadge({ status, label }: { status: number; label: string }) {
  return (
    <Badge variant="secondary" className={cn('border-0', TONE_CLASS[agentTaskTone(status)])}>
      {label}
    </Badge>
  )
}
