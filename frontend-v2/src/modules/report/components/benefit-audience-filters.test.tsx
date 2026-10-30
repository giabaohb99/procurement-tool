import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { BenefitAudienceFilters } from './benefit-audience-filters'

const perm = vi.hoisted(() => ({ sensitive: true, leave: true }))
//  Không có `department.read` → ô phòng ban tự ẩn, không gọi API danh mục.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string) =>
      (entity === 'employee_sensitive' && perm.sensitive) || (entity === 'leave_request' && perm.leave),
  }),
}))

beforeEach(() => {
  perm.sensitive = true
  perm.leave = true
})

/**
 * Dựng ô lọc trên một data router để ĐẾM số lượt ghi URL: mỗi `setSearchParams` = một lượt
 * điều hướng mới (khóa `location.key` mới). Bẫy cần canh: gọi hai setter liên tiếp trong một
 * lần bấm thì lượt sau đọc URL cũ và đè mất lượt trước (`use-url-param-state.ts`).
 */
function renderFilters(search = '') {
  const router = createMemoryRouter([{ path: '/', element: <BenefitAudienceFilters /> }], {
    initialEntries: [`/${search}`],
  })
  const writes: URLSearchParams[] = []
  let lastKey = router.state.location.key
  router.subscribe((state) => {
    if (state.location.key === lastKey) return
    lastKey = state.location.key
    writes.push(new URLSearchParams(state.location.search))
  })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  const url = () => new URLSearchParams(router.state.location.search)
  return { writes, url }
}

describe('BenefitAudienceFilters', () => {
  it('a preset chip writes its whole filter set in ONE URL update and clears the previous occasion', async () => {
    const user = userEvent.setup()
    const { writes, url } = renderFilters('?gender=2&occasion_label=Qu%E1%BB%91c+t%E1%BA%BF+Ph%E1%BB%A5+n%E1%BB%AF+8%2F3')
    await user.click(screen.getByRole('button', { name: '1/6' }))
    expect(writes).toHaveLength(1)
    const p = url()
    expect(p.get('child_max_age')).toBe('14')
    expect(p.get('occasion_label')).toBe('Quốc tế Thiếu nhi 1/6')
    expect(p.get('gender')).toBeNull()
    expect(p.get('preset')).toBe('custom')
    expect(p.get('date_from')).toMatch(/^\d{4}-06-01$/)
    expect(p.get('date_to')).toBe(p.get('date_from'))
    expect(screen.getByRole('button', { name: '1/6' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Tính theo con, con ≤ 14 tuổi')).toBeInTheDocument()
  })

  it('typing a gift amount writes the URL once after the user stops, not once per digit', async () => {
    const user = userEvent.setup()
    const { writes, url } = renderFilters()
    await user.type(screen.getByLabelText('Mức quà nhân viên (đ)'), '500000')
    await waitFor(() => expect(url().get('amount_staff')).toBe('500000'))
    expect(writes.filter((w) => w.has('amount_staff')).map((w) => w.get('amount_staff'))).toEqual(['500000'])
  })

  it('clamps a gift amount above one billion while typing', async () => {
    const user = userEvent.setup()
    const { url } = renderFilters()
    await user.type(screen.getByLabelText('Mức quà quản lý — từ Phó phòng (đ)'), '99999999999')
    await waitFor(() => expect(url().get('amount_manager')).toBe('1000000000'))
  })

  it('"Bỏ hết điều kiện" clears every H1 param in one write and the inputs follow the URL', async () => {
    const user = userEvent.setup()
    const { writes, url } = renderFilters('?amount_staff=200000&birth_month=3&include_on_leave=0&preset=today')
    expect(screen.getByLabelText('Mức quà nhân viên (đ)')).toHaveValue('200.000')
    await user.click(screen.getByRole('button', { name: 'Bỏ hết điều kiện' }))
    expect(writes).toHaveLength(1)
    expect(url().toString()).toBe('preset=today')
    expect(screen.getByLabelText('Mức quà nhân viên (đ)')).toHaveValue('')
    expect(screen.queryByRole('button', { name: 'Bỏ hết điều kiện' })).not.toBeInTheDocument()
  })

  it('removes a single preset condition from its badge', async () => {
    const user = userEvent.setup()
    const { url } = renderFilters('?seniority_years=1,3,5,10&gender=2')
    await user.click(screen.getByRole('button', { name: 'Bỏ điều kiện Tròn 1, 3, 5, 10 năm làm việc' }))
    expect(url().get('seniority_years')).toBeNull()
    expect(url().get('gender')).toBe('2')
  })

  it('the on-leave switch writes include_on_leave=0 and back to the default (removed)', async () => {
    const user = userEvent.setup()
    const { url } = renderFilters()
    const sw = screen.getByRole('switch', { name: 'Tính người đang nghỉ' })
    expect(sw).toBeChecked()
    await user.click(sw)
    expect(url().get('include_on_leave')).toBe('0')
    await user.click(sw)
    expect(url().has('include_on_leave')).toBe(false)
  })

  it('without the sensitive permission, birthday / children presets and age inputs are locked', () => {
    perm.sensitive = false
    renderFilters()
    for (const name of ['1/6', 'Trung thu', 'Sinh nhật tháng']) {
      expect(screen.getByRole('button', { name })).toBeDisabled()
    }
    for (const name of ['8/3', '20/10', 'Tết', 'Kỷ niệm năm làm việc']) {
      expect(screen.getByRole('button', { name })).toBeEnabled()
    }
    expect(screen.getByLabelText('Tuổi tại ngày dịp (từ – đến)')).toBeDisabled()
    expect(screen.getByText(/cần quyền xem ngày sinh và người thân/)).toBeInTheDocument()
  })

  it('without leave_request.read, the on-leave switch is locked with an explanation', () => {
    perm.leave = false
    renderFilters('?include_on_leave=0')
    const sw = screen.getByRole('switch', { name: 'Tính người đang nghỉ' })
    expect(sw).toBeDisabled()
    expect(sw).toBeChecked()
    expect(screen.getByText(/cần quyền xem đơn nghỉ phép/)).toBeInTheDocument()
  })
})
