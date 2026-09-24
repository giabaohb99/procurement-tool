import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { FolderShareSubjectPicker, type MixedSubject } from './folder-share-subject-picker'
import { SUBJECT_KIND } from '../types/document-access'

vi.mock('@/modules/hr/hooks/use-employees', () => ({ useEmployees: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-departments', () => ({ useDepartments: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-companies', () => ({ useCompanies: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-roles', () => ({ useRoles: vi.fn() }))

beforeEach(() => {
  vi.mocked(useEmployees).mockReturnValue({
    data: { items: [{ id: 1, full_name: 'Người Một' }, { id: 2, full_name: 'Người Hai' }] },
  } as unknown as ReturnType<typeof useEmployees>)
  vi.mocked(useDepartments).mockReturnValue({ data: { items: [] } } as unknown as ReturnType<typeof useDepartments>)
  vi.mocked(useCompanies).mockReturnValue({ data: { items: [] } } as unknown as ReturnType<typeof useCompanies>)
  vi.mocked(useRoles).mockReturnValue({ data: [] } as unknown as ReturnType<typeof useRoles>)
})

function Picker({ value = [], onChange = vi.fn() }: { value?: MixedSubject[]; onChange?: (v: MixedSubject[]) => void }) {
  return <FolderShareSubjectPicker value={value} onChange={onChange} />
}

describe('FolderShareSubjectPicker', () => {
  //  Bug lead bắt 23/09/2026: dòng tùy chọn từng là `<button>` bọc `Checkbox`
  //  (cũng là một `<button>`) — React cảnh báo "cannot contain a nested
  //  <button>". Rà lại bằng cách theo dõi `console.error` thật (jsdom/React
  //  in cảnh báo này qua đó) trong lúc mở popup và bấm chọn.
  it('không phát cảnh báo lồng <button> khi mở popup và chọn một dòng', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const user = userEvent.setup()
    render(<Picker />)

    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
    await user.click(await screen.findByText('Người Một'))

    const nestedButtonWarning = errorSpy.mock.calls.some((args) =>
      args.some((arg) => typeof arg === 'string' && arg.includes('cannot contain a nested')),
    )
    expect(nestedButtonWarning).toBe(false)
    errorSpy.mockRestore()
  })

  it('bấm CHUỘT vào một dòng → gọi onChange kèm đúng subject vừa chọn', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Picker onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
    await user.click(await screen.findByText('Người Một'))

    expect(onChange).toHaveBeenCalledWith([{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }])
  })

  it('điều hướng bằng BÀN PHÍM (Tab tới dòng rồi Enter) vẫn chọn được — không phụ thuộc chuột', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Picker onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
    const option = await screen.findByRole('option', { name: /Người Một/ })
    option.focus()
    await user.keyboard('{Enter}')

    expect(onChange).toHaveBeenCalledWith([{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }])
  })

  it('phím Space trên dòng đã chọn → bỏ chọn lại (khớp aria-selected)', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Picker value={[{ subject_kind: SUBJECT_KIND.employee, subject_id: 1 }]} onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
    const option = await screen.findByRole('option', { name: /Người Một/ })
    expect(option).toHaveAttribute('aria-selected', 'true')

    option.focus()
    await user.keyboard(' ')

    expect(onChange).toHaveBeenCalledWith([])
  })
})
