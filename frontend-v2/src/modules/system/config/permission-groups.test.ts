import { describe, expect, it } from 'vitest'

import {
  buildPermissionTree,
  filterPermissionTree,
  type MetaEntity,
} from './permission-groups'

const e = (key: string, label = key): MetaEntity => ({ key, label })

describe('buildPermissionTree', () => {
  it('groups vehicle entities under Đặt xe in the declared order', () => {
    const tree = buildPermissionTree([e('driver', 'Tài xế'), e('vehicle_booking'), e('vehicle')])
    const datxe = tree.find((g) => g.id === 'vehicle-booking')
    expect(datxe?.title).toBe('Đặt xe')
    // Thứ tự theo khai báo (vehicle_booking, vehicle, driver), KHÔNG theo thứ tự đầu vào.
    expect(datxe?.entities.map((x) => x.key)).toEqual(['vehicle_booking', 'vehicle', 'driver'])
  })

  it('keeps the label coming from meta, not a hard-coded one', () => {
    const tree = buildPermissionTree([e('vehicle', 'Phương tiện (Xe)')])
    expect(tree[0].entities[0].label).toBe('Phương tiện (Xe)')
  })

  it('drops groups that have no present entity', () => {
    const tree = buildPermissionTree([e('vehicle_booking')])
    // Chỉ còn nhóm Đặt xe, không có Thu mua/Văn thư… rỗng.
    expect(tree.map((g) => g.id)).toEqual(['vehicle-booking'])
  })

  it('puts unknown entities into a trailing "Khác" group so nothing disappears', () => {
    const tree = buildPermissionTree([e('vehicle_booking'), e('brand_new_thing', 'Thứ mới')])
    const last = tree[tree.length - 1]
    expect(last.id).toBe('__other__')
    expect(last.title).toBe('Khác')
    expect(last.entities.map((x) => x.key)).toEqual(['brand_new_thing'])
  })

  it('never assigns an entity to two groups', () => {
    const tree = buildPermissionTree([e('report'), e('purchase_request')])
    const keys = tree.flatMap((g) => g.entities.map((x) => x.key))
    expect(keys.length).toBe(new Set(keys).size)
  })

  it('returns an empty array for empty meta', () => {
    expect(buildPermissionTree([])).toEqual([])
  })

  it('does not lose any entity — every input key appears exactly once', () => {
    const input = [
      e('vehicle_booking'),
      e('document'),
      e('employee'),
      e('setting'),
      e('some_future_entity'),
    ]
    const out = buildPermissionTree(input)
        .flatMap((g) => g.entities.map((x) => x.key))
        .sort()
    expect(out).toEqual(input.map((x) => x.key).sort())
  })
})

describe('filterPermissionTree', () => {
  const tree = buildPermissionTree([
    e('vehicle_booking', 'Yêu cầu đặt xe'),
    e('vehicle', 'Phương tiện (Xe)'),
    e('driver', 'Tài xế'),
    e('purchase_order', 'Đơn mua hàng'),
    e('purchase_request', 'Yêu cầu mua hàng'),
    e('document', 'Văn bản'),
  ])

  const shape = (groups: ReturnType<typeof buildPermissionTree>) =>
    groups.map((g) => [g.id, g.entities.map((x) => x.key)] as const)

  it('từ khóa rỗng trả NGUYÊN cây, cùng tham chiếu (không dựng lại mỗi lượt render)', () => {
    expect(filterPermissionTree(tree, '')).toBe(tree)
    expect(filterPermissionTree(tree, '   ')).toBe(tree)
  })

  it('khớp TÊN PHÂN HỆ thì giữ ĐỦ mục con, không chỉ mục có chữ đó', () => {
    // Gõ "thu mua" là muốn cả phân hệ Thu mua — "Văn bản" không có chữ đó nhưng
    // cũng không được rơi vào đây.
    const out = filterPermissionTree(tree, 'đặt xe')
    expect(shape(out)).toEqual([['vehicle-booking', ['vehicle_booking', 'vehicle', 'driver']]])
  })

  it('không khớp tên nhóm thì chỉ giữ mục con khớp', () => {
    const out = filterPermissionTree(tree, 'đơn mua')
    expect(shape(out)).toEqual([['procurement', ['purchase_order']]])
  })

  it('BỎ DẤU vẫn khớp — người Việt gõ ô tìm thường không bỏ dấu', () => {
    expect(shape(filterPermissionTree(tree, 'don mua hang'))).toEqual([
      ['procurement', ['purchase_order']],
    ])
    // Chữ đ/Đ không phải d có dấu nên NFD không xử được, phải thay tay.
    expect(shape(filterPermissionTree(tree, 'dat xe'))).toEqual([
      ['vehicle-booking', ['vehicle_booking', 'vehicle', 'driver']],
    ])
  })

  it('tìm được bằng MÃ entity — mã là thứ nằm trong tài liệu và trong lỗi 403', () => {
    expect(shape(filterPermissionTree(tree, 'purchase_request'))).toEqual([
      ['procurement', ['purchase_request']],
    ])
  })

  it('không khớp gì thì trả mảng rỗng, KHÔNG trả cả cây', () => {
    // Trả cả cây là kiểu hỏng tệ nhất: người dùng tưởng mọi dòng đều khớp, và
    // "chọn hết đang hiện" sẽ cấp quyền cho toàn hệ.
    expect(filterPermissionTree(tree, 'khong-co-thu-nay')).toEqual([])
  })

  it('không sửa cây gốc (nhóm bị cắt bớt phải là bản sao)', () => {
    const before = shape(tree)
    filterPermissionTree(tree, 'đơn mua')
    expect(shape(tree)).toEqual(before)
  })

  it('một ký tự cũng lọc, không đợi đủ độ dài', () => {
    // Không có ngưỡng "gõ từ 2 ký tự mới tìm": ngưỡng như vậy làm ô tìm im lặng
    // ở đúng lúc người dùng vừa bắt đầu gõ.
    expect(filterPermissionTree(tree, 'x').length).toBeGreaterThan(0)
  })
})
