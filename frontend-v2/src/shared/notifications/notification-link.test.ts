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
  })

  it('giữ nguyên link đã ở dạng phân hệ, không dịch lần hai', () => {
    expect(toAppPath('/procurement/purchase-orders/12')).toBe(
      '/procurement/purchase-orders/12',
    )
  })

  it('màn hình v2 chưa có thì trả null để đứng yên, không quăng vào trang trắng', () => {
    expect(toAppPath('/payment-requests/9')).toBeNull()
    expect(toAppPath('/import-batches/3')).toBeNull()
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
