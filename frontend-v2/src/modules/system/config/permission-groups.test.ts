import { describe, expect, it } from 'vitest'

import { buildPermissionTree, type MetaEntity } from './permission-groups'

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
