import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FolderShareSubjectPicker } from './folder-share-subject-picker'
import { SUBJECT_KIND } from '../types/document-access'

//  Nhiều người hơn hẳn phòng ban — đúng tỉ lệ thật (272 người / 18 phòng ban).
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: {
      items: Array.from({ length: 40 }, (_, i) => ({ id: i + 1, full_name: `Nhân viên ${i + 1}` })),
    },
  }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({
    data: {
      items: [
        { id: 7, name: 'Kế toán', company_id: 1, is_active: true },
        { id: 8, name: 'Kế toán', company_id: 2, is_active: true },
        { id: 9, name: 'Phòng đã giải thể', company_id: 1, is_active: false },
      ],
    },
  }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({
    data: {
      items: [
        { id: 1, name: 'CÔNG TY TNHH DEGO HOLDING', short_name: 'DEGO Holding' },
        { id: 2, name: 'CÔNG TY TNHH ABA', short_name: '' },
      ],
    },
  }),
}))
vi.mock('@/modules/hr/hooks/use-roles', () => ({
  useRoles: () => ({ data: [{ id: 3, name: 'Văn thư' }] }),
}))

async function openPicker(onChange = vi.fn()) {
  const user = userEvent.setup()
  render(<FolderShareSubjectPicker value={[]} onChange={onChange} />)
  await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
  return { user, onChange }
}

//  Phản hồi 24/09/2026: 272 dòng người đứng đầu vùi mất phòng ban + pháp nhân,
//  người dùng tưởng chỉ chia sẻ được cho từng người.
describe('FolderShareSubjectPicker — chia sẻ cho phòng ban / pháp nhân', () => {
  it('lists companies and departments BEFORE people', async () => {
    await openPicker()
    const labels = screen.getAllByRole('option').map((option) => option.textContent ?? '')
    expect(labels[0]).toMatch(/DEGO Holding/)
    expect(labels.findIndex((l) => l.startsWith('Kế toán'))).toBeLessThan(
      labels.findIndex((l) => l.startsWith('Nhân viên')),
    )
  })

  it('same-name departments are told apart by their company', async () => {
    await openPicker()
    expect(screen.getByRole('option', { name: /Kế toán · DEGO Holding/ })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /Kế toán · CÔNG TY TNHH ABA/ })).toBeInTheDocument()
  })

  it('inactive departments are not offered', async () => {
    await openPicker()
    expect(screen.queryByRole('option', { name: /Phòng đã giải thể/ })).not.toBeInTheDocument()
  })

  it('kind filter shows only departments, with counts on every chip', async () => {
    const { user } = await openPicker()
    const filters = screen.getByRole('group', { name: 'Lọc theo loại' })
    expect(within(filters).getByRole('button', { name: 'Phòng ban (2)' })).toBeInTheDocument()
    expect(within(filters).getByRole('button', { name: 'Người (40)' })).toBeInTheDocument()
    await user.click(within(filters).getByRole('button', { name: 'Phòng ban (2)' }))
    expect(screen.getAllByRole('option')).toHaveLength(2)
  })

  it('picking a department emits a DEPARTMENT subject, not a person', async () => {
    const { user, onChange } = await openPicker()
    await user.click(screen.getByRole('option', { name: /Kế toán · DEGO Holding/ }))
    expect(onChange).toHaveBeenCalledWith([
      { subject_kind: SUBJECT_KIND.department, subject_id: 7 },
    ])
  })

  it('counts follow the typed keyword', async () => {
    const { user } = await openPicker()
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'ke toan')
    expect(screen.getByRole('button', { name: 'Tất cả (2)' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Người (0)' })).toBeInTheDocument()
  })
})
