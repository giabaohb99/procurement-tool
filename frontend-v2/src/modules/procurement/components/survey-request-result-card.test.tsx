import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { SurveyRequestResult } from '../types/survey-request-detail'
import { SurveyRequestResultCard } from './survey-request-result-card'

vi.mock('@/core/api', () => ({ downloadFile: vi.fn() }))

function renderCard(mergedFlowEnabled: boolean, props?: { showWaitFinalizeHint?: boolean }) {
  const result: SurveyRequestResult = {
    id: 1,
    code: 'YCBG-001',
    status: 'survey_done',
    merged_flow_enabled: mergedFlowEnabled,
    lines: [],
  }
  render(
    <SurveyRequestResultCard
      result={result}
      canChoose
      canSetLineStatus={false}
      showCreatePrHint={!props?.showWaitFinalizeHint}
      showWaitFinalizeHint={!!props?.showWaitFinalizeHint}
      onChooseOption={vi.fn()}
      onRequestResurvey={vi.fn()}
      onConfirmLine={vi.fn()}
    />,
  )
}

/**
 * bao-CR-290: luồng gộp bỏ hẳn bước YCMH và nút "Tạo yêu cầu mua" ở góc phải trên
 * đã ẩn theo cờ — câu hướng dẫn mà vẫn chỉ vào cái nút không còn ở đó thì người
 * yêu cầu đứng chờ một nút không tồn tại.
 */
describe('SurveyRequestResultCard — câu hướng dẫn theo luồng', () => {
  it('points at "Chốt phương án" when the merged flow is on', () => {
    renderCard(true)

    expect(screen.getByText(/Chốt phương án/)).toBeInTheDocument()
    expect(screen.queryByText(/Tạo yêu cầu mua/)).not.toBeInTheDocument()
    expect(screen.getByText(/không lên đơn mua hàng/)).toBeInTheDocument()
  })

  it('keeps the legacy YCMH wording when the merged flow is off', () => {
    renderCard(false)

    expect(screen.getByText(/Tạo yêu cầu mua/)).toBeInTheDocument()
    expect(screen.queryByText(/Chốt phương án/)).not.toBeInTheDocument()
    expect(screen.getByText(/không tạo YCMH/)).toBeInTheDocument()
  })

  it('says "đã lên đơn mua hàng", not "đã tạo YCMH", while waiting in the merged flow', () => {
    // Luồng gộp cũng đẩy phiếu sang trạng thái `pr_created` sau khi tạo ĐMH, nên
    // câu chờ Hoàn thành dùng chung nhánh này — nói "YCMH" là nói về một chứng từ
    // chưa từng được sinh ra.
    renderCard(true, { showWaitFinalizeHint: true })

    expect(screen.getByText(/Đã lên đơn mua hàng/)).toBeInTheDocument()
    expect(screen.queryByText(/Đã tạo YCMH/)).not.toBeInTheDocument()
  })
})
