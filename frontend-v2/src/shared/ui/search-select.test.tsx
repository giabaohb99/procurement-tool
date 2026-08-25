import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SearchSelect } from './search-select'

const LOAI_VAN_BAN = [
  { value: '1', label: 'Công văn · CV' },
  { value: '28', label: 'Giấy nghỉ phép · GNP' },
  { value: '5', label: 'Hợp đồng · HD' },
  { value: '30', label: 'Đơn vị gửi nhận · DVN' },
]

function dung(onChange = vi.fn()) {
  render(
    <SearchSelect
      value=""
      onChange={onChange}
      options={LOAI_VAN_BAN}
      placeholder="Chọn loại văn bản"
      searchPlaceholder="Tìm theo tên hoặc mã loại…"
    />,
  )
  return onChange
}

async function moVaGo(nguoi: ReturnType<typeof userEvent.setup>, tu: string) {
  await nguoi.click(screen.getByRole('combobox'))
  if (tu) await nguoi.type(screen.getByPlaceholderText(/Tìm theo tên/), tu)
}

describe('SearchSelect', () => {
  it('tìm theo TÊN, không bắt gõ đúng từ đầu nhãn', async () => {
    //  Lỗi khách báo 25/08/2026: ô chọn loại văn bản là `Select` thường, 33
    //  dòng, không có ô tìm. Typeahead của trình duyệt khớp từ ĐẦU nhãn mà nhãn
    //  lại bắt đầu bằng MÃ, nên gõ «nghỉ phép» không nhảy tới đâu và người dùng
    //  kết luận là danh mục không có loại đó.
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, 'nghỉ phép')

    expect(screen.getByText('Giấy nghỉ phép · GNP')).toBeInTheDocument()
    expect(screen.queryByText('Công văn · CV')).not.toBeInTheDocument()
  })

  it('gõ KHÔNG DẤU vẫn ra — người Việt tìm thường không bỏ dấu', async () => {
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, 'nghi phep')

    expect(screen.getByText('Giấy nghỉ phép · GNP')).toBeInTheDocument()
  })

  it('chữ Đ cũng bỏ dấu được — NFD không đụng tới nó', async () => {
    //  `normalize('NFD')` tách dấu thành ký tự tổ hợp, nhưng «đ» là một CHỮ CÁI
    //  riêng chứ không phải d có dấu, nên phải thay tay. Thiếu chỗ đó thì gõ
    //  "don vi" không ra "Đơn vị".
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, 'don vi')

    expect(screen.getByText('Đơn vị gửi nhận · DVN')).toBeInTheDocument()
  })

  it('tìm theo MÃ loại cũng được', async () => {
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, 'GNP')

    expect(screen.getByText('Giấy nghỉ phép · GNP')).toBeInTheDocument()
  })

  it('không khớp gì thì nói thẳng, đừng hiện danh sách trống', async () => {
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, 'khong-co-that')

    expect(screen.getByText(/Không tìm thấy/i)).toBeInTheDocument()
  })

  it('chọn xong báo đúng giá trị cho bên gọi', async () => {
    const nguoi = userEvent.setup()
    const onChange = dung()
    await moVaGo(nguoi, 'nghi phep')
    await nguoi.click(screen.getByText('Giấy nghỉ phép · GNP'))

    expect(onChange).toHaveBeenCalledWith('28')
  })

  it('chưa gõ gì thì hiện đủ danh sách', async () => {
    const nguoi = userEvent.setup()
    dung()
    await moVaGo(nguoi, '')

    for (const item of LOAI_VAN_BAN) {
      expect(screen.getByText(item.label)).toBeInTheDocument()
    }
  })
})
