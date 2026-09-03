import { render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApprovalTrailCard } from './approval-trail-card'
import { ACTION, INSTANCE_STATUS, TASK_STATUS, type ApprovalTrail } from '../types/approval'

const { mockUseApprovalTrail } = vi.hoisted(() => ({
  mockUseApprovalTrail: vi.fn(),
}))

vi.mock('../hooks/use-approvals', () => ({
  useApprovalTrail: mockUseApprovalTrail,
}))

const TRAIL: ApprovalTrail = {
  instance: {
    id: 8,
    entity: 'document',
    entity_id: 196,
    entity_code: 'VB-196',
    entity_title: 'Quy định hành chính',
    flow_id: 2,
    flow_version: 8,
    flow_name: 'Ban hành văn bản hành chính',
    status: INSTANCE_STATUS.running,
    status_label: 'Đang chạy',
    current_seq: 1,
    started_by_name: 'Dego Admin',
    started_at: '2026-08-21T02:15:00Z',
    finished_at: null,
    finish_reason: '',
  },
  lines: [
    {
      id: 1,
      node_seq: 0,
      node_name: '',
      action: ACTION.start,
      action_label: 'Bắt đầu trình duyệt',
      actor_name: 'Dego Admin',
      on_behalf_of_name: '',
      delegation_id: null,
      comment: 'Trình duyệt theo luồng phiên bản 8',
      created_at: '2026-08-21T02:15:00Z',
      sentence: 'Dego Admin — Bắt đầu trình duyệt',
    },
    {
      id: 2,
      node_seq: 1,
      node_name: 'Trưởng bộ phận duyệt nội dung',
      action: ACTION.approve,
      action_label: 'Duyệt',
      actor_name: 'Nguyễn An',
      on_behalf_of_name: 'Trần Bình',
      delegation_id: 42,
      comment: 'Nội dung đã đủ căn cứ để ban hành.',
      created_at: '2026-08-21T03:30:00Z',
      sentence: 'Nguyễn An duyệt thay Trần Bình theo ủy quyền số 42',
    },
  ],
  tasks: [
    {
      id: 9,
      instance_id: 8,
      node_seq: 1,
      node_name: 'Trưởng bộ phận duyệt nội dung',
      order_no: 1,
      assignee_employee_id: 4,
      assignee_name: 'Trưởng bộ phận (Demo)',
      status: TASK_STATUS.pending,
      status_label: 'Đang chờ',
      due_at: '2026-08-22T10:00:00Z',
      decided_at: null,
    },
  ],
}

describe('ApprovalTrailCard', () => {
  beforeEach(() => {
    mockUseApprovalTrail.mockReturnValue({ data: TRAIL, isLoading: false })
  })

  it('hiện timeline chi tiết theo người, hành động, chặng, thời gian và ý kiến', () => {
    render(<ApprovalTrailCard instanceId={8} />)

    expect(screen.getByText('Lịch sử phê duyệt')).toBeInTheDocument()
    //  KHÔNG còn dòng đếm "N mốc đã ghi nhận": con số trôi ra mép phải và không
    //  nói thêm được gì so với chính danh sách ngay dưới nó.
    expect(screen.queryByText(/mốc đã ghi nhận/)).not.toBeInTheDocument()
    //  KHÔNG còn dải tóm tắt 4 ô: bốn nhãn đó nói lại đúng thứ dòng thời gian
    //  ngay dưới đã nói, nhưng bằng từ của bộ máy nên người đọc phải dịch.
    expect(screen.queryByText('Luồng xử lý')).not.toBeInTheDocument()
    expect(screen.queryByText('Người trình')).not.toBeInTheDocument()
    expect(screen.queryByText('Vị trí hiện tại')).not.toBeInTheDocument()
    expect(screen.queryByText('Phiên bản 8')).not.toBeInTheDocument()
    expect(screen.getByText('đã duyệt')).toBeInTheDocument()
    expect(screen.getAllByText('Chặng 1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Trưởng bộ phận duyệt nội dung').length).toBeGreaterThan(0)
    expect(screen.getByText('Nội dung đã đủ căn cứ để ban hành.')).toBeInTheDocument()
    expect(screen.getByText(/Thực hiện thay/)).toHaveTextContent(
      'Thực hiện thay Trần Bình · Theo ủy quyền #42',
    )
    expect(screen.getAllByText(/21\/08\/2026/).length).toBeGreaterThan(0)
    const rails = screen.getAllByTestId('approval-timeline-rail')
    expect(rails).toHaveLength(2)
    rails.forEach((rail) => {
      expect(rail).toHaveClass('approval-timeline-rail')
    })
  })

  it('đặt người đang chờ lên đầu rồi xếp thao tác từ mới nhất về cũ nhất', () => {
    render(<ApprovalTrailCard instanceId={8} />)

    const timeline = screen.getByRole('list', { name: 'Các mốc phê duyệt' })
    const pending = within(timeline).getByRole('region', { name: 'Đang chờ phản hồi' })
    const approved = within(timeline).getByRole('article', { name: 'Nguyễn An đã duyệt' })
    const started = within(timeline).getByRole('article', {
      name: 'Dego Admin đã bắt đầu trình duyệt',
    })

    expect(
      pending.compareDocumentPosition(approved) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(
      approved.compareDocumentPosition(started) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(screen.getByText('Trưởng bộ phận (Demo)')).toBeInTheDocument()
    expect(screen.getByText(/Hạn xử lý:/)).toBeInTheDocument()
    expect(screen.queryByText('Chi tiết')).not.toBeInTheDocument()
  })

  it('ý kiến dài không dấu cách phải BẺ ĐƯỢC, không đẩy tràn thẻ', () => {
    //  Lỗi thật, dựng lại được trên giao diện 03/09/2026: lý do hủy 420 ký tự
    //  liền không khoảng trắng làm đoạn chữ rộng 3139px nằm trong khung 768px,
    //  đè lên cột bên cạnh và sinh thanh cuộn ngang cho cả trang.
    //  `whitespace-pre-wrap` một mình KHÔNG đủ — nó chỉ xuống dòng ở chỗ có
    //  khoảng trắng, mà chuỗi này không có chỗ nào.
    const dai = 'Lydobitraveratdaikhongcodaucachnaoca'.repeat(12)
    mockUseApprovalTrail.mockReturnValue({
      data: { ...TRAIL, lines: [{ ...TRAIL.lines[1], comment: dai }] },
      isLoading: false,
    })

    render(<ApprovalTrailCard instanceId={8} />)

    expect(screen.getByText(dai)).toHaveClass('break-words')
  })

  it('nêu rõ nguyên nhân khi luồng bị kẹt', () => {
    mockUseApprovalTrail.mockReturnValue({
      data: {
        ...TRAIL,
        instance: {
          ...TRAIL.instance,
          status: INSTANCE_STATUS.blocked,
          status_label: 'Bị kẹt',
          finish_reason: 'Không tìm được người duyệt phù hợp.',
        },
      },
      isLoading: false,
    })

    render(<ApprovalTrailCard instanceId={8} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Luồng đang bị kẹt')
    expect(screen.getByRole('alert')).toHaveTextContent('Không tìm được người duyệt phù hợp.')
  })
})
