import { describe, expect, it } from 'vitest'

import { mergePendingFiles } from './merge-pending-files'

/**
 * Gom tệp chờ gửi kèm bình luận.
 *
 * Tệp vào ô soạn bằng BA đường — chọn tay, dán ảnh, kéo thả — nên hàm này chạy
 * ở cả ba. Hỏng ở đây thì hoặc người dùng gõ xong cả đoạn mới bị backend từ
 * chối vì thừa tệp, hoặc gửi lên hai bản y hệt nhau.
 */

const MAX = 5

/** `lastModified` cố định để hai tệp cùng tên/cỡ được coi là MỘT. */
function tep(name: string, noiDung = 'x', lastModified = 1_000): File {
  return new File([noiDung], name, { lastModified })
}

const ten = (files: File[]) => files.map((f) => f.name)

describe('mergePendingFiles', () => {
  it('nối tệp mới vào cuối, giữ nguyên thứ tự người dùng đưa vào', () => {
    const ket = mergePendingFiles([tep('a.png')], [tep('b.pdf'), tep('c.xlsx')], MAX)
    expect(ten(ket)).toEqual(['a.png', 'b.pdf', 'c.xlsx'])
  })

  it('CẮT ở trần, không để lọt tệp thứ sáu', () => {
    //  Dán một lượt mười ảnh chụp màn hình là chuyện thường.
    const nhieu = Array.from({ length: 10 }, (_, i) => tep(`anh-${i}.png`))
    expect(mergePendingFiles([], nhieu, MAX)).toHaveLength(MAX)
  })

  it('đã ĐẦY thì thêm nữa không ăn, và không làm rụng tệp đang có', () => {
    const day = Array.from({ length: MAX }, (_, i) => tep(`cu-${i}.png`))
    const ket = mergePendingFiles(day, [tep('moi.png')], MAX)
    expect(ten(ket)).toEqual(ten(day))
  })

  it('bỏ TRÙNG khi dán lại đúng tệp vừa dán', () => {
    //  `File` không có id; hai tệp trùng tên + cỡ + lần sửa cuối coi như một.
    const a = tep('bao-gia.pdf')
    const ket = mergePendingFiles([a], [tep('bao-gia.pdf')], MAX)
    expect(ten(ket)).toEqual(['bao-gia.pdf'])
  })

  it('bỏ trùng NGAY TRONG một lượt thả nhiều tệp', () => {
    const ket = mergePendingFiles([], [tep('a.png'), tep('a.png'), tep('b.png')], MAX)
    expect(ten(ket)).toEqual(['a.png', 'b.png'])
  })

  it('CÙNG TÊN nhưng khác nội dung thì GIỮ CẢ HAI', () => {
    //  Hai bản báo giá khác nhau, người dùng đặt trùng tên — nuốt mất một cái là
    //  âm thầm làm hỏng ý định của họ.
    const ket = mergePendingFiles([tep('bao-gia.pdf', 'ban-1')], [tep('bao-gia.pdf', 'ban-hai-dai-hon')], MAX)
    expect(ket).toHaveLength(2)
  })

  it('cùng tên cùng cỡ nhưng khác LẦN SỬA thì vẫn là hai tệp', () => {
    const ket = mergePendingFiles([tep('a.png', 'x', 1)], [tep('a.png', 'x', 2)], MAX)
    expect(ket).toHaveLength(2)
  })

  it('trần đúng bằng 1 thì chỉ nhận một tệp', () => {
    expect(mergePendingFiles([], [tep('a.png'), tep('b.png')], 1)).toHaveLength(1)
  })

  it('trần 0 hoặc ÂM thì không nhận gì — không được hiểu thành đếm ngược', () => {
    //  `slice(0, -1)` cắt từ cuối và vẫn trả về vài phần tử; đó là cái bẫy.
    for (const max of [0, -1, -3]) {
      expect(mergePendingFiles([tep('a.png')], [tep('b.png')], max)).toEqual([])
    }
  })

  it('không thêm gì thì trả đúng bộ cũ', () => {
    const cu = [tep('a.png')]
    expect(ten(mergePendingFiles(cu, [], MAX))).toEqual(['a.png'])
  })

  it('cả hai đều rỗng thì ra mảng rỗng, không nổ', () => {
    expect(mergePendingFiles([], [], MAX)).toEqual([])
  })

  it('KHÔNG sửa mảng gốc — component giữ nó trong state', () => {
    //  Sửa tại chỗ thì React không thấy tham chiếu đổi và bỏ qua lần vẽ lại.
    const cu = [tep('a.png')]
    const ket = mergePendingFiles(cu, [tep('b.png')], MAX)
    expect(cu).toHaveLength(1)
    expect(ket).not.toBe(cu)
  })

  it('bộ đang có ĐÃ vượt trần thì không nhận thêm, cũng không cắt bớt', () => {
    //  Trạng thái này chỉ xảy ra nếu trần bị hạ xuống giữa chừng; đừng lặng lẽ
    //  vứt tệp người dùng đã chọn.
    const qua = Array.from({ length: 7 }, (_, i) => tep(`x-${i}.png`))
    expect(mergePendingFiles(qua, [tep('moi.png')], MAX)).toHaveLength(7)
  })

  it('tệp cỡ 0 byte vẫn được nhận', () => {
    //  Tệp rỗng là dữ liệu hợp lệ; chặn ở đây là chặn nhầm chỗ (backend lo).
    const rong = new File([], 'rong.txt', { lastModified: 1 })
    expect(mergePendingFiles([], [rong], MAX)).toHaveLength(1)
  })
})
