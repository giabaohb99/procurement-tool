import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { DocumentAccessCard } from './document-access-card'
import { EFFECT } from '../types/document-access'

const DONG_CON_HIEU_LUC = {
  id: 1,
  subject_kind: 1,
  subject_kind_label: 'Người',
  subject_id: 7,
  subject_name: 'Nhân viên Thu mua (Demo)',
  effect: EFFECT.allow,
  effect_label: 'Cho phép',
  can_read: true,
  can_write: false,
  can_delete: false,
  valid_from: null,
  valid_to: null,
  reason: '',
  granted_by_name: 'Dego Admin',
  is_active: true,
  revoked_at: null,
  revoked_by_name: null,
  revoke_reason: null,
}

const DONG_DA_HUY = {
  ...DONG_CON_HIEU_LUC,
  id: 2,
  subject_name: 'Nhân viên (Demo)',
  is_active: false,
  revoked_at: '2026-08-24T10:48:00',
  revoked_by_name: 'Dego Admin',
  revoke_reason: null,
}

const revoke = { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false }

vi.mock('../hooks/use-document-access', () => ({
  useDocumentAccess: () => ({ data: [DONG_CON_HIEU_LUC, DONG_DA_HUY] }),
  useGrantAccess: () => ({ mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false }),
  useRevokeAccess: () => revoke,
}))

//  Hộp chia quyền kéo theo cả cây danh mục nhân sự / phòng ban — không phải thứ
//  bài này kiểm, và mount thật thì phải giả lập thêm bốn hook nữa.
vi.mock('./document-access-dialog', () => ({ DocumentAccessDialog: () => null }))

describe('DocumentAccessCard — chữ «Hủy» thay cho «Thu hồi»', () => {
  it('nút và dòng đã hủy đều dùng chữ HỦY, không còn chữ «Thu hồi»', () => {
    //  Khách yêu cầu 25/08/2026: đổi hết chữ «Thu hồi» thành «Hủy».
    render(<DocumentAccessCard documentId={1} canWrite />)

    expect(screen.getByLabelText('Hủy quyền')).toBeInTheDocument()
    expect(screen.getByText(/^Đã hủy/)).toBeInTheDocument()
    expect(screen.queryByText(/Thu hồi/)).not.toBeInTheDocument()
  })

  it('hộp xác nhận KHÔNG được có hai nút cùng chữ «Hủy»', async () => {
    //  Nút bỏ qua của `ConfirmIconButton` đã là «Hủy» sẵn. Đặt nhãn nút thi hành
    //  cũng là «Hủy» trơn thì hộp có hai nút cạnh nhau chữ y hệt nhau — một cái
    //  bỏ qua, một cái cắt quyền người khác và không hoàn tác được. Nhãn thi
    //  hành phải nói rõ hủy CÁI GÌ.
    const nguoi = userEvent.setup()
    render(<DocumentAccessCard documentId={1} canWrite />)
    await nguoi.click(screen.getByLabelText('Hủy quyền'))

    const hop = await screen.findByRole('alertdialog')
    const nhan = [...hop.querySelectorAll('button')].map((nut) => nut.textContent?.trim())
    expect(nhan).toContain('Hủy') //  nút bỏ qua
    expect(nhan).toContain('Hủy quyền') //  nút thi hành
    expect(new Set(nhan).size).toBe(nhan.length) //  không nhãn nào trùng nhau
  })

  it('không có quyền sửa thì không hiện nút hủy', () => {
    render(<DocumentAccessCard documentId={1} canWrite={false} />)
    expect(screen.queryByLabelText('Hủy quyền')).not.toBeInTheDocument()
  })
})
