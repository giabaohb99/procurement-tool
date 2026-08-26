import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

function task(doi: Partial<ApprovalTask> = {}): ApprovalTask {
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

function session(doi: Partial<ApprovalInstance> = {}): ApprovalInstance {
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
    tasks: [task()],
    ...doi,
  }
}

describe('DocumentApprovalTab', () => {
  it('vẽ các chặng thành timeline dọc có rail nối và phân cấp trạng thái', () => {
    render(<DocumentApprovalTab instance={session()} documentId={212} />)

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
        instance={session({
          current_seq: 2,
          tasks: [
            task({ status: TASK_STATUS.approved, status_label: 'Đã duyệt' }),
            task({
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


  //  Ảnh người dùng gửi 24/08/2026: chặng 1 hiện BỐN dòng — ba dòng «Đã hủy»,
  //  hai dòng trùng tên nhau — và không đọc ra ai mới là người thật sự đã ký.
  //  Việc bị hủy sinh ra khi trả phiếu về một bước phía trước: bộ máy hủy việc
  //  cũ rồi mở việc mới, nên chặng đó tích lại nhiều lượt giao cho cùng những
  //  con người ấy.
  it('bỏ hẳn lượt giao việc ĐÃ HỦY, chỉ hiện người thật sự còn hiệu lực', () => {
    render(
      <DocumentApprovalTab
        documentId={212}
        instance={session({
          tasks: [
            task({ id: 1, status: TASK_STATUS.cancelled, status_label: 'Đã hủy',
                   assignee_name: 'Trưởng bộ phận (Demo)' }),
            task({ id: 2, status: TASK_STATUS.cancelled, status_label: 'Đã hủy',
                   assignee_name: 'Trưởng phòng Thu mua (Demo)' }),
            task({ id: 3, status: TASK_STATUS.approved, status_label: 'Đã duyệt',
                   assignee_name: 'Nhân viên Thu mua (Demo)' }),
          ],
        })}
      />,
    )

    expect(screen.getByText('Nhân viên Thu mua (Demo)')).toBeVisible()
    expect(screen.queryByText('Đã hủy')).not.toBeInTheDocument()
    expect(screen.queryByText('Trưởng bộ phận (Demo)')).not.toBeInTheDocument()
  })

  it('chỉ hiện MỘT người, còn lại giấu sau nút «Xem thêm»', async () => {
    const user = userEvent.setup()
    render(
      <DocumentApprovalTab
        documentId={212}
        instance={session({
          tasks: [
            task({ id: 1, status: TASK_STATUS.approved, status_label: 'Đã duyệt',
                   assignee_name: 'Người đã ký' }),
            task({ id: 2, assignee_name: 'Người còn chờ' }),
            task({ id: 3, assignee_name: 'Người nữa' }),
          ],
        })}
      />,
    )

    //  Người ĐÃ QUYẾT phải đứng đầu: câu người đọc cần là "ai ký chặng này".
    expect(screen.getByText('Người đã ký')).toBeVisible()
    expect(screen.queryByText('Người còn chờ')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Xem thêm 2 người' }))
    expect(screen.getByText('Người còn chờ')).toBeVisible()
    expect(screen.getByText('Người nữa')).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Thu gọn' }))
    expect(screen.queryByText('Người còn chờ')).not.toBeInTheDocument()
  })

  it('một người thì không bày nút xem thêm', () => {
    render(<DocumentApprovalTab documentId={212} instance={session()} />)
    expect(screen.queryByRole('button', { name: /Xem thêm/ })).not.toBeInTheDocument()
  })
})

