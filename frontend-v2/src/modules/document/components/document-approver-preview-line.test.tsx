import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DocumentApproverPreviewLine } from './document-approver-preview-line'
import type { ApprovalPreviewResult, ApprovalPreviewStep } from '../types/approval-preview'

function step(overrides: Partial<ApprovalPreviewStep>): ApprovalPreviewStep {
  return {
    seq: 1,
    name: 'Trưởng phòng',
    rule_label: '',
    approvers: [],
    unresolved_reason: '',
    fallback_used: false,
    pending_field: '',
    note: '',
    ...overrides,
  }
}

function flow(
  steps: ApprovalPreviewStep[],
  cc: ApprovalPreviewResult['cc'] = [],
): ApprovalPreviewResult {
  return { mode: 'flow', engine_enabled: true, flow_name: 'Luồng A', steps, cc }
}

describe('DocumentApproverPreviewLine', () => {
  it('reads as one line: each step with its approvers, in order', () => {
    render(
      <DocumentApproverPreviewLine
        isLoading={false}
        preview={flow([
          step({ seq: 1, approvers: [{ employee_id: 1, name: 'Nguyễn A', position: '' }] }),
          step({
            seq: 2,
            approvers: [
              { employee_id: 2, name: 'Trần B', position: '' },
              { employee_id: 3, name: 'Lê C', position: '' },
            ],
          }),
        ])}
      />,
    )
    expect(screen.getByText('Nguyễn A')).toBeInTheDocument()
    expect(screen.getByText('Trần B, Lê C')).toBeInTheDocument()
  })

  it('a step with nobody found (config problem) shows its reason, not a blank', () => {
    render(
      <DocumentApproverPreviewLine
        isLoading={false}
        preview={flow([step({ unresolved_reason: 'Phòng chưa có trưởng phòng' })])}
      />,
    )
    expect(screen.getByText('Phòng chưa có trưởng phòng')).toBeInTheDocument()
  })

  it('lists carbon-copy recipients after the steps', () => {
    render(
      <DocumentApproverPreviewLine
        isLoading={false}
        preview={flow(
          [step({ approvers: [{ employee_id: 1, name: 'Nguyễn A', position: '' }] })],
          [
            {
              seq: 9,
              name: 'CC',
              rule_label: '',
              approvers: [{ employee_id: 5, name: 'Văn thư', position: '' }],
            },
          ],
        )}
      />,
    )
    expect(screen.getByText(/Nhận bản sao: Văn thư/)).toBeInTheDocument()
  })

  it.each([
    [
      { mode: 'none', engine_enabled: true, flow_name: '', steps: [], cc: [] },
      'Không cần phê duyệt',
    ],
    [{ mode: 'legacy', engine_enabled: false, flow_name: '', steps: [], cc: [] }, /Duyệt một bước/],
    [flow([]), 'Luồng chưa có chặng nào'],
  ] as const)('explains the non-flow case %#', (preview, text) => {
    render(
      <DocumentApproverPreviewLine isLoading={false} preview={preview as ApprovalPreviewResult} />,
    )
    expect(screen.getByText(text)).toBeInTheDocument()
  })

  it('before Loại/Pháp nhân are picked it says what to do, not an empty line', () => {
    render(<DocumentApproverPreviewLine isLoading={false} preview={undefined} />)
    expect(screen.getByText(/chọn Loại văn bản và Pháp nhân/)).toBeInTheDocument()
  })
})
