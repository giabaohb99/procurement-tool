import { describe, expect, it } from 'vitest'

import { nameInitials } from './name-initials'

describe('nameInitials', () => {
  it('lấy chữ đầu của hai từ cuối nên hai người khác nhau không ra cùng một chữ tắt', () => {
    //  Đúng ca đã hỏng trên màn Quản lý dự án: bản cũ lấy hai ký tự đầu của TỪ
    //  CUỐI nên cả hai người đều ra «MỘ», hai vòng tròn cạnh nhau giống hệt.
    expect(nameInitials('Nguyễn Văn Nhân Sự Một')).toBe('SM')
    expect(nameInitials('Phạm Thị Kế Toán Một')).toBe('TM')
  })

  it('giữ dấu tiếng Việt ở dạng hoa', () => {
    expect(nameInitials('Lý Phó Phòng')).toBe('PP')
    expect(nameInitials('Trần Đình Ước')).toBe('ĐƯ')
  })

  it('tên hai từ kiểu tài khoản hệ thống vẫn ra hai chữ', () => {
    expect(nameInitials('Dego Admin')).toBe('DA')
  })

  it('một từ duy nhất thì lấy hai ký tự đầu của chính nó', () => {
    expect(nameInitials('Admin')).toBe('AD')
    //  Từ một ký tự: trả đúng một ký tự, KHÔNG đệm thêm gì.
    expect(nameInitials('A')).toBe('A')
  })

  it('chuỗi rỗng hoặc toàn khoảng trắng ra dấu hỏi, không ra chuỗi rỗng', () => {
    //  Chuỗi rỗng lọt xuống giao diện là một vòng tròn trắng trơn — nhìn như lỗi
    //  tải ảnh chứ không như "chưa có tên".
    expect(nameInitials('')).toBe('?')
    expect(nameInitials('   ')).toBe('?')
    expect(nameInitials('\t\n ')).toBe('?')
  })

  it('chịu được null và undefined lọt từ API xuống', () => {
    //  `WorkMember.employee_name` khai là `string`, nhưng nó tới từ JSON của máy
    //  chủ — hồ sơ nhân sự bị xoá thì trường này về `null` chứ không về "".
    expect(nameInitials(null as unknown as string)).toBe('?')
    expect(nameInitials(undefined as unknown as string)).toBe('?')
  })

  it('gộp mọi loại khoảng trắng thừa, kể cả xuống dòng giữa tên', () => {
    expect(nameInitials('  Nguyễn   Nhân    Viên  ')).toBe('NV')
    expect(nameInitials('Nguyễn\nNhân\tViên')).toBe('NV')
  })

  it('tên dài bất thường vẫn chỉ ra ĐÚNG hai ký tự', () => {
    //  Ô tên là `String(255)`; ai đó dán cả một câu vào thì vòng tròn avatar
    //  không được phép phình ra theo.
    const long = Array.from({ length: 200 }, (_, i) => `Từ${i}`).join(' ')
    expect(nameInitials(long)).toHaveLength(2)
  })

  it('không cắt đôi ký tự ngoài BMP dán vào ô tên', () => {
    //  `slice(0, 1)` trên emoji trả về nửa cặp surrogate — hiện thành ô vuông.
    //  `Array.from` đếm theo điểm mã nên lấy trọn ký tự.
    expect(Array.from(nameInitials('😀'))).toHaveLength(1)
    expect(nameInitials('😀 Bình')).toBe('😀B')
  })

  it('ký tự lạ không phải chữ cái vẫn đi qua nguyên vẹn, không thành rỗng', () => {
    expect(nameInitials('#1 Kho')).toBe('#K')
    expect(nameInitials('123')).toBe('12')
  })
})
