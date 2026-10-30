import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { OAuthConsentPage } from './oauth-consent-page'

/**
 * Màn đồng ý OAuth của cổng MCP (ai-CR-218). Chỗ dễ lủng:
 * - mức mặc định phải theo đúng mức ứng dụng XIN (xin đọc thì không tự cấp ghi), người dùng đổi được;
 * - Cho phép / Từ chối gửi đúng chuỗi ký + mức rồi đưa trình duyệt về địa chỉ máy chủ trả (không tự ghép);
 * - bấm đúp không gửi hai lần (mỗi lần gửi tạo một mã cấp quyền);
 * - yêu cầu hết hạn / ký sai thì báo rõ, không hiện nút Cho phép.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const goTo = vi.fn()
const isFramed = vi.fn(() => false)

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  extractErrorMessage: (e: unknown) => (e instanceof Error ? e.message : 'lỗi'),
}))
vi.mock('./oauth-consent-redirect', () => ({ goTo: (url: string) => goTo(url), isFramed: () => isFramed() }))

const INFO = {
  client_name: 'ChatGPT',
  redirect_host: 'chatgpt.com',
  redirect_trusted: true,
  requested_scope: 0,
  grant_days: 90,
  user_label: 'Người YC (TESTREQ)',
}

function renderPage(req = 'abc.sig') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/oauth/consent/${req}`]}>
        <Routes>
          <Route path="/oauth/consent/:req" element={<OAuthConsentPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('OAuthConsentPage', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    goTo.mockReset()
    isFramed.mockReturnValue(false)
  })

  it('shows who asks and defaults to the scope the app requested (read only)', async () => {
    apiGet.mockResolvedValue(INFO)
    renderPage()
    expect(await screen.findByText('ChatGPT')).toBeInTheDocument()
    expect(screen.getByText('Người YC (TESTREQ)')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Chỉ đọc/ })).toBeChecked()
    expect(screen.getByRole('radio', { name: /Được ghi/ })).not.toBeChecked()
    expect(screen.getAllByText(/chatgpt\.com/).length).toBeGreaterThan(0)   // tiêu đề + dòng "quay về"
    expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/oauth/request/abc.sig', expect.anything())
  })

  it('approves with the chosen scope and sends the browser exactly where the server says', async () => {
    apiGet.mockResolvedValue(INFO)
    apiPost.mockResolvedValue({ redirect_to: 'https://chatgpt.com/cb?code=X&state=s' })
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /Được ghi/ }))
    await userEvent.click(screen.getByRole('button', { name: /Cho phép/ }))
    await waitFor(() => expect(goTo).toHaveBeenCalledWith('https://chatgpt.com/cb?code=X&state=s'))
    expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/oauth/approve', { req: 'abc.sig', scope: 1 }, expect.anything())
  })

  it('denies through the server so the app receives access_denied', async () => {
    apiGet.mockResolvedValue(INFO)
    apiPost.mockResolvedValue({ redirect_to: 'https://chatgpt.com/cb?error=access_denied' })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Từ chối' }))
    await waitFor(() => expect(goTo).toHaveBeenCalledWith('https://chatgpt.com/cb?error=access_denied'))
    expect(apiPost.mock.calls[0][0]).toBe('/api/agent-hub/oauth/deny')
  })

  it('sends only once on a double click (each send mints a one-time code)', async () => {
    apiGet.mockResolvedValue(INFO)
    let resolve: (v: unknown) => void = () => {}
    apiPost.mockReturnValue(new Promise((r) => { resolve = r }))
    renderPage()
    const allow = await screen.findByRole('button', { name: /Cho phép/ })
    await userEvent.dblClick(allow)
    resolve({ redirect_to: 'https://chatgpt.com/cb?code=X' })
    await waitFor(() => expect(goTo).toHaveBeenCalledTimes(1))
    expect(apiPost).toHaveBeenCalledTimes(1)
  })

  it('explains an expired or forged request and offers no Allow button', async () => {
    apiGet.mockRejectedValue(new Error('Yêu cầu cấp quyền đã hết hạn'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('đã hết hạn')
    expect(screen.queryByRole('button', { name: /Cho phép/ })).toBeNull()
  })

  //  ai-CR-222 (Agent 1 rà 19/10): kẻ xấu nhúng màn đồng ý vào iframe rồi đè nút giả lên "Cho phép" — nginx đã cấm nhúng,
  //  đây là lớp thứ hai: bị nhúng thì không gọi API, không có nút nào để bấm.
  it('refuses to work inside a frame: no request read, no buttons', async () => {
    isFramed.mockReturnValue(true)
    apiGet.mockResolvedValue(INFO)
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('cửa sổ trình duyệt riêng')
    expect(apiGet).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: /Cho phép/ })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Từ chối' })).toBeNull()
  })

  //  ai-CR-225 (Agent 1 rà 19/10, consent-phishing): tên ứng dụng là TỰ KHAI — kẻ xấu đăng ký "ChatGPT" với địa chỉ quay
  //  về của họ. Nơi quay về phải đứng cạnh tên, và lạ thì cảnh báo đỏ.
  it('puts the return host next to the app name and warns loudly when it is not a known AI app', async () => {
    apiGet.mockResolvedValue({ ...INFO, redirect_host: 'evil.example', redirect_trusted: false })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('evil.example')
    expect(screen.getByRole('alert')).toHaveTextContent('Từ chối')
    expect(screen.getByText('evil.example', { selector: 'span' })).toBeInTheDocument()
  })

  it('shows no warning for a known AI app', async () => {
    apiGet.mockResolvedValue(INFO)
    renderPage()
    expect(await screen.findByText('chatgpt.com', { selector: 'span' })).toBeInTheDocument()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('shows the server error and lets the user retry after a failed approve', async () => {
    apiGet.mockResolvedValue(INFO)
    apiPost.mockRejectedValueOnce(new Error('Yêu cầu cấp quyền đã hết hạn — quay lại ứng dụng AI'))
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Cho phép/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('quay lại ứng dụng AI')
    expect(screen.getByRole('button', { name: /Cho phép/ })).toBeEnabled()
    expect(goTo).not.toHaveBeenCalled()
  })
})
