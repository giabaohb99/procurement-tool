import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, MyTask } from '@/modules/approval/types/approval'
import { DocumentApprovalBanner } from './document-approval-banner'

const DOCUMENT_ID = 135

//  Việc duyệt của CHÍNH người đang đọc, lấy từ hộp việc. `null` = người ngoài
//  cuộc, và đó là 9/10 lượt mở trang này.
const hopViec: { viec: MyTask | null } = { viec: null }
vi.mock('../hooks/use-my-document-approvals', () => ({
  useMyDocumentTask: () => hopViec.viec,
}))

beforeEach(() => {
  hopViec.viec = null
})

function ve(instance: ApprovalInstance | null) {
  return render(
    <MemoryRouter>
      <DocumentApprovalBanner instance={instance} documentId={DOCUMENT_ID} />
    </MemoryRouter>,
  )
}

function phien(doi: Partial<ApprovalInstance> = {}): ApprovalInstance {
  return {
    id: 7,
    entity: 'document',
    entity_id: DOCUMENT_ID,
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

function viecCuaToi(doi: Partial<MyTask> = {}): MyTask {
  return {
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
    entity: 'document',
    entity_id: DOCUMENT_ID,
    entity_code: '',
    entity_title: 'Quy chế bảo mật',
    started_by_name: 'Quản trị viên',
    instance_status: INSTANCE_STATUS.running,
    on_behalf_of_id: null,
    on_behalf_of_name: '',
    delegation_id: null,
    is_overdue: false,
    ...doi,
  }
}

describe('DocumentApprovalBanner', () => {
  it('chưa vào bộ máy duyệt thì không chen thêm băng nào', () => {
    const { container } = ve(null)
    expect(container).toBeEmptyDOMElement()
  })

  it('đang chạy thì nói rõ đang ở bước nào và chờ ai', () => {
    ve(phien())

    expect(screen.getByText(/bước 2/)).toBeInTheDocument()
    expect(screen.getByText(/Dego Admin/)).toBeInTheDocument()
  })

  it('người NGOÀI cuộc không thấy nút duyệt nào', () => {
    //  LỖI ĐÃ XẢY RA: băng nói với tất cả mọi người là "xử lý ở màn «Việc của
    //  tôi»". Màn đó chỉ liệt kê việc của CHÍNH người đăng nhập, nên người soạn
    //  bấm sang chỉ thấy trống trơn và tưởng hệ thống hỏng.
    ve(phien())

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.getByText(/Bạn không phải làm gì/)).toBeInTheDocument()
  })

  it('đúng người đang giữ việc thì duyệt được NGAY TẠI VĂN BẢN', () => {
    //  Người dùng đòi đúng câu này: "vào thẳng văn bản đó duyệt". Dẫn sang hộp
    //  việc để bấm nghĩa là ký một văn bản chưa mở ra đọc, hoặc phải đi hai vòng.
    hopViec.viec = viecCuaToi()

    ve(phien())

    expect(screen.getByText(/Đang chờ bạn duyệt/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Duyệt \/ Trả lại/ })).toBeInTheDocument()
  })

  it('bấm THAY người khác thì nói ra trước khi bấm, không phải sau', () => {
    hopViec.viec = viecCuaToi({ on_behalf_of_name: 'Trần Văn B' })

    ve(phien())

    expect(screen.getByText(/bạn bấm thay Trần Văn B/)).toBeInTheDocument()
  })

  it('duyệt xong TRỌN VẸN thì im lặng — không có gì để báo', () => {
    const { container } = ve(
      phien({ status: INSTANCE_STATUS.approved, status_label: 'Đã duyệt', tasks: [] }),
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('duyệt hết bước mà văn bản chưa ban hành được thì phải kêu lên', () => {
    //  LỖI ĐÃ XẢY RA: loại «phải kèm Quyết định» mà thiếu Quyết định thì hook
    //  ban hành ném lỗi, `entity_hooks.fire` nuốt lỗi để giữ chữ ký. Kết quả là
    //  phiên ghi «Đã duyệt», văn bản nằm lại ở *chờ duyệt* không số, và lý do
    //  chỉ nằm trong log container — không ai biết có chuyện.
    ve(
      phien({
        status: INSTANCE_STATUS.approved,
        status_label: 'Đã duyệt',
        tasks: [],
        finish_reason:
          'Đã duyệt hết các bước nhưng CHƯA hoàn tất được: Loại «Quy trình» phải ban hành kèm một Quyết định.',
      }),
    )

    expect(screen.getByText(/CHƯA ban hành/)).toBeInTheDocument()
    expect(screen.getByText(/phải ban hành kèm một Quyết định/)).toBeInTheDocument()
  })

  it('phiếu kẹt vì không có người duyệt cũng phải kêu lên', () => {
    ve(
      phien({
        status: INSTANCE_STATUS.blocked,
        status_label: 'Kẹt — không có người duyệt',
        tasks: [],
        finish_reason: 'Chặng 1: không tìm được người duyệt nào',
      }),
    )

    expect(screen.getByText(/đang kẹt/)).toBeInTheDocument()
    expect(screen.getByText(/không tìm được người duyệt/)).toBeInTheDocument()
  })
})
