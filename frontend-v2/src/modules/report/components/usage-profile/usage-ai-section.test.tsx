import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { USAGE_UNMEASURED_REASON_CODE } from '@/shared/constants/statuses'

import type { UsageSnapshot } from '../../types/usage-profile'
import { channelBars, clientBars, isAiNotCollected, toolGroupBars } from '../../utils/usage-ai-helpers'
import { UsageAiSection } from './usage-ai-section'

const collected: UsageSnapshot = {
  metrics: {
    ai_uses: { v: 8 },
    ai_active_days: { v: 2 },
    ai_mcp_share: { v: 0.375 },
    ai_tool_groups_used: { v: 2 },
    ai_docs_drafted: { v: 2 },
    ai_denied: { v: 0 },
    ai_drafts_confirmed: { v: 1 },
  },
  unmeasured: { ai_docs_share: USAGE_UNMEASURED_REASON_CODE.NOT_APPLICABLE },
  lists: { ai_channels: { '1': 5, '3': 3 }, ai_clients: { '1': 3 }, ai_tool_groups: [['mine', 4], ['xyz', 1]] },
}

describe('UsageAiSection (duoc-CR-655)', () => {
  it('says "chưa thu thập" and never shows 0 when AI usage is not collected', () => {
    const snapshot: UsageSnapshot = {
      metrics: {},
      unmeasured: { ai_uses: USAGE_UNMEASURED_REASON_CODE.NOT_COLLECTED },
    }
    render(<UsageAiSection snapshot={snapshot} />)
    expect(screen.getByText(/Chưa thu thập/)).toBeInTheDocument()
    expect(screen.queryByText('Lượt dùng AI')).not.toBeInTheDocument()
  })

  it('treats a snapshot from before the AI group existed as not collected', () => {
    expect(isAiNotCollected({ metrics: { logins: { v: 3 } } })).toBe(true)
  })

  it('shows the metrics once collected, with "Chưa đo được" for a metric without a denominator', () => {
    render(<UsageAiSection snapshot={collected} />)
    expect(screen.getByText('Lượt dùng AI')).toBeInTheDocument()
    expect(screen.getByText('38%')).toBeInTheDocument()
    expect(screen.getByText(/Chưa đo được — không áp dụng/)).toBeInTheDocument()
  })

  it('maps channel / client codes to Vietnamese labels and tool groups to names, unknown codes kept visible', () => {
    expect(channelBars(collected).map((b) => b.label)).toEqual(['Trợ lý web', 'Ứng dụng AI (MCP)'])
    expect(clientBars(collected)).toEqual([{ label: 'Claude', value: 3 }])
    expect(toolGroupBars(collected)).toEqual([
      { label: 'Việc và phiếu của mình', value: 4 },
      { label: 'xyz', value: 1 },
    ])
  })
})
