import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DocumentApproverPreviewCard } from './document-approver-preview-card'
import type { ApprovalPreviewResult, ApprovalPreviewStep } from '../types/approval-preview'

const CAVEAT_TEXT = 'người duyệt thực tế chốt lúc gửi duyệt'

function step(overrides: Partial<ApprovalPreviewStep> = {}): ApprovalPreviewStep {
  return {
    seq: 1,
    name: 'Chặng 1',
    rule_label: '',
    approvers: [],
    unresolved_reason: '',
    fallback_used: false,
    pending_field: '',
    note: '',
    ...overrides,
  }
}

function result(overrides: Partial<ApprovalPreviewResult> = {}): ApprovalPreviewResult {
  return {
    mode: 'flow',
    engine_enabled: true,
    flow_name: 'Luồng duyệt quy chế',
    steps: [],
    cc: [],
    ...overrides,
  }
}

describe('trạng thái chưa có gì để xem', () => {
  it('đang tải thì không hiện câu mời chọn Loại/Pháp nhân', () => {
    render(<DocumentApproverPreviewCard preview={undefined} isLoading />)
    expect(
      screen.queryByText('Chọn Loại văn bản và Pháp nhân để xem người duyệt dự kiến.'),
    ).not.toBeInTheDocument()
  })

  it('không tải và chưa có preview thì mời chọn Loại/Pháp nhân', () => {
    render(<DocumentApproverPreviewCard preview={undefined} isLoading={false} />)
    expect(
      screen.getByText('Chọn Loại văn bản và Pháp nhân để xem người duyệt dự kiến.'),
    ).toBeInTheDocument()
  })
})

describe('ba trạng thái mode', () => {
  it('mode "none" nói rõ loại này không cần duyệt', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({ mode: 'none', engine_enabled: false, flow_name: '' })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Loại văn bản này KHÔNG cần phê duyệt.')).toBeInTheDocument()
  })

  it('mode "legacy" + bộ máy tắt → nói bộ máy TẮT', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({ mode: 'legacy', engine_enabled: false, flow_name: '' })}
        isLoading={false}
      />,
    )
    expect(screen.getByText(/Bộ máy luồng nhiều bước đang TẮT/)).toBeInTheDocument()
  })

  it('mode "legacy" + bộ máy bật nhưng không luồng nào khớp → nói rõ lý do khác', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({ mode: 'legacy', engine_enabled: true, flow_name: '' })}
        isLoading={false}
      />,
    )
    expect(screen.getByText(/Chưa khai luồng phê duyệt nào khớp/)).toBeInTheDocument()
  })

  it('mode "flow" hiện tên luồng', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({ steps: [step({ approvers: [{ employee_id: 1, name: 'A', position: '' }] })] })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Luồng duyệt quy chế')).toBeInTheDocument()
  })
})

describe('một chặng có người duyệt', () => {
  it('hiện tên, chức vụ và quy tắc khai', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              name: 'Trưởng bộ phận duyệt',
              rule_label: 'Trưởng bộ phận người nộp',
              approvers: [{ employee_id: 9, name: 'Nguyễn Văn A', position: 'Trưởng phòng Nhân sự' }],
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Trưởng bộ phận duyệt')).toBeInTheDocument()
    expect(screen.getByText('Trưởng bộ phận người nộp')).toBeInTheDocument()
    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
    expect(screen.getByText(/Trưởng phòng Nhân sự/)).toBeInTheDocument()
  })

  it('nhiều người duyệt cùng chặng thì hiện ĐỦ từng người, không chỉ người đầu', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              approvers: [
                { employee_id: 1, name: 'Người A', position: '' },
                { employee_id: 2, name: 'Người B', position: '' },
                { employee_id: 3, name: 'Người C', position: '' },
              ],
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Người A')).toBeInTheDocument()
    expect(screen.getByText('Người B')).toBeInTheDocument()
    expect(screen.getByText('Người C')).toBeInTheDocument()
  })

  it('dùng người DỰ PHÒNG thì vẫn hiện tên kèm ghi chú, không phải cảnh báo đỏ', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              approvers: [{ employee_id: 1, name: 'Người dự phòng', position: '' }],
              fallback_used: true,
              note: 'Không tìm được người duyệt theo quy tắc — sẽ chuyển cho người dự phòng.',
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Người dự phòng')).toBeInTheDocument()
    expect(screen.getByText(/chuyển cho người dự phòng/)).toBeInTheDocument()
  })
})

describe('một chặng RỖNG — ba lý do khác nhau, ba câu khác nhau', () => {
  it('FIELD chưa chọn (vd người ký) → câu "chưa chọn", KHÔNG phải "không có ai"', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              pending_field: 'signer_employee_id',
              unresolved_reason: 'Sẽ là người ký — chưa chọn',
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Sẽ là người ký — chưa chọn')).toBeInTheDocument()
    expect(screen.queryByText(/không tìm được/i)).not.toBeInTheDocument()
  })

  it('tự động qua vì trùng người chặng trước → hiện NOTE, không phải câu kẹt', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              note: 'Mọi người ở chặng này đều đã duyệt ở (các) chặng trước — chặng này sẽ tự động qua, không cần ai bấm thêm.',
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText(/tự động qua/)).toBeInTheDocument()
  })

  it('không tìm được người duyệt và không dự phòng → cảnh báo phiếu sẽ DỪNG', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              unresolved_reason:
                'Không tìm được người duyệt cho chặng «Bước 1» — phiếu sẽ DỪNG LẠI ở đây và cần quản trị sửa luồng.',
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText(/phiếu sẽ DỪNG LẠI/)).toBeInTheDocument()
  })

  it('cực đoan: cả bốn cờ cùng có giá trị — ưu tiên ĐÚNG THỨ TỰ của backend, không hiện chồng chéo', () => {
    //  Backend không bao giờ trả tổ hợp này (bốn nhánh loại trừ nhau ở
    //  `_stage_step`), nhưng component không được sụp nếu dữ liệu bất thường —
    //  và phải chọn ĐÚNG MỘT câu theo thứ tự ưu tiên tài liệu hóa trong
    //  `StepBody`: có người duyệt thắng tất cả.
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [
            step({
              approvers: [{ employee_id: 1, name: 'Người thắng', position: '' }],
              pending_field: 'signer_employee_id',
              note: 'ghi chú trùng người',
              unresolved_reason: 'không tìm được người duyệt',
            }),
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText('Người thắng')).toBeInTheDocument()
    expect(screen.queryByText('ghi chú trùng người')).not.toBeInTheDocument()
    expect(screen.queryByText('không tìm được người duyệt')).not.toBeInTheDocument()
  })
})

describe('CC — nhận bản sao', () => {
  it('có người trong `cc` thì liệt kê tên, tách khỏi danh sách chặng duyệt', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [step({ approvers: [{ employee_id: 1, name: 'Người duyệt', position: '' }] })],
          cc: [
            {
              seq: 2,
              name: 'Nhận bản sao',
              rule_label: '',
              approvers: [{ employee_id: 5, name: 'Người xem', position: '' }],
            },
          ],
        })}
        isLoading={false}
      />,
    )
    expect(screen.getByText(/Nhận bản sao:/)).toBeInTheDocument()
    expect(screen.getByText(/Người xem/)).toBeInTheDocument()
  })

  it('`cc` rỗng thì KHÔNG hiện dòng "Nhận bản sao" nào cả', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [step({ approvers: [{ employee_id: 1, name: 'Người duyệt', position: '' }] })],
          cc: [],
        })}
        isLoading={false}
      />,
    )
    expect(screen.queryByText(/Nhận bản sao:/)).not.toBeInTheDocument()
  })

  it('cực đoan: bước CC có tên trong `cc` nhưng approvers rỗng thì không lộ dòng trống', () => {
    render(
      <DocumentApproverPreviewCard
        preview={result({
          steps: [],
          cc: [{ seq: 1, name: 'Nhận bản sao', rule_label: '', approvers: [] }],
        })}
        isLoading={false}
      />,
    )
    expect(screen.queryByText(/Nhận bản sao:/)).not.toBeInTheDocument()
  })
})

describe('câu chú thích luôn hiện khi đã có kết quả', () => {
  it('mọi mode đều kèm câu "dự kiến"', () => {
    render(<DocumentApproverPreviewCard preview={result({ mode: 'none' })} isLoading={false} />)
    expect(screen.getByText(new RegExp(CAVEAT_TEXT))).toBeInTheDocument()
  })
})
