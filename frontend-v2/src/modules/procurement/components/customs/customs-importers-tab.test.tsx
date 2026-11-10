// duoc-CR-744 — bảng xếp hạng doanh nghiệp (Giá thị trường > Doanh nghiệp) đã tải đủ 20 dòng nên xếp ngay trên
// trình duyệt: bấm tiêu đề cột phải đổi thứ tự dòng, ô trống luôn xuống cuối. Chặn ở tầng `@/core/api`.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import type { CustomsFilters } from '../../types/customs'
import { CustomsImportersTab } from './customs-importers-tab'

const ITEM = { share: 0.5, wavg: 3, last_date: '2026-01-02' }

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async (url: string) => {
      if (url.endsWith('/importers')) {
        return {
          unit: 'KGM',
          units: [{ unit: 'KGM', count: 4 }],
          total_importers: 4,
          items: [
            { importer_id: 1, name: 'Công ty Mu', tax_code: '0200', count: 30, qty: 900, ...ITEM },
            { importer_id: 2, name: 'Công ty Alpha', tax_code: '0100', count: 5, qty: 100, ...ITEM },
            { importer_id: 3, name: '', tax_code: '0300', count: 12, qty: 700, ...ITEM, wavg: null },
            { importer_id: 4, name: 'Công ty Zeta', tax_code: '0400', count: 12, qty: 300, ...ITEM, wavg: 9 },
          ],
        }
      }
      throw new Error(`Không mock đường ${url}`)
    },
  }
})

const FILTERS = { q: 'abamectin' } as unknown as CustomsFilters

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CustomsImportersTab filters={FILTERS} onPickImporter={() => undefined} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Mã số thuế theo thứ tự dòng đang hiện — đủ để nhận ra thứ tự mà không phụ thuộc cách hiển thị tên. */
function shownTaxCodes() {
  const body = screen.getAllByRole('rowgroup')[1]
  return within(body)
    .getAllByRole('row')
    .map((row) => within(row).getAllByRole('cell').map((cell) => cell.textContent ?? ''))
    .map((cells) => cells.find((text) => /^0\d{3}$/.test(text)) ?? '')
}

const header = (text: string | RegExp) => screen.findByText(text, { selector: 'thead span' })

describe('CustomsImportersTab — sắp xếp cột', () => {
  it('keeps the ranking order until a header is clicked', async () => {
    build()
    await screen.findByText('Công ty Mu')
    expect(shownTaxCodes()).toEqual(['0200', '0100', '0300', '0400'])
  })

  it('sorts a numeric column biggest-first on the first click, then smallest-first, then back to the ranking', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByText('Công ty Mu')
    await user.click(await header('Số dòng'))
    await waitFor(() => expect(shownTaxCodes()).toEqual(['0200', '0300', '0400', '0100']))
    await user.click(await header('Số dòng'))
    await waitFor(() => expect(shownTaxCodes()).toEqual(['0100', '0300', '0400', '0200']))
    await user.click(await header('Số dòng'))
    await waitFor(() => expect(shownTaxCodes()).toEqual(['0200', '0100', '0300', '0400']))
  })

  it('puts the row with an empty name and the row with no average price last in BOTH directions', async () => {
    const user = userEvent.setup()
    build()
    await screen.findByText('Công ty Mu')
    await user.click(await header('Doanh nghiệp'))
    await waitFor(() => expect(shownTaxCodes()).toEqual(['0100', '0200', '0400', '0300']))
    await user.click(await header('Doanh nghiệp'))
    await waitFor(() => expect(shownTaxCodes()).toEqual(['0400', '0200', '0100', '0300']))

    await user.click(await header(/^Giá BQ/))
    await waitFor(() => expect(shownTaxCodes().at(-1)).toBe('0300'))
    await user.click(await header(/^Giá BQ/))
    await waitFor(() => expect(shownTaxCodes().at(-1)).toBe('0300'))
  })
})
