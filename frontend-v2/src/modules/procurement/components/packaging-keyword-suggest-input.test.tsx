import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type * as PackagingCostApi from '../api/packaging-cost-api'
import { PackagingKeywordSuggestInput } from './packaging-keyword-suggest-input'

vi.mock('../api/packaging-cost-api', async (importOriginal) => ({
  ...(await importOriginal<typeof PackagingCostApi>()),
  fetchPackagingFgOptions: vi.fn(async () => [
    { code: 'HH0713', name: 'Phân bón lá Đầu Trâu 500ml' },
    { code: 'HH0714', name: 'Phân bón lá Đầu Trâu 1 lít' },
  ]),
  fetchPackagingCodeOptions: vi.fn(async () => [
    { code: 'CPT0105', name: 'Chai PET 500ml', group: 'Chai', usage: 2, new: 3000 },
  ]),
}))

function Harness() {
  const [value, setValue] = useState('')
  return (
    <>
      <PackagingKeywordSuggestInput value={value} onChange={setValue} />
      <output aria-label="keyword">{value}</output>
    </>
  )
}

describe('PackagingKeywordSuggestInput', () => {
  it('shows product / component suggestions while typing and fills the exact code on click', async () => {
    const user = userEvent.setup()
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <Harness />
      </QueryClientProvider>,
    )
    await user.type(screen.getByRole('combobox', { name: 'Tìm sản phẩm' }), 'trau')
    const option = await screen.findByRole('option', { name: /HH0714/ })
    expect(screen.getByRole('option', { name: /HH0713/ })).toBeInTheDocument()
    await user.click(option)
    expect(screen.getByLabelText('keyword')).toHaveTextContent('HH0714')
  })
})
