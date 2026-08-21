import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiPost } from '@/core/api/api-request'
import { DocumentImportButton } from './document-import-button'

vi.mock('@/core/api/api-request', () => ({ apiPost: vi.fn() }))

const imported = {
  filename: 'quy-che.docx',
  content_html: '<h1>Nội dung từ tệp</h1>',
  structural_nodes: 1,
}

beforeEach(() => {
  vi.mocked(apiPost).mockReset().mockResolvedValue(imported)
})

function renderButton(hasContent: boolean) {
  const onInsert = vi.fn().mockResolvedValue(true)
  const result = render(<DocumentImportButton hasContent={() => hasContent} onInsert={onInsert} />)
  const input = result.container.querySelector('input[type="file"]') as HTMLInputElement
  return { input, onInsert }
}

describe('chọn cách nhập tệp vào văn bản', () => {
  it('văn bản đã có nội dung thì hỏi trước và mặc định chèn tại con trỏ', async () => {
    const user = userEvent.setup()
    const { input, onInsert } = renderButton(true)

    await user.upload(input, new File(['docx'], 'quy-che.docx', { type: 'application/docx' }))

    expect(screen.getByRole('dialog', { name: 'Nhập nội dung tệp theo cách nào?' })).toBeVisible()
    expect(screen.getByRole('radio', { name: /Chèn tại vị trí con trỏ/ })).toBeChecked()
    expect(apiPost).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Chèn tại con trỏ' }))

    await waitFor(() => expect(onInsert).toHaveBeenCalledWith(imported.content_html, 'insert'))
  })

  it('cho phép chọn ghi đè toàn bộ nội dung hiện tại', async () => {
    const user = userEvent.setup()
    const { input, onInsert } = renderButton(true)

    await user.upload(input, new File(['docx'], 'quy-che.docx', { type: 'application/docx' }))
    await user.click(screen.getByRole('radio', { name: /Ghi đè toàn bộ/ }))
    await user.click(screen.getByRole('button', { name: 'Ghi đè toàn bộ' }))

    await waitFor(() => expect(onInsert).toHaveBeenCalledWith(imported.content_html, 'replace'))
  })

  it('editor rỗng thì nhập thẳng, không hiện hộp lựa chọn', async () => {
    const user = userEvent.setup()
    const { input, onInsert } = renderButton(false)

    await user.upload(input, new File(['docx'], 'quy-che.docx', { type: 'application/docx' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await waitFor(() => expect(onInsert).toHaveBeenCalledWith(imported.content_html, 'replace'))
  })
})
