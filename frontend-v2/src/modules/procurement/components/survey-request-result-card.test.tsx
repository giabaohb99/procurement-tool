import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'
import type {
  SurveyOptionAttachment,
  SurveyRequestResult,
  SurveyResultOption,
} from '../types/survey-request-detail'
import { SurveyRequestResultCard } from './survey-request-result-card'

const downloadFileMock = vi.fn((..._args: unknown[]) => Promise.resolve())
vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  downloadFile: (...args: unknown[]) => downloadFileMock(...args),
}))

const PDF: SurveyOptionAttachment = {
  file_id: 11,
  filename: 'bao-gia-ncc.pdf',
  url: '/api/attachments/11/download',
  content_type: 'application/pdf',
  size: 2048,
}
const PHOTO: SurveyOptionAttachment = {
  file_id: 12,
  filename: 'mau-thung.jpg',
  url: '/api/attachments/12/view',
  content_type: 'image/jpeg',
  size: 4096,
}

function buildOption(attachments: SurveyOptionAttachment[]): SurveyResultOption {
  return {
    id: 71,
    public_id: 1,
    display_label: 'Option 1',
    is_chosen: false,
    ncc_ref: 1,
    system_product_code: '',
    snap_product_name: 'Thùng carton 5 lớp',
    snap_spec: '',
    snap_origin: '',
    snap_quote_unit: 'Cái',
    snap_moq: '',
    snap_price_by_volume: '',
    snap_volume_range: '',
    snap_vat: '',
    snap_delivery_time: '',
    snap_delivery_place: '',
    snap_shipping_cost: '',
    snap_sample_ready: '',
    snap_lab_result: '',
    survey_result_date: '',
    survey_note: '',
    nstm_note: '',
    attachments,
    ycmh_list: [],
    ycmh_count: 0,
  }
}

function buildResult(attachments: SurveyOptionAttachment[]): SurveyRequestResult {
  return {
    id: 28,
    code: 'YCBG28082601',
    status: 'processing',
    lines: [
      {
        id: 301,
        item_group: 'Bao bì',
        requirement_detail: 'Thùng carton',
        other_requirement: '',
        request_qty: 100,
        uom: 'Cái',
        proposed_price: 0,
        is_completed: false,
        line_status: '',
        pr_id: 0,
        pr_code: '',
        no_option: false,
        options: [buildOption(attachments)],
        option_count: 1,
        has_chosen: false,
        progress_state: '',
        progress_tone: 'gray',
      },
    ],
  }
}

function renderCard(attachments: SurveyOptionAttachment[]) {
  const onChooseOption = vi.fn()
  render(
    <>
      <SurveyRequestResultCard
        result={buildResult(attachments)}
        canChoose
        canSetLineStatus={false}
        showCreatePrHint={false}
        showWaitFinalizeHint={false}
        onChooseOption={onChooseOption}
        onRequestResurvey={vi.fn()}
      />
      <ConfirmDialogHost />
    </>,
  )
  return { onChooseOption }
}

beforeEach(() => downloadFileMock.mockClear())

/**
 * duoc-CR-741 — bản v1 (`SurveyRequestDetail.tsx` openAtt) hỏi *Tải tài liệu* trước khi tải tệp
 * không phải ảnh của một phương án; v2 trước đây tải thẳng.
 */
describe('SurveyRequestResultCard — hỏi trước khi tải tệp đính kèm (duoc-CR-741)', () => {
  it('asks Tải tài liệu with the file name and only downloads after Tải về', async () => {
    const user = userEvent.setup()
    const { onChooseOption } = renderCard([PDF])

    await user.click(screen.getByRole('button', { name: 'bao-gia-ncc.pdf' }))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('Tải tài liệu')
    expect(dialog).toHaveTextContent('Tải file "bao-gia-ncc.pdf" về máy?')
    expect(downloadFileMock).not.toHaveBeenCalled()

    await user.click(within(dialog).getByRole('button', { name: 'Tải về' }))
    await waitFor(() =>
      expect(downloadFileMock).toHaveBeenCalledWith('/api/attachments/11/download', 'bao-gia-ncc.pdf'),
    )
    //  Bấm tệp nằm trong thẻ phương án KHÔNG được tính là chọn phương án.
    expect(onChooseOption).not.toHaveBeenCalled()
  })

  it('does not download when the user presses Hủy', async () => {
    const user = userEvent.setup()
    renderCard([PDF])

    await user.click(screen.getByRole('button', { name: 'bao-gia-ncc.pdf' }))
    await user.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Hủy' }))
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull())
    expect(downloadFileMock).not.toHaveBeenCalled()
  })

  it('opens an image straight away without asking, like v1', async () => {
    const user = userEvent.setup()
    renderCard([PHOTO])

    await user.click(screen.getByRole('button', { name: 'mau-thung.jpg' }))
    expect(screen.queryByRole('alertdialog')).toBeNull()
    expect(downloadFileMock).not.toHaveBeenCalled()
    expect(await screen.findByRole('dialog')).toBeInTheDocument()
  })
})
