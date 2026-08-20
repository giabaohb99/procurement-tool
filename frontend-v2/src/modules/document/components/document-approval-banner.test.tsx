import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance } from '@/modules/approval/types/approval'
import { DocumentApprovalBanner } from './document-approval-banner'

//  Ai đang đọc băng — quyết định băng nói câu nào. Mặc định là người NGOÀI cuộc
//  (nhân sự 99), vì đó là 9/10 lượt mở trang này.
const dangDangNhap = { employee_id: 99 }
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: dangDangNhap }),
}))

beforeEach(() => {
  dangDangNhap.employee_id = 99
})

//  Băng có một <Link> sang «Việc của tôi», nên phải có Router context.
function ve(instance: ApprovalInstance | null) {
  return render(
    <MemoryRouter>
      <DocumentApprovalBanner instance={instance} />
    </MemoryRouter>,
  )
}

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
    const { container } = ve(null)
    expect(container).toBeEmptyDOMElement()
  })

  it('đang chạy thì nói rõ đang ở bước nào và chờ ai', () => {
    ve(phien())

    expect(screen.getByText(/bước 2/)).toBeInTheDocument()
    expect(screen.getByText(/Dego Admin/)).toBeInTheDocument()
  })

  it('người NGOÀI cuộc không bị đẩy sang một danh sách rỗng', () => {
    //  LỖI ĐÃ XẢY RA: băng nói với tất cả mọi người là "xử lý ở màn «Việc của
    //  tôi»". Màn đó chỉ liệt kê việc của CHÍNH người đăng nhập, nên người soạn
    //  bấm sang chỉ thấy trống trơn và tưởng hệ thống hỏng.
    ve(phien())

    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText(/Bạn không phải làm gì/)).toBeInTheDocument()
  })

  it('đúng người đang giữ việc thì mở thẳng được «Việc của tôi»', () => {
    dangDangNhap.employee_id = 2 // = assignee_employee_id của task đang chờ

    ve(phien())

    expect(screen.getByText(/Đang chờ bạn duyệt/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Việc của tôi/ })).toHaveAttribute(
      'href',
      '/approval/my-tasks',
    )
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
