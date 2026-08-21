import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, ApprovalTask } from '@/modules/approval/types/approval'
import { DocumentApprovalTab } from './document-approval-tab'

vi.mock('@/modules/approval/components/approval-action-dialog', () => ({
  ApprovalActionDialog: () => null,
}))

vi.mock('@/modules/approval/components/approval-trail-card', () => ({
  ApprovalTrailCard: () => <div data-testid="approval-trail" />,
}))

vi.mock('../hooks/use-my-document-approvals', () => ({
  useMyDocumentTask: () => null,
}))

function viec(doi: Partial<ApprovalTask> = {}): ApprovalTask {
  return {
    id: 11,
    instance_id: 8,
    node_seq: 1,
    node_name: 'Trưởng bộ phận duyệt nội dung',
    order_no: 1,
    assignee_employee_id: 3,
    assignee_name: 'Trưởng bộ phận (Demo)',
    status: TASK_STATUS.pending,
    status_label: 'Đang chờ',
    due_at: null,
    decided_at: null,
    ...doi,
  }
}

function phien(doi: Partial<ApprovalInstance> = {}): ApprovalInstance {
  return {
    id: 8,
    entity: 'document',
    entity_id: 212,
    entity_code: '02/2026/TB-NSHC-DEGO',
    entity_title: 'Thông báo lịch trực',
    flow_id: 4,
    flow_version: 8,
    flow_name: 'Ban hành văn bản hành chính',
    status: INSTANCE_STATUS.running,
    status_label: 'Đang chạy',
    current_seq: 1,
    started_by_name: 'Dego Admin',
    started_at: '2026-08-21T10:07:00',
    finished_at: null,
    finish_reason: '',
    steps: [
      { seq: 1, name: 'Trưởng bộ phận duyệt nội dung', branch_key: '' },
      { seq: 2, name: 'Chánh Văn phòng ký ban hành', branch_key: '' },
    ],
    tasks: [viec()],
    ...doi,
  }
}

describe('DocumentApprovalTab', () => {
  it('vẽ các chặng thành timeline dọc có rail nối và phân cấp trạng thái', () => {
    render(<DocumentApprovalTab instance={phien()} documentId={212} />)

    const timeline = screen.getByRole('list', { name: 'Các chặng phê duyệt' })
    expect(timeline.children).toHaveLength(2)
    expect(screen.getAllByTestId('approval-flow-step-rail')).toHaveLength(1)
    expect(within(timeline).getByText('Chặng 1 · Trưởng bộ phận duyệt nội dung')).toBeVisible()
    expect(within(timeline).getByText('Đang chờ')).toBeVisible()
    expect(within(timeline).getByText('Chưa tới lượt')).toBeVisible()
    expect(timeline).toHaveTextContent('Trưởng bộ phận (Demo)')
    expect(timeline).not.toHaveTextContent('—')

    expect(within(timeline).getByText(/Chặng 1/).closest('li')).toHaveAttribute(
      'aria-current',
      'step',
    )
  })

  it('đưa aria-current sang đúng chặng đang chạy sau khi chặng trước đã duyệt', () => {
    render(
      <DocumentApprovalTab
        documentId={212}
        instance={phien({
          current_seq: 2,
          tasks: [
            viec({ status: TASK_STATUS.approved, status_label: 'Đã duyệt' }),
            viec({
              id: 12,
              node_seq: 2,
              node_name: 'Chánh Văn phòng ký ban hành',
              assignee_name: 'Chánh Văn phòng',
            }),
          ],
        })}
      />,
    )

    const timeline = screen.getByRole('list', { name: 'Các chặng phê duyệt' })
    expect(within(timeline).getByText(/Chặng 1/).closest('li')).not.toHaveAttribute('aria-current')
    expect(within(timeline).getByText(/Chặng 2/).closest('li')).toHaveAttribute(
      'aria-current',
      'step',
    )
    expect(within(timeline).getByText('Đã duyệt')).toBeVisible()
  })
})
