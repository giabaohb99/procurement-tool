// bao-CR-608 — hộp chi tiết dòng hàng: nút Sửa / Xóa theo quyền, sửa chỉ gửi ô đã đổi, xóa phải
// hỏi xác nhận. Chặn ở tầng `@/core/api` (luật testing.md) để thấy đúng đường API được gọi.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type * as CoreApi from '@/core/api'

import { CustomsLineDetailDialog } from './customs-line-detail-dialog'

const patchCalls: { url: string; body: unknown }[] = []
const deleteCalls: string[] = []

const LINE = {
  id: 4321,
  batch_id: 9,
  source_row: 2,
  date_fixed: false,
  importer_id: 3,
  partner_id: 0,
  active_ingredient: 'ATRAZINE',
  formulation: '97%',
  active_ingredient_from_file: false,
  formulation_from_file: false,
  price_vnd_flat_from_file: false,
  price_vnd_line_tax_from_file: false,
  reg_date: '2026-01-13',
  office_code: 'HQHPKV3',
  line_no: 1,
  import_country: 'VN',
  importer_name: 'CÔNG TY A',
  importer_tax_code: '0500590269',
  partner_name: '',
  origin_country: 'DK',
  product_name: 'ATRAZINE 97% TECH',
  hs_code: '38089990',
  quantity: 880,
  unit_code: 'KGM',
  price_usd: 17.3897,
  adj_price_usd: null,
  effective_price_usd: 17.3897,
  price_vnd_flat: 485437,
  price_vnd_line_tax: null,
  price_nt: 14.9,
  adj_price_nt: null,
  currency: 'EUR',
  fx_rate: 30448.32,
  usd_rate: 26089,
  contract_no: '770710',
  contract_date: null,
  incoterm: 'CIF',
  transport_mode: 2,
  transport_label: 'Đường biển (container)',
  rate_import: 0,
  rate_excise: null,
  rate_vat: 5,
  rate_safeguard: null,
  tax_import: 0,
  tax_excise: null,
  tax_vat: 1,
  tax_environment: null,
  tax_safeguard: null,
}

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApi>()
  return {
    ...actual,
    apiGet: async () => LINE,
    apiPatch: async (url: string, body: unknown) => {
      patchCalls.push({ url, body })
      return LINE
    },
    apiDelete: async (url: string) => {
      deleteCalls.push(url)
      return null
    },
  }
})

function mount(props: { canEdit?: boolean; canDelete?: boolean; onClose?: () => void } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <CustomsLineDetailDialog
        lineId={LINE.id}
        onClose={props.onClose ?? (() => undefined)}
        onFilterImporter={() => undefined}
        onFilterPartner={() => undefined}
        canEdit={props.canEdit}
        canDelete={props.canDelete}
      />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  patchCalls.length = 0
  deleteCalls.length = 0
})

describe('CustomsLineDetailDialog — bao-CR-608', () => {
  it('shows neither Sửa nor Xóa without the rights', async () => {
    mount()
    expect(await screen.findByText('ATRAZINE 97% TECH')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Sửa/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xóa/ })).not.toBeInTheDocument()
  })

  it('shows only the button the user has the right for', async () => {
    mount({ canDelete: true })
    expect(await screen.findByRole('button', { name: /Xóa/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Sửa/ })).not.toBeInTheDocument()
  })

  it('edits in place and sends only the changed cell', async () => {
    mount({ canEdit: true })
    await userEvent.click(await screen.findByRole('button', { name: /Sửa/ }))
    const price = screen.getByLabelText('Đơn giá khai báo (USD)')
    await userEvent.clear(price)
    await userEvent.type(price, '21')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(patchCalls).toHaveLength(1))
    expect(patchCalls[0]).toEqual({ url: '/api/customs/lines/4321', body: { price_usd: 21 } })
  })

  it('does not save when Enter is pressed inside a cell', async () => {
    mount({ canEdit: true })
    await userEvent.click(await screen.findByRole('button', { name: /Sửa/ }))
    await userEvent.type(screen.getByLabelText('Số hợp đồng'), 'X{Enter}')
    expect(patchCalls).toHaveLength(0)
  })

  it('refuses a negative quantity before calling the API', async () => {
    mount({ canEdit: true })
    await userEvent.click(await screen.findByRole('button', { name: /Sửa/ }))
    const quantity = screen.getByLabelText('Lượng')
    await userEvent.clear(quantity)
    await userEvent.type(quantity, '-5')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText(/«Lượng» phải là số không âm/)).toBeInTheDocument()
    expect(patchCalls).toHaveLength(0)
  })

  it('asks for confirmation before deleting, then deletes and closes', async () => {
    const onClose = vi.fn()
    mount({ canDelete: true, onClose })
    await userEvent.click(await screen.findByRole('button', { name: /Xóa/ }))
    expect(deleteCalls).toHaveLength(0)
    const dialog = await screen.findByRole('alertdialog')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Xóa' }))
    await waitFor(() => expect(deleteCalls).toEqual(['/api/customs/lines/4321']))
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
