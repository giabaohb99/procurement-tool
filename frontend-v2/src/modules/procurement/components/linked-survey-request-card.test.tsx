import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import type { LinkedSurveyRequest } from '../types/purchase-request-detail'
import { LinkedSurveyRequestCard } from './linked-survey-request-card'

function surveyRequest(overrides: Partial<LinkedSurveyRequest> = {}): LinkedSurveyRequest {
  return {
    id: 501,
    code: 'YCBG05092601',
    status: 'survey_done',
    request_date: '2026-09-03',
    requester: 'Nguyễn Văn A',
    ...overrides,
  }
}

function renderCard(row: LinkedSurveyRequest, canOpen = true) {
  return render(
    <MemoryRouter>
      <LinkedSurveyRequestCard surveyRequest={row} canOpen={canOpen} />
    </MemoryRouter>,
  )
}

describe('LinkedSurveyRequestCard', () => {
  it('leads with the requester and keeps the code as a link to the survey request', () => {
    renderCard(surveyRequest())

    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /YCBG05092601/ })).toHaveAttribute(
      'href',
      appRoutes.procurement.surveyRequestDetail(501),
    )
    expect(screen.getByText(/03\/09\/2026/)).toBeInTheDocument()
  })

  it('without survey_request:read the code is plain text — a link would only hit 403', () => {
    renderCard(surveyRequest(), false)

    expect(screen.queryByRole('link')).toBeNull()
    expect(screen.getByText('YCBG05092601')).toBeInTheDocument()
  })

  it('unknown status code still shows up as the raw code', () => {
    renderCard(surveyRequest({ status: 'ma_la' }))

    expect(screen.getByText('ma_la')).toBeInTheDocument()
  })

  it('missing requester and date do not leave a blank first line or a dangling dot', () => {
    renderCard(surveyRequest({ requester: '', request_date: '' }))

    expect(screen.getByText('(chưa rõ người yêu cầu)')).toBeInTheDocument()
    expect(screen.queryByText('·')).toBeNull()
  })
})
