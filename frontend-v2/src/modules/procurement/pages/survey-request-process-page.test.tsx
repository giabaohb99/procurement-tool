import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { SurveyRequestProcessPage } from './survey-request-process-page'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => false }),
}))
vi.mock('../hooks/use-survey-request', () => ({
  useSurveyRequest: () => ({ data: undefined, isLoading: false, isError: false }),
}))

/**
 * duoc-CR-741 — người không có quyền xử lý khảo sát: bản v1 cho nút *Quay lại* về ĐÚNG phiếu
 * YCBG đang mở, không văng ra danh sách như v2 cũ (*Về danh sách*).
 */
describe('SurveyRequestProcessPage — không có quyền xử lý (duoc-CR-741)', () => {
  it('offers Quay lại that goes back to the same survey request, not to the list', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={['/procurement/survey-requests/28/process']}>
        <Routes>
          <Route path="/procurement/survey-requests/:id/process" element={<SurveyRequestProcessPage />} />
          <Route path="/procurement/survey-requests/:id" element={<p>Chi tiết phiếu 28</p>} />
          <Route path="/procurement/survey-requests" element={<p>Danh sách phiếu</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Không có quyền xử lý khảo sát')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Về danh sách' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Quay lại' }))
    expect(await screen.findByText('Chi tiết phiếu 28')).toBeInTheDocument()
  })
})
