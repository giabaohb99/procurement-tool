import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance } from '@/modules/approval/types/approval'
import { DocumentApprovalBanner } from './document-approval-banner'

function phien(doi: Partial<ApprovalInstance> = {}): ApprovalInstance {
  return {
    id: 7,
    entity: 'document',
    entity_id: 135,
    entity_code: '',
    entity_title: 'Quy chế bảo mật',
    flow_id: 19,
    flow_version: 1,
    flow_name: 'Ban hành văn bản quản trị',
    status: INSTANCE_STATUS.running,
    status_label: 'Đang chạy',
    current_seq: 2,
    started_by_name: 'Quản trị viên',
    started_at: null,
    finished_at: null,
    finish_reason: '',
    tasks: [
      {
        id: 1,
        instance_id: 7,
        node_seq: 2,
        node_name: 'Pháp chế rà soát',
        order_no: 1,
        assignee_employee_id: 2,
        assignee_name: 'Dego Admin',
        status: TASK_STATUS.pending,
        status_label: 'Đang chờ',
        due_at: null,
        decided_at: null,
      },
    ],
    ...doi,
  }
}

describe('DocumentApprovalBanner', () => {
  it('chưa vào bộ máy duyệt thì không chen thêm băng nào', () => {
    const { container } = render(<DocumentApprovalBanner instance={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('đang chạy thì nói rõ đang ở bước nào và chờ ai', () => {
    render(<DocumentApprovalBanner instance={phien()} />)

    expect(screen.getByText(/bước 2/)).toBeInTheDocument()
    expect(screen.getByText(/Dego Admin/)).toBeInTheDocument()
  })

  it('duyệt xong TRỌN VẸN thì im lặng — không có gì để báo', () => {
    const { container } = render(
      <DocumentApprovalBanner
        instance={phien({ status: INSTANCE_STATUS.approved, status_label: 'Đã duyệt', tasks: [] })}
      />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('duyệt hết bước mà văn bản chưa ban hành được thì phải kêu lên', () => {
    //  LỖI ĐÃ XẢY RA: loại «phải kèm Quyết định» mà thiếu Quyết định thì hook
    //  ban hành ném lỗi, `entity_hooks.fire` nuốt lỗi để giữ chữ ký. Kết quả là
    //  phiên ghi «Đã duyệt», văn bản nằm lại ở *chờ duyệt* không số, và lý do
    //  chỉ nằm trong log container — không ai biết có chuyện.
    render(
      <DocumentApprovalBanner
        instance={phien({
          status: INSTANCE_STATUS.approved,
          status_label: 'Đã duyệt',
          tasks: [],
          finish_reason:
            'Đã duyệt hết các bước nhưng CHƯA hoàn tất được: Loại «Quy trình» phải ban hành kèm một Quyết định.',
        })}
      />,
    )

    expect(screen.getByText(/CHƯA ban hành/)).toBeInTheDocument()
    expect(screen.getByText(/phải ban hành kèm một Quyết định/)).toBeInTheDocument()
  })

  it('phiếu kẹt vì không có người duyệt cũng phải kêu lên', () => {
    render(
      <DocumentApprovalBanner
        instance={phien({
          status: INSTANCE_STATUS.blocked,
          status_label: 'Kẹt — không có người duyệt',
          tasks: [],
          finish_reason: 'Chặng 1: không tìm được người duyệt nào',
        })}
      />,
    )

    expect(screen.getByText(/đang kẹt/)).toBeInTheDocument()
    expect(screen.getByText(/không tìm được người duyệt/)).toBeInTheDocument()
  })
})
