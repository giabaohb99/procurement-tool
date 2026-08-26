import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { DocumentNumberingRuleForm } from './document-numbering-rule-form'

vi.mock('../hooks/use-document-types', () => ({
  useDocumentTypes: () => ({ items: [] }),
}))

vi.mock('../hooks/use-document-books', () => ({
  useDocumentBooks: () => ({ items: [] }),
}))

vi.mock('../hooks/use-issue-codes', () => ({
  useIssueCodes: () => ({
    data: {
      companies: [],
      departments: [],
      department_companies: [],
      doc_types: [],
      books: [],
    },
    isLoading: false,
  }),
  useSaveIssueCode: () => ({ isPending: false, mutate: vi.fn() }),
}))

describe('DocumentNumberingRuleForm', () => {
  function renderForm() {
    render(
      <DocumentNumberingRuleForm
        formId="numbering-rule"
        initialDirection={1}
        onSubmit={vi.fn()}
      />,
    )
  }

  it('mở cấu hình mã phòng ban ngay tại khối mẫu số hiệu', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.click(screen.getByRole('button', { name: 'Tùy chỉnh thêm' }))

    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '{PhongBan}' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Mã riêng' })).toBeInTheDocument()
  })

  it('highlight những thẻ đang có trong mẫu', () => {
    renderForm()

    expect(screen.getByRole('button', { name: 'Số thứ tự' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Mã phòng ban' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Ngày phát hành' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
    expect(screen.getByRole('button', { name: '/' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '-' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '(' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('kéo thả thẻ vào đúng vị trí con trỏ trong mẫu', () => {
    renderForm()

    const values = new Map<string, string>()
    const dataTransfer = {
      effectAllowed: 'none',
      dropEffect: 'none',
      types: ['application/x-document-numbering-token', 'text/plain'],
      setData: vi.fn((type: string, value: string) => values.set(type, value)),
      getData: vi.fn((type: string) => values.get(type) ?? ''),
    } as unknown as DataTransfer

    const token = screen.getByRole('button', { name: 'Ngày phát hành' })
    const input = screen.getByPlaceholderText('Ví dụ: {STT}/{Nam}/{LoaiVB}')
    const position = (input as HTMLInputElement).value.indexOf('{Nam}')
    ;(input as HTMLInputElement).setSelectionRange(position, position)

    fireEvent.dragStart(token, { dataTransfer })
    fireEvent.dragOver(input, { dataTransfer })
    fireEvent.drop(input, { dataTransfer })

    expect(input).toHaveValue('{STT}/{Ngay}{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}')
    expect(token).toHaveAttribute('aria-pressed', 'true')
  })

  it('kéo thả được cả dấu phân cách vào mẫu', () => {
    renderForm()

    const values = new Map<string, string>()
    const dataTransfer = {
      effectAllowed: 'none',
      dropEffect: 'none',
      types: ['application/x-document-numbering-token', 'text/plain'],
      setData: vi.fn((type: string, value: string) => values.set(type, value)),
      getData: vi.fn((type: string) => values.get(type) ?? ''),
    } as unknown as DataTransfer

    const bracket = screen.getByRole('button', { name: '(' })
    const input = screen.getByPlaceholderText('Ví dụ: {STT}/{Nam}/{LoaiVB}')
    ;(input as HTMLInputElement).setSelectionRange(0, 0)

    fireEvent.dragStart(bracket, { dataTransfer })
    fireEvent.dragOver(input, { dataTransfer })
    fireEvent.drop(input, { dataTransfer })

    expect((input as HTMLInputElement).value).toMatch(/^\(\{STT\}/)
    expect(bracket).toHaveAttribute('aria-pressed', 'true')
  })
})
