import { render, screen } from '@testing-library/react'
import { ClipboardCheck } from 'lucide-react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import { SEAL_STATUS, type SealRequest } from '../types/seal-request'
import { SealQueueList } from './seal-queue-list'

function makeRow(id: number, patch: Partial<SealRequest> = {}): SealRequest {
  return {
    id,
    code: `DD${String(id).padStart(3, '0')}`,
    title: `Văn bản số ${id}`,
    purpose: `Đóng dấu văn bản số ${id}`,
    copies: 1,
    status: SEAL_STATUS.pending,
    status_label: 'Chờ duyệt',
    requester: 'Võ Trọng Tín',
    requester_role: 'Nhân sự',
    requester_email: 'tin@degoholding.vn',
    requester_phone: '',
    companies: [{ id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', tax_code: '0312345678', logo: '' }],
    created_at: '2026-09-18T10:00:00',
    company_ids: [1],
    department_id: 1,
    first_approver_id: 2,
    note: '',
    requester_id: 10,
    approver_name: '',
    approved_at: '',
    completed_by_name: '',
    completed_at: '',
    approval_running: false,
    ...patch,
  }
}

function renderList(props: Partial<Parameters<typeof SealQueueList>[0]> = {}) {
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <SealQueueList
          icon={ClipboardCheck}
          title="Chờ phê duyệt"
          description="Phiếu đang chờ bạn thẩm định"
          rows={[makeRow(1)]}
          emptyMessage="Không có phiếu chờ duyệt."
          viewAllTo="/approval-seal/requests"
          {...props}
        />
      </TooltipProvider>
    </MemoryRouter>,
  )
}

describe('SealQueueList', () => {
  it('mỗi dòng là một liên kết mở thẳng chi tiết phiếu', () => {
    renderList({ rows: [makeRow(7)] })
    expect(screen.getByRole('link', { name: /DD007/ })).toHaveAttribute(
      'href',
      '/approval-seal/7',
    )
  })

  it('bày tối đa 5 dòng và nói rõ còn bao nhiêu phiếu nữa', () => {
    renderList({ rows: Array.from({ length: 9 }, (_, i) => makeRow(i + 1)) })
    expect(screen.getByText('DD005')).toBeInTheDocument()
    expect(screen.queryByText('DD006')).not.toBeInTheDocument()
    expect(screen.getByText('Còn 4 phiếu nữa')).toBeInTheDocument()
  })

  //  `total` là số của CẢ hàng đợi, máy chủ chỉ trả về vài dòng đầu — nên phần
  //  còn lại phải đếm theo nó, không đếm theo độ dài mảng.
  it('đếm phần còn lại theo tổng của máy chủ, không theo số dòng nhận được', () => {
    renderList({ rows: [makeRow(1), makeRow(2)], total: 30 })
    expect(screen.getByText('Còn 28 phiếu nữa')).toBeInTheDocument()
  })

  it('không hứa suông khi đã bày hết', () => {
    renderList({ rows: [makeRow(1), makeRow(2)] })
    expect(screen.queryByText(/Còn .* phiếu nữa/)).not.toBeInTheDocument()
  })

  it('danh sách rỗng thì nói lý do chứ không để khung trắng', () => {
    renderList({ rows: [], emptyMessage: 'Không có phiếu chờ duyệt.' })
    expect(screen.getByText('Không có phiếu chờ duyệt.')).toBeInTheDocument()
  })

  //  Ba hàng đợi theo vai trò chỉ chứa MỘT trạng thái nên huy hiệu ở đó là một
  //  cột chữ lặp lại; chỉ danh sách trộn ("Phiếu gần đây của tôi") mới bật.
  it('chỉ bày huy hiệu trạng thái khi được yêu cầu', () => {
    const { unmount } = renderList()
    expect(screen.queryByText('Chờ duyệt')).not.toBeInTheDocument()
    unmount()

    renderList({ showStatus: true })
    expect(screen.getByText('Chờ duyệt')).toBeInTheDocument()
  })

  it('phiếu chưa có tiêu đề thì lùi về mục đích, không để dòng trống', () => {
    renderList({ rows: [makeRow(3, { title: '' })] })
    expect(screen.getByText('Đóng dấu văn bản số 3')).toBeInTheDocument()
  })

  it('ngày tạo rút về ngày/tháng cho vừa dòng', () => {
    renderList({ rows: [makeRow(1, { created_at: '2026-09-18T10:00:00' })] })
    expect(screen.getByText('18/09')).toBeInTheDocument()
  })

  it('thiếu ngày tạo hoặc người tạo thì bỏ mẩu đó, không bày dấu chấm mồ côi', () => {
    renderList({ rows: [makeRow(1, { created_at: '', requester: '' })] })
    expect(screen.queryByText('·')).not.toBeInTheDocument()
  })
})
