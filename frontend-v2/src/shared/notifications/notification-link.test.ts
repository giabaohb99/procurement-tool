import { describe, expect, it } from 'vitest'

import { allModules } from '@/app/router/module-registry'
import { toAppPath, V2_PREFIXES } from './notification-link'

describe('toAppPath', () => {
  it('link của phân hệ dựng thẳng trên v2 thì đi thẳng, không trả null', () => {
    //  LỖI ĐÃ XẢY RA (20/08/2026): hàm này chỉ biết link kiểu app CŨ. Nhánh
    //  "link v2 thì giữ nguyên" so với đúng sáu đích trong bảng dịch, nên
    //  `/document/...` rơi xuống cuối và trả null — bấm vào thông báo không đi
    //  đâu cả. Cả HAI thư của luồng clone đều dính, tức là đường báo việc cho
    //  pháp nhân con gãy ở bước cuối.
    expect(toAppPath('/document/documents/273')).toBe('/document/documents/273')
    expect(toAppPath('/approval/flows')).toBe('/approval/flows')
  })

  it('dịch link kiểu app cũ sang đường dẫn phân hệ', () => {
    expect(toAppPath('/purchase-orders/12')).toBe('/procurement/purchase-orders/12')
    expect(toAppPath('/employees')).toBe('/hr/employees')
    //  Thông báo phiếu hỗ trợ: backend vẫn ghi `/tickets/{id}`, phải rơi đúng
    //  vào chi tiết phiếu ở phân hệ Hỗ trợ chứ không trả null.
    expect(toAppPath('/tickets/12')).toBe('/support/tickets/12')
    //  Mẻ nhập: backend ghi `/import-batches/{id}` (import_tool/tasks.py); từ
    //  Đ-13a màn Quản lý Import đã có ở phân hệ Quản trị nên phải dịch được.
    expect(toAppPath('/import-batches/3')).toBe('/system/imports/3')
  })

  it('link «Xử lý khảo sát» kiểu cũ phải rơi về chi tiết YCBG, không giữ đuôi /process', () => {
    //  LỖI ĐÃ XẢY RA (29/08/2026): backend ghi `/survey-requests/{id}/process`
    //  khi phiếu được duyệt / dòng được gán NSTM. Bảng tiền tố dịch máy móc
    //  thành `/procurement/survey-requests/{id}/process` — route không tồn tại
    //  ở v2 (màn Xử lý khảo sát đã gộp vào chi tiết) nên bấm thông báo ăn 404.
    expect(toAppPath('/survey-requests/2927/process')).toBe(
      '/procurement/survey-requests/2927',
    )
    //  Link chi tiết thường thì vẫn đi theo bảng tiền tố như cũ.
    expect(toAppPath('/survey-requests/2927')).toBe('/procurement/survey-requests/2927')
  })

  it('giữ nguyên link đã ở dạng phân hệ, không dịch lần hai', () => {
    expect(toAppPath('/procurement/purchase-orders/12')).toBe(
      '/procurement/purchase-orders/12',
    )
  })

  it('màn hình v2 chưa có thì trả null để đứng yên, không quăng vào trang trắng', () => {
    expect(toAppPath('/payment-requests/9')).toBeNull()
  })

  it('không khớp nửa vời: `/documents` khác `/document`', () => {
    //  `startsWith` trần sẽ cho `/documentation` lọt qua nhánh `/document`.
    expect(toAppPath('/documentation')).toBeNull()
  })

  it('chuỗi rỗng không nổ', () => {
    expect(toAppPath('')).toBeNull()
  })
})

describe('V2_PREFIXES', () => {
  it('phủ hết phân hệ đang bật — thêm phân hệ mà quên khai là thông báo chết', () => {
    //  Ràng buộc dữ liệu, không phải test hành vi: hai danh sách nằm hai nơi thì
    //  sớm muộn cũng lệch, mà lệch ở đây là im lặng — thông báo vẫn hiện, bấm
    //  vào không đi đâu, không có lỗi nào để lần ra.
    const thieu = allModules
      .filter((m) => m.enabled)
      //  Phân hệ Hướng dẫn sử dụng chỉ là link ra app ngoài, không có route v2.
      .filter((m) => m.path.startsWith('/'))
      .map((m) => m.path)
      .filter((path) => !V2_PREFIXES.includes(path))

    expect(thieu).toEqual([])
  })
})
