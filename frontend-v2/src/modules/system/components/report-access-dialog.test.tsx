import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAccessSubjectOptions } from '@/modules/hr/hooks/use-access-subject-options'
import { useGrantReportAccess, useRevokeReportAccess } from '../hooks/use-report-access'
import type { ReportAccessGrant, ReportAccessItem } from '../types/report-access'
import { ReportAccessDialog } from './report-access-dialog'

vi.mock('../hooks/use-report-access', () => ({
  useGrantReportAccess: vi.fn(),
  useRevokeReportAccess: vi.fn(),
}))
vi.mock('@/modules/hr/hooks/use-access-subject-options', () => ({
  useAccessSubjectOptions: vi.fn(),
}))

const grantMutate = vi.fn()
const revokeMutate = vi.fn()

function grant(overrides: Partial<ReportAccessGrant> = {}): ReportAccessGrant {
  return {
    id: 1,
    subject_kind: 1,
    subject_kind_label: 'Người',
    subject_id: 1,
    subject_name: 'Người A',
    effect: 1,
    reason: '',
    valid_from: null,
    valid_to: null,
    created_at: '2026-10-02T00:00:00Z',
    ...overrides,
  }
}

function report(overrides: Partial<ReportAccessItem> = {}): ReportAccessItem {
  return {
    key: 1,
    label: 'Báo cáo mua hàng',
    group: 'Thu mua',
    grants: [],
    ...overrides,
  }
}

beforeEach(() => {
  grantMutate.mockClear()
  revokeMutate.mockClear()
  vi.mocked(useGrantReportAccess).mockReturnValue({
    mutate: grantMutate,
    isPending: false,
  } as unknown as ReturnType<typeof useGrantReportAccess>)
  vi.mocked(useRevokeReportAccess).mockReturnValue({
    mutate: revokeMutate,
    isPending: false,
  } as unknown as ReturnType<typeof useRevokeReportAccess>)
  vi.mocked(useAccessSubjectOptions).mockReturnValue({
    options: [
      { subject_kind: 1, subject_id: 1, label: 'Người Một' },
      { subject_kind: 1, subject_id: 2, label: 'Người Hai' },
    ],
    loading: false,
  })
})

describe('ReportAccessDialog', () => {
  it('report = null thì không dựng nội dung bên trong', () => {
    render(<ReportAccessDialog report={null} onOpenChange={vi.fn()} />)
    expect(
      screen.queryByText('Thêm người · phòng ban · pháp nhân · vai trò…'),
    ).not.toBeInTheDocument()
  })

  it('chưa chọn ai thì nút Thêm vô hiệu', () => {
    render(<ReportAccessDialog report={report()} onOpenChange={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Thêm' })).toBeDisabled()
  })

  it('chọn 2 chủ thể + Cấm + lý do rồi bấm Thêm → gọi gán ĐÚNG {subjects, effect: 2, reason}', async () => {
    const user = userEvent.setup()
    render(<ReportAccessDialog report={report()} onOpenChange={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Thêm người · phòng ban · pháp nhân · vai trò…' }))
    await user.click(await screen.findByText('Người Một'))
    await user.click(screen.getByText('Người Hai'))
    await user.click(screen.getByRole('radio', { name: 'Cấm' }))
    await user.type(screen.getByLabelText('Lý do'), 'Phối hợp kiểm tra')

    await user.click(screen.getByRole('button', { name: /^Thêm \(2\)$/ }))

    expect(grantMutate).toHaveBeenCalledTimes(1)
    expect(grantMutate).toHaveBeenCalledWith(
      {
        subjects: [
          { subject_kind: 1, subject_id: 1 },
          { subject_kind: 1, subject_id: 2 },
        ],
        effect: 2,
        reason: 'Phối hợp kiểm tra',
      },
      expect.anything(),
    )
  })

  it('lý do 501 ký tự bị chặn, không vượt quá 500', async () => {
    const user = userEvent.setup()
    render(<ReportAccessDialog report={report()} onOpenChange={vi.fn()} />)

    const textarea = screen.getByLabelText('Lý do') as HTMLTextAreaElement
    await user.type(textarea, 'a'.repeat(501))

    expect(textarea.value).toHaveLength(500)
    expect(screen.getByText('500/500')).toBeInTheDocument()
  })

  it('thu hồi dòng đang sống → gọi thu hồi đúng id, lý do rỗng (hộp xác nhận đã đủ để tránh bấm nhầm)', async () => {
    const user = userEvent.setup()
    render(
      <ReportAccessDialog
        report={report({ grants: [grant({ id: 42, subject_name: 'Người Cần Thu Hồi' })] })}
        onOpenChange={vi.fn()}
      />,
    )

    await user.click(screen.getByRole('button', { name: 'Thu hồi quyền của Người Cần Thu Hồi' }))
    await user.click(screen.getByRole('button', { name: 'Thu hồi' }))

    expect(revokeMutate).toHaveBeenCalledWith({ accessId: 42, reason: '' })
  })

  it('dòng Cấm hiển thị khác dòng Cho phép — khẳng định theo CHỮ, không theo class CSS', () => {
    render(
      <ReportAccessDialog
        report={report({
          grants: [
            grant({ id: 1, subject_name: 'Được xem', effect: 1 }),
            grant({ id: 2, subject_name: 'Bị cấm', effect: 2 }),
          ],
        })}
        onOpenChange={vi.fn()}
      />,
    )

    //  Khoanh vùng vào DANH SÁCH đang sống (khối 1) — khối 2 (gán thêm) cũng
    //  có radio "Cho phép"/"Cấm" riêng, khoanh vùng mới tránh trùng chữ.
    const list = screen.getByRole('list')
    expect(within(list).getByText('Cho phép')).toBeInTheDocument()
    expect(within(list).getByText('Cấm')).toBeInTheDocument()
  })

  it('chưa gán cho ai thì nói rõ, không phải một khung trống im lặng', () => {
    render(<ReportAccessDialog report={report({ grants: [] })} onOpenChange={vi.fn()} />)
    expect(screen.getByText(/Chưa gán cho ai/)).toBeInTheDocument()
  })
})
