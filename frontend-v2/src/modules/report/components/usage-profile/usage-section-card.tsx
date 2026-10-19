import type { ReactNode } from 'react'

import { Card } from '@/shared/ui/card'

interface UsageSectionCardProps {
  title: string
  description?: string
  children: ReactNode
}

/** Khung chung của mỗi khối trên hồ sơ: tiêu đề, một dòng giải thích, nội dung. */
export function UsageSectionCard({ title, description, children }: UsageSectionCardProps) {
  return (
    <Card className="space-y-3 p-4">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {children}
    </Card>
  )
}
