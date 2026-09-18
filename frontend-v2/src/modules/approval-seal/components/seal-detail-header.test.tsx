import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { TooltipProvider } from '@/shared/ui/tooltip'
import { SealDetailHeader } from './seal-detail-header'
import type { SealRequest } from '../types/seal-request'

const MOCK_REQUEST: SealRequest = {
  id: 15,
  code: 'DD015',
  title: 'Hồ sơ công bố tiêu chuẩn cơ sở phân bón vi sinh',
  purpose: 'Đóng dấu Bản tự công bố hợp chuẩn hợp quy cho dòng phân bón vi sinh mới',
  copies: 5,
  status: 2,
  status_label: 'Chờ duyệt',
  requester: 'Nguyễn Thị Phương Thảo',
  requester_role: 'Nhân sự · Sản xuất - Thử nghiệm',
  requester_email: 'thao.ntp@degoholding.vn',
  requester_phone: '0901234567',
  companies: [
    { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', tax_code: '0312345678', logo: '' },
    { id: 2, name: 'CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL', tax_code: '0312345679', logo: '' },
  ],
  created_at: '2026-09-18T10:00:00',
  company_ids: [1, 2],
  department_id: 1,
  first_approver_id: 2,
  note: 'Cần gấp trong tuần này',
  requester_id: 10,
  approver_name: '',
  approved_at: '',
  completed_by_name: '',
  completed_at: '',
  approval_running: false,
}

describe('SealDetailHeader', () => {
  it('hiển thị tiêu đề, mục đích và mã phiếu', () => {
    render(
      <TooltipProvider>
        <SealDetailHeader request={MOCK_REQUEST} onBack={vi.fn()} />
      </TooltipProvider>,
    )

    expect(
      screen.getByText('Hồ sơ công bố tiêu chuẩn cơ sở phân bón vi sinh'),
    ).toBeInTheDocument()
    expect(screen.getByText('DD015')).toBeInTheDocument()
    expect(screen.getByText('5 bản')).toBeInTheDocument()
    expect(screen.getByText('Nguyễn Thị Phương Thảo')).toBeInTheDocument()
  })
})
