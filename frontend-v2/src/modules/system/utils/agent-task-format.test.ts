import { describe, expect, it } from 'vitest'

import { AGENT_TASK_STATUS, agentTaskTone, formatDurationMs, formatUsd, stripTelegramHtml } from './agent-task-format'

describe('agent-task-format', () => {
  it('formats model cost with 3 decimals below one dollar and dashes zero or missing', () => {
    expect(formatUsd(0.0312)).toBe('$0.031')
    expect(formatUsd(2.5)).toBe('$2.50')
    expect(formatUsd(0)).toBe('—')
    expect(formatUsd(null)).toBe('—')
    expect(formatUsd(undefined)).toBe('—')
  })

  it('formats durations the same way as the Telegram timing line', () => {
    expect(formatDurationMs(45_000)).toBe('45 giây')
    expect(formatDurationMs(396_000)).toBe('6,6 phút')
    expect(formatDurationMs(1_980_000)).toBe('33 phút')
    expect(formatDurationMs(0)).toBe('—')
    expect(formatDurationMs(-5_000)).toBe('—')
    expect(formatDurationMs(999)).toBe('—')
  })

  it('never falls back to a success tone for an unknown or closed-bad status', () => {
    expect(agentTaskTone(AGENT_TASK_STATUS.DONE)).toBe('done')
    expect(agentTaskTone(AGENT_TASK_STATUS.CANCELLED)).toBe('danger')
    expect(agentTaskTone(AGENT_TASK_STATUS.FAILED)).toBe('danger')
    expect(agentTaskTone(999)).toBe('neutral')
  })

  it('strips Telegram HTML and decodes entities, including a literal ampersand-lt sequence', () => {
    expect(stripTelegramHtml('<b>AI-0007</b>: gộp <code>erp-v2</code>')).toBe('AI-0007: gộp erp-v2')
    expect(stripTelegramHtml('a &lt; b &amp;&amp; c<br/>d')).toBe('a < b && c\nd')
    //  &amp;lt; là chữ «&lt;» thật trong tin, không phải dấu nhỏ hơn.
    expect(stripTelegramHtml('&amp;lt;')).toBe('&lt;')
    expect(stripTelegramHtml('')).toBe('')
  })
})
