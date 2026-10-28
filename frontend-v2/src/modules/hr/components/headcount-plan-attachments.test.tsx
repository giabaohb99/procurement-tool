import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { HeadcountPlanAttachments } from './headcount-plan-attachments'

const card = vi.fn()
vi.mock('@/modules/procurement/components/document-attachments-card', () => ({
  DocumentAttachmentsCard: (props: Record<string, unknown>) => {
    card(props)
    return <div>thẻ tệp</div>
  },
}))

describe('plan attachments', () => {
  it('never mounts the file card when files are hidden — /api/attachments would 403 on open', () => {
    card.mockClear()
    render(<HeadcountPlanAttachments planId={6} hidden canManage />)
    expect(screen.getByText('Tệp đính kèm chỉ hiện với người được xem lương của pháp nhân này.')).toBeInTheDocument()
    expect(card).not.toHaveBeenCalled()
  })

  it('uses the shared attachment card with entity headcount_plan otherwise', () => {
    card.mockClear()
    render(<HeadcountPlanAttachments planId={6} hidden={false} canManage={false} />)
    expect(card).toHaveBeenCalledWith({ entity: 'headcount_plan', entityId: 6, canManage: false })
  })
})
