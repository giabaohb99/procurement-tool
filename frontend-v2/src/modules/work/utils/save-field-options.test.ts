import { describe, expect, it, vi } from 'vitest'

import { saveFieldOptions, type DraftOption, type SavedOption } from './save-field-options'

function fakeApi() {
  return {
    create: vi.fn().mockResolvedValue(undefined),
    update: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  }
}

const goc: SavedOption[] = [
  { id: 1, name: 'P1', color: 'red' },
  { id: 2, name: 'P2', color: 'orange' },
]

/** Bản nháp giống hệt bản gốc — dùng làm mốc cho các phép sửa từng phần. */
function nhap(): DraftOption[] {
  return goc.map((o) => ({ ...o }))
}

describe('saveFieldOptions', () => {
  it('không gửi lệnh nào khi bản nháp y hệt bản gốc', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, nhap(), api)
    expect(api.create).not.toHaveBeenCalled()
    expect(api.update).not.toHaveBeenCalled()
    expect(api.remove).not.toHaveBeenCalled()
  })

  it('chỉ đổi thứ tự cũng phải gửi lệnh sửa, kèm sort_order mới', async () => {
    const api = fakeApi()
    const daoNguoc = [...nhap()].reverse()
    await saveFieldOptions(goc, daoNguoc, api)
    expect(api.update).toHaveBeenCalledTimes(2)
    expect(api.update).toHaveBeenCalledWith(2, { name: 'P2', color: 'orange', sort_order: 0 })
    expect(api.update).toHaveBeenCalledWith(1, { name: 'P1', color: 'red', sort_order: 1 })
  })

  it('dòng id âm là dòng mới → tạo, không phải sửa', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, [...nhap(), { id: -1, name: 'P3', color: 'sky' }], api)
    expect(api.create).toHaveBeenCalledWith({ name: 'P3', color: 'sky', sort_order: 2 })
    expect(api.update).not.toHaveBeenCalled()
  })

  it('bỏ qua dòng để trống — máy chủ từ chối tên rỗng và làm hỏng cả lượt lưu', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, [...nhap(), { id: -1, name: '   ', color: 'sky' }], api)
    expect(api.create).not.toHaveBeenCalled()
    expect(api.remove).not.toHaveBeenCalled()
  })

  it('cắt khoảng trắng trước khi so, gõ thừa dấu cách không thành một lệnh sửa', async () => {
    const api = fakeApi()
    const draft = nhap()
    draft[0].name = '  P1  '
    await saveFieldOptions(goc, draft, api)
    expect(api.update).not.toHaveBeenCalled()
  })

  it('dòng biến mất khỏi bản nháp thì bị xóa', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, [{ id: 2, name: 'P2', color: 'orange' }], api)
    expect(api.remove).toHaveBeenCalledExactlyOnceWith(1)
    //  Dòng còn lại lên đầu nên sort_order đổi theo.
    expect(api.update).toHaveBeenCalledWith(2, { name: 'P2', color: 'orange', sort_order: 0 })
  })

  it('xóa sạch bộ giá trị thì xóa hết, không sót dòng nào', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, [], api)
    expect(api.remove).toHaveBeenCalledTimes(2)
    expect(api.create).not.toHaveBeenCalled()
  })

  it('bộ giá trị đang rỗng, thêm hai dòng mới thì sort_order là 0 rồi 1', async () => {
    const api = fakeApi()
    await saveFieldOptions(
      [],
      [
        { id: -1, name: 'A', color: 'sky' },
        { id: -2, name: 'B', color: 'red' },
      ],
      api,
    )
    expect(api.create).toHaveBeenNthCalledWith(1, { name: 'A', color: 'sky', sort_order: 0 })
    expect(api.create).toHaveBeenNthCalledWith(2, { name: 'B', color: 'red', sort_order: 1 })
  })

  it('dòng trống nằm GIỮA không làm lệch sort_order của các dòng sau', async () => {
    //  Vị trí trong mảng là sort_order, nên bỏ qua dòng trống vẫn phải giữ đúng
    //  chỉ số của dòng đứng sau nó — không thì hai dòng cùng sort_order.
    const api = fakeApi()
    const draft: DraftOption[] = [
      { id: 1, name: 'P1', color: 'red' },
      { id: -1, name: '', color: 'sky' },
      { id: 2, name: 'P2', color: 'orange' },
    ]
    await saveFieldOptions(goc, draft, api)
    expect(api.update).toHaveBeenCalledExactlyOnceWith(2, {
      name: 'P2',
      color: 'orange',
      sort_order: 2,
    })
  })

  it('id lạ trong bản nháp thì bỏ qua, không gọi sửa lên một dòng không có thật', async () => {
    const api = fakeApi()
    await saveFieldOptions(goc, [...nhap(), { id: 999, name: 'X', color: 'sky' }], api)
    expect(api.update).not.toHaveBeenCalled()
    expect(api.create).not.toHaveBeenCalled()
  })
})
