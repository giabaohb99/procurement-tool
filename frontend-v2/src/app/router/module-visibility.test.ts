import { describe, expect, it } from 'vitest'

import { FileText } from 'lucide-react'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { ErpModule } from './module-definition'
import {
  canAccessRoute,
  canOpenModule,
  firstAccessibleNavPath,
  visibleNavItems,
} from './module-visibility'
import { allModules, moduleRegistry } from './module-registry'

function module(nav: ErpModule['nav'], entity?: string): ErpModule {
  return { id: 'x', title: 'X', path: '/x', enabled: true, entity, nav } as ErpModule
}

/** `can` giả lập: chỉ mấy entity trong danh sách là đọc được. */
function allow(...duoc: string[]) {
  return (entity: PermissionEntity) => duoc.includes(entity)
}

describe('canOpenModule', () => {
  //  LỖI THẬT (22/08/2026): màn chọn phân hệ chỉ xét `module.entity`, nên
  //  DEMO_MANAGER — người ký ở ba trong bốn chặng luồng ban hành văn bản — thấy
  //  ô «Văn bản» đeo ổ khóa. Chuông báo 6 việc chờ mà không vào nổi chỗ để duyệt.
  it('người duyệt không có quyền trên phân hệ vẫn mở được nếu có mục không gác quyền', () => {
    const document = module(
      [
        { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
        //  «Chờ tôi duyệt» cố ý không khai `entity`.
        { label: 'Chờ tôi duyệt', path: '/d/pending', icon: FileText },
      ],
      'document',
    )

    expect(canOpenModule(document, allow())).toBe(true)
  })

  it('không thấy mục nào thì mới khóa', () => {
    const document = module([{ label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText }], 'document')

    expect(canOpenModule(document, allow())).toBe(false)
    expect(canOpenModule(document, allow('document'))).toBe(true)
  })

  it('có quyền một mục bất kỳ là mở được, không cần đúng entity của phân hệ', () => {
    const document = module(
      [
        { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
        { label: 'Sổ văn bản', path: '/d/books', entity: 'document_book', icon: FileText },
      ],
      'document',
    )

    expect(canOpenModule(document, allow('document_book'))).toBe(true)
  })

  it('phân hệ không có mục nào thì khóa, không sập', () => {
    expect(canOpenModule(module([]), allow())).toBe(false)
  })

  //  Thu mua mượn hai màn của Tài chính làm lối tắt (`crossModule`, 31/08/2026).
  //  Đếm cả lối tắt thì kế toán chỉ có `payable.read` thấy thẻ Thu mua mở, bấm
  //  vào rỗng tuếch — đúng lỗi «thẻ mở cho người ngoài phân hệ» đã vá 27/08.
  it('lối tắt sang phân hệ khác KHÔNG tự mở khóa thẻ phân hệ này', () => {
    const procurement = module([
      { label: 'YCMH', path: '/x/pr', entity: 'purchase_request', icon: FileText },
      {
        label: 'Công nợ phải trả',
        path: '/finance/payables',
        entity: 'payable',
        crossModule: true,
        icon: FileText,
      },
    ])

    expect(canOpenModule(procurement, allow('payable'))).toBe(false)
    expect(canOpenModule(procurement, allow('purchase_request'))).toBe(true)
  })

  it('nhưng vào được rồi thì lối tắt vẫn hiện trên menu theo quyền của nó', () => {
    const procurement = module([
      { label: 'YCMH', path: '/x/pr', entity: 'purchase_request', icon: FileText },
      {
        label: 'Công nợ phải trả',
        path: '/finance/payables',
        entity: 'payable',
        crossModule: true,
        icon: FileText,
      },
    ])

    expect(visibleNavItems(procurement, allow('purchase_request')).map((i) => i.label)).toEqual([
      'YCMH',
    ])
    expect(
      visibleNavItems(procurement, allow('purchase_request', 'payable')).map((i) => i.label),
    ).toEqual(['YCMH', 'Công nợ phải trả'])
  })
})

describe('visibleNavItems', () => {
  it('giữ lại mục không gác quyền và mục đã có quyền, bỏ phần còn lại', () => {
    const nav = [
      { label: 'Tổng quan', path: '/d', icon: FileText },
      { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
      { label: 'Sổ', path: '/d/books', entity: 'document_book', icon: FileText },
    ] as ErpModule['nav']

    expect(visibleNavItems(module(nav), allow('document_book')).map((i) => i.label)).toEqual([
      'Tổng quan',
      'Sổ',
    ])
  })
})

/** `can` giả lập theo (entity, action): map entity -> tập action được phép. */
function allowFullRow(map: Record<string, PermissionAction[]>) {
  return (entity: PermissionEntity, action: PermissionAction) =>
    (map[entity] ?? []).includes(action)
}

describe('canAccessRoute', () => {
  const navEmp = [
    { label: 'Nhân sự', path: '/x/emp', entity: 'employee', icon: FileText },
  ] as ErpModule['nav']

  it('trang chi tiết ăn theo quyền của mục danh sách khớp path dài nhất', () => {
    // /x/emp/5 không có mục riêng -> lấy quyền của /x/emp (entity=employee, read).
    expect(canAccessRoute(module(navEmp), '/x/emp/5', allow())).toBe(false)
    expect(canAccessRoute(module(navEmp), '/x/emp/5', allow('employee'))).toBe(true)
  })

  it('mục cụ thể hơn mà cố ý KHÔNG gác quyền thì cho xem, dù không có quyền entity cha', () => {
    // Mục con công khai (không entity) phải thắng mục cha có entity nhờ path dài hơn —
    // nếu ưu tiên nhầm mục cha, màn công khai sẽ bị khóa oan.
    const nav = [
      { label: 'Nhân sự', path: '/x/emp', entity: 'employee', icon: FileText },
      { label: 'Danh bạ công khai', path: '/x/emp/dir', icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(module(nav), '/x/emp/dir/9', allow())).toBe(true)
  })

  it('không mục nào khớp thì cho xem (backend vẫn gác)', () => {
    expect(canAccessRoute(module(navEmp), '/x/khac', allow())).toBe(true)
  })

  it('mục khai action riêng thì hỏi đúng action đó, không phải read', () => {
    const nav = [
      { label: 'Chờ duyệt', path: '/x/duyet', entity: 'document', action: 'approve', icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(module(nav), '/x/duyet', allowFullRow({ document: ['read'] }))).toBe(false)
    expect(canAccessRoute(module(nav), '/x/duyet', allowFullRow({ document: ['approve'] }))).toBe(true)
  })

  it('mục quản lý (manage) đòi quyền tạo/sửa/xóa, read thuần không đủ', () => {
    const nav = [
      { label: 'Danh mục', path: '/x/dm', entity: 'unit', manage: true, icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(module(nav), '/x/dm', allowFullRow({ unit: ['read'] }))).toBe(false)
    expect(canAccessRoute(module(nav), '/x/dm', allowFullRow({ unit: ['write'] }))).toBe(true)
  })
})

/**
 * ─── Đáp xuống đâu khi KHÔNG xem được trang gốc (bao-CR-380) ───
 *
 * Lỗi khách báo 11/09/2026: tài khoản chỉ có `warehouse.read` bấm vào phân hệ
 * Kho là rơi thẳng vào Tổng quan rồi ăn một ô đỏ, trong khi *Danh mục Kho* ngay
 * bên dưới họ xem được. Người dùng đọc ra "không có quyền vào Kho" và dừng lại.
 */
describe('firstAccessibleNavPath', () => {
  const navKho = [
    { label: 'Tổng quan', path: '/x', entity: 'inventory', icon: FileText },
    { label: 'Tồn kho', path: '/x/stock', entity: 'inventory', icon: FileText },
    { label: 'Danh mục Kho', path: '/x/warehouses', entity: 'warehouse', icon: FileText },
  ] as ErpModule['nav']

  it('trả về màn đầu tiên xem được, KHÔNG trả về chính trang gốc', () => {
    expect(firstAccessibleNavPath(module(navKho), allow('warehouse'))).toBe('/x/warehouses')
  })

  it('xem được trang gốc thì vẫn trả màn khác — nơi gọi tự quyết có dùng hay không', () => {
    //  `ModuleLayout` chỉ hỏi hàm này khi trang gốc đã bị chặn, nên hàm không
    //  cần tự biết điều đó. Giữ hợp đồng đơn giản: "màn đầu tiên KHÁC trang gốc".
    expect(firstAccessibleNavPath(module(navKho), allow('inventory'))).toBe('/x/stock')
  })

  it('không còn màn nào xem được thì trả null, đừng đẩy người ta vào vòng lặp', () => {
    expect(firstAccessibleNavPath(module(navKho), allow())).toBeNull()
  })

  it('BỎ QUA lối tắt sang phân hệ khác — đá người ta ra ngoài còn khó hiểu hơn', () => {
    const nav = [
      { label: 'Tổng quan', path: '/x', entity: 'inventory', icon: FileText },
      { label: 'Công nợ', path: '/finance/payables', entity: 'payable', crossModule: true, icon: FileText },
    ] as ErpModule['nav']

    expect(firstAccessibleNavPath(module(nav), allow('payable'))).toBeNull()
  })

  it('BỎ QUA mục ẩn — đẩy tới đó thì menu trái không mục nào sáng', () => {
    const nav = [
      { label: 'Tổng quan', path: '/x', entity: 'inventory', icon: FileText },
      { label: 'Loại nghỉ', path: '/x/leave-types', entity: 'leave_type', hidden: true, icon: FileText },
    ] as ErpModule['nav']

    expect(firstAccessibleNavPath(module(nav), allow('leave_type'))).toBeNull()
  })

  it('người chỉ giữ danh mục kho KHÔNG còn đáp xuống Tổng quan của phân hệ Kho', () => {
    //  Chạy trên phân hệ THẬT: hai luật (mục menu và trang bên trong) từng lệch
    //  nhau đúng ở đây — menu mời vào bằng `entities: [inventory, warehouse]`,
    //  trang lại đòi `inventory.read`.
    const kho = moduleRegistry.find((m) => m.id === 'inventory')
    expect(kho).toBeDefined()
    if (!kho) return

    const chiCoDanhMuc = allow('warehouse')
    expect(canAccessRoute(kho, kho.path, chiCoDanhMuc)).toBe(false)
    expect(firstAccessibleNavPath(kho, chiCoDanhMuc)).toBe('/inventory/warehouses')
  })
})

describe('mục gom nhiều màn con (`entities`)', () => {
  //  «Thiết lập văn bản» là MỘT mục menu chứa bốn tab chạy trên bốn khóa khác
  //  nhau. Trước CR-157 nó gác bằng đúng `doc_type`, nên người chỉ giữ *Đơn vị
  //  gửi nhận* không vào nổi trang chứa đúng tab của mình.
  const thietLap = [
    {
      label: 'Thiết lập văn bản',
      path: '/d/settings',
      icon: FileText,
      entities: ['doc_type', 'doc_template', 'security_level', 'external_party'],
    },
  ] as ErpModule['nav']

  it('có quyền trên BẤT KỲ khóa nào là hiện mục', () => {
    expect(visibleNavItems(module(thietLap), allow('external_party'))).toHaveLength(1)
    expect(visibleNavItems(module(thietLap), allow('doc_type'))).toHaveLength(1)
  })

  it('không có khóa nào thì ẩn — đừng biến nó thành mục ai cũng thấy', () => {
    expect(visibleNavItems(module(thietLap), allow('document'))).toHaveLength(0)
  })

  it('mảng rỗng thì coi như không gác, giống mục bỏ trống `entity`', () => {
    const nav = [
      { label: 'Chờ tôi duyệt', path: '/d/pending', icon: FileText, entities: [] },
    ] as ErpModule['nav']
    expect(visibleNavItems(module(nav), allow())).toHaveLength(1)
  })
})

describe('phân hệ LINK RA NGOÀI', () => {
  /** Đúng hình dạng `helpCenterModule`: không màn hình nào trong app này. */
  function externalLink(): ErpModule {
    return {
      id: 'help-center',
      title: 'Hướng dẫn sử dụng',
      path: '',
      externalUrl: () => 'http://localhost:8082',
      enabled: true,
      nav: [],
      routes: [],
    } as unknown as ErpModule
  }

  //  LỖI KHÁCH BÁO 25/08/2026: ô «Hướng dẫn sử dụng» đeo ổ khóa, không ai bấm
  //  vào được — kể cả admin. `canOpenModule` đo bằng "còn mục menu nào hiện
  //  không", mà phân hệ link ra ngoài có `nav: []` theo đúng bản chất nên luôn
  //  ra 0. Tài liệu dùng hệ thống mà không ai mở được là hỏng đúng chỗ đáng giá.
  it('luôn mở, kể cả tài khoản không có quyền nào', () => {
    expect(canOpenModule(externalLink(), allow())).toBe(true)
  })

  it('không phụ thuộc quyền của người dùng', () => {
    expect(canOpenModule(externalLink(), allow('help_article'))).toBe(true)
  })

  //  Chốt chiều ngược: đừng nới thành "phân hệ nào không có mục menu cũng mở".
  it('phân hệ THƯỜNG mà không thấy mục nào thì vẫn khóa', () => {
    expect(canOpenModule(module([]), allow())).toBe(false)
  })
})

/**
 * ─── B3/B4/B5: chạy trên BẢNG ĐĂNG KÝ THẬT, không phải phân hệ giả ───
 *
 * Mấy khẳng định trên kiểm đúng LUẬT của `module-visibility`. Nhóm dưới đây
 * kiểm luật đó áp lên 20 phân hệ có thật — chỗ mà một mục khai thiếu, một
 * đường dẫn gõ nhầm hay một mục công khai đặt sai chỗ sẽ lọt qua mọi bài kiểm
 * dùng dữ liệu bịa.
 */
const DENY_ALL = () => false

describe('B3 — gõ thẳng URL màn không có quyền', () => {
  it('mọi mục CÓ gác quyền đều bị chặn khi tài khoản không có quyền nào', () => {
    //  Không chỉ là nhắc lại `itemAllowed`: `canAccessRoute` chọn mục khớp path
    //  DÀI NHẤT, nên một mục công khai (`/hr/emp/dir`) đặt trùm lên một mục có
    //  gác sẽ âm thầm mở khóa màn kia. Bài này bắt đúng chuyện đó.
    const lot: string[] = []
    for (const module of moduleRegistry) {
      for (const item of module.nav) {
        if (!item.entity && !item.entities?.length) continue
        if (canAccessRoute(module, item.path, DENY_ALL)) {
          lot.push(`${module.id} - ${item.label} (${item.path})`)
        }
      }
    }
    expect(lot).toEqual([])
  })

  it('trang CHI TIẾT của mục có gác cũng bị chặn, không chỉ trang danh sách', () => {
    //  `/x/y/5` không có mục riêng -> phải ăn theo quyền của `/x/y`. Nếu không,
    //  người bị chặn ở danh sách chỉ cần gõ thêm một id là vào được.
    const lot: string[] = []
    for (const module of moduleRegistry) {
      for (const item of module.nav) {
        if (!item.entity && !item.entities?.length) continue
        if (canAccessRoute(module, `${item.path}/12345`, DENY_ALL)) {
          lot.push(`${module.id} - ${item.label}`)
        }
      }
    }
    expect(lot).toEqual([])
  })
})

describe('B4 — thẻ phân hệ khi không có quyền nào', () => {
  it('chỉ ba phân hệ CÔNG KHAI (+ phân hệ link ra ngoài) là mở', () => {
    //  Danh sách chủ ý, giữ song song với `module-registry.test.ts`. Thêm tên
    //  vào đây phải kèm lý do, kẻo lại tái diễn lỗi 27/08/2026: thẻ phân hệ mở
    //  cho người ngoài, vào trong toàn số 0.
    const congKhai = new Set([
      'document', // «Chờ tôi duyệt» dành cho người duyệt NGOÀI phân hệ
      'forum', // bảng tin toàn công ty
      'appearance', // tùy chọn hiển thị của chính người đăng nhập
      //  ⚠️ **Hồ sơ (`dossier`) CỐ Ý không nằm ở đây** — xem ghi chú song song ở
      //  `module-registry.test.ts`. Phân hệ chỉ còn danh mục *Loại hồ sơ*, gác đủ
      //  bằng `dossier_type`, nên thẻ của nó đóng với người không quản danh mục.
      //  «Dego Coffee» từng công khai qua «Ví điểm của tôi», nhưng phân hệ nay TẮT
      //  (`enabled: false`, phần Điểm cà phê còn dở) nên không nằm trong moduleRegistry.
    ])
    //  Chỉ xét phân hệ ĐANG BẬT: phân hệ tắt (`sales`, `approval-seal`, `dego-coffee`)
    //  mới có mỗi mục «Tổng quan»/công khai nhưng không vào router nên không ai mở được.
    const mo = moduleRegistry
      .filter((m) => !m.externalUrl && canOpenModule(m, DENY_ALL))
      .map((m) => m.id)
    expect(new Set(mo)).toEqual(congKhai)
  })
})

describe('B5 — phân hệ đang tắt', () => {
  it('không nằm trong bảng đăng ký, nên không có route và không dò được theo URL', () => {
    for (const module of allModules.filter((m) => !m.enabled)) {
      expect(moduleRegistry.map((m) => m.id), module.id).not.toContain(module.id)
    }
  })

  it('bảng đăng ký chỉ chứa phân hệ đang bật', () => {
    expect(moduleRegistry.filter((m) => !m.enabled)).toEqual([])
  })
})

describe('mục có submenu (children)', () => {
  it('lọc các mục con theo đúng quyền của từng mục con', () => {
    const hr = module([
      {
        label: 'Nghỉ phép',
        path: '/hr/leave-requests',
        entity: 'leave_request',
        children: [
          { label: 'Đơn nghỉ phép', path: '/hr/leave-requests', entity: 'leave_request' },
          { label: 'Quỹ phép', path: '/hr/leave-balances', entity: 'leave_balance' },
          { label: 'Thiết lập', path: '/hr/leave-types', entity: 'leave_type', manage: true },
        ],
      },
    ])

    // Chỉ có quyền xem đơn:
    const nhanVien = visibleNavItems(hr, allow('leave_request'))
    expect(nhanVien[0].children?.map((c) => c.label)).toEqual(['Đơn nghỉ phép'])

    // Có thêm quyền xem quỹ:
    const coQuy = visibleNavItems(hr, allow('leave_request', 'leave_balance'))
    expect(coQuy[0].children?.map((c) => c.label)).toEqual(['Đơn nghỉ phép', 'Quỹ phép'])
  })

  it('canAccessRoute kiểm tra đúng quyền của mục con', () => {
    const hr = module([
      {
        label: 'Nghỉ phép',
        path: '/hr/leave-requests',
        entities: ['leave_request', 'leave_balance'],
        children: [
          { label: 'Đơn nghỉ phép', path: '/hr/leave-requests', entity: 'leave_request' },
          { label: 'Quỹ phép', path: '/hr/leave-balances', entity: 'leave_balance' },
        ],
      },
    ])

    expect(canAccessRoute(hr, '/hr/leave-balances', allow('leave_request'))).toBe(false)
    expect(canAccessRoute(hr, '/hr/leave-balances', allow('leave_balance'))).toBe(true)
    expect(canAccessRoute(hr, '/hr/leave-requests', allow('leave_balance'))).toBe(false)
    expect(canAccessRoute(hr, '/hr/leave-requests', allow('leave_request'))).toBe(true)
  })
})

describe('Phân quyền cụm Nghỉ phép thực tế (hrModule)', () => {
  //  Không dùng `!`: module vắng thì ném lỗi rõ ràng thay vì nổ ở dòng khẳng định.
  const hr = (() => {
    const found = allModules.find((m) => m.id === 'hr')
    if (!found) throw new Error('Module hr chưa đăng ký trong module-registry')
    return found
  })()

  function makeCan(perms: Record<string, string[]>) {
    return (entity: PermissionEntity, action: PermissionAction = 'read') => {
      return perms[entity]?.includes(action) ?? false
    }
  }

  describe('Chặn truy cập trực tiếp qua URL (canAccessRoute)', () => {
    it('/hr/leave-requests: chỉ cho phép khi có quyền leave_request', () => {
      expect(canAccessRoute(hr, '/hr/leave-requests', makeCan({ leave_request: ['read'] }))).toBe(true)
      expect(canAccessRoute(hr, '/hr/leave-requests', makeCan({ leave_balance: ['read'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/leave-requests', makeCan({ leave_type: ['write'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/leave-requests', makeCan({}))).toBe(false)
    })

    it('/hr/leave-calendar: chỉ cho phép khi có quyền leave_request', () => {
      expect(canAccessRoute(hr, '/hr/leave-calendar', makeCan({ leave_request: ['read'] }))).toBe(true)
      expect(canAccessRoute(hr, '/hr/leave-calendar', makeCan({ leave_balance: ['read'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/leave-calendar', makeCan({}))).toBe(false)
    })

    it('/hr/leave-balances: chỉ cho phép khi có quyền leave_balance', () => {
      expect(canAccessRoute(hr, '/hr/leave-balances', makeCan({ leave_balance: ['read'] }))).toBe(true)
      expect(canAccessRoute(hr, '/hr/leave-balances', makeCan({ leave_request: ['read', 'create'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/leave-balances', makeCan({}))).toBe(false)
    })

    it('/hr/leave-types: đòi hỏi quyền quản lý (manage: true) trên leave_type hoặc holiday', () => {
      // Có quyền sửa/tạo loại nghỉ -> vào được
      expect(canAccessRoute(hr, '/hr/leave-types', makeCan({ leave_type: ['write'] }))).toBe(true)
      expect(canAccessRoute(hr, '/hr/leave-types', makeCan({ holiday: ['create'] }))).toBe(true)
      // Chỉ có quyền read (đổ dropdown) -> KHÔNG vào được màn quản lý
      expect(canAccessRoute(hr, '/hr/leave-types', makeCan({ leave_type: ['read'] }))).toBe(false)
      // Nhân viên thường có leave_request -> KHÔNG vào được
      expect(canAccessRoute(hr, '/hr/leave-types', makeCan({ leave_request: ['read', 'create', 'write'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/leave-types', makeCan({}))).toBe(false)
    })

    it('/hr/holidays: đòi hỏi quyền quản lý (manage: true) trên holiday', () => {
      expect(canAccessRoute(hr, '/hr/holidays', makeCan({ holiday: ['write'] }))).toBe(true)
      expect(canAccessRoute(hr, '/hr/holidays', makeCan({ holiday: ['read'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/holidays', makeCan({ leave_request: ['read'] }))).toBe(false)
      expect(canAccessRoute(hr, '/hr/holidays', makeCan({}))).toBe(false)
    })
  })

  describe('Hiển thị trên Sidebar (visibleNavItems)', () => {
    it('nhân viên thường (leave_request): chỉ thấy Đơn nghỉ phép và Lịch nghỉ', () => {
      const items = visibleNavItems(hr, makeCan({ leave_request: ['read'], employee: ['read'] }))
      const leaveMenu = items.find((i) => i.label === 'Nghỉ phép')
      expect(leaveMenu).toBeDefined()
      expect(leaveMenu?.children?.map((c) => c.label)).toEqual(['Đơn nghỉ phép', 'Lịch nghỉ'])
    })

    it('người quản lý quỹ phép (leave_balance): chỉ thấy Quỹ phép năm', () => {
      const items = visibleNavItems(hr, makeCan({ leave_balance: ['read'], employee: ['read'] }))
      const leaveMenu = items.find((i) => i.label === 'Nghỉ phép')
      expect(leaveMenu).toBeDefined()
      expect(leaveMenu?.children?.map((c) => c.label)).toEqual(['Quỹ phép năm'])
    })

    it('người quản lý danh mục (leave_type:write): chỉ thấy Thiết lập', () => {
      const items = visibleNavItems(hr, makeCan({ leave_type: ['write'], employee: ['read'] }))
      const leaveMenu = items.find((i) => i.label === 'Nghỉ phép')
      expect(leaveMenu).toBeDefined()
      expect(leaveMenu?.children?.map((c) => c.label)).toEqual(['Thiết lập'])
    })

    it('quản trị viên nhân sự có đủ mọi quyền: thấy trọn vẹn 4 mục', () => {
      const items = visibleNavItems(
        hr,
        makeCan({
          leave_request: ['read'],
          leave_balance: ['read'],
          leave_type: ['write'],
          holiday: ['write'],
          employee: ['read'],
        }),
      )
      const leaveMenu = items.find((i) => i.label === 'Nghỉ phép')
      expect(leaveMenu).toBeDefined()
      expect(leaveMenu?.children?.map((c) => c.label)).toEqual([
        'Đơn nghỉ phép',
        'Lịch nghỉ',
        'Quỹ phép năm',
        'Thiết lập',
      ])
    })

    it('tài khoản không có quyền nào thuộc cụm nghỉ phép: menu Nghỉ phép ẩn hoàn toàn', () => {
      const items = visibleNavItems(hr, makeCan({ employee: ['read'], department: ['read'] }))
      const leaveMenu = items.find((i) => i.label === 'Nghỉ phép')
      expect(leaveMenu).toBeUndefined()
    })
  })
})


describe('Tra cứu thị trường — submenu thật (procurementModule)', () => {
  const procurement = moduleRegistry.find((m) => m.id === 'procurement')
  if (!procurement) throw new Error('Thiếu phân hệ Thu mua')

  /** `can` giả lập theo từng cặp «khóa.hành động». */
  function grants(...cap: string[]) {
    return (entity: PermissionEntity, action: PermissionAction) => cap.includes(`${entity}.${action}`)
  }
  function customsChildren(can: ReturnType<typeof grants>) {
    const parent = visibleNavItems(procurement as ErpModule, can).find(
      (item) => item.path === '/procurement/customs-prices',
    )
    //  Chỉ mục VẼ trên menu — bỏ mục `hidden` (bốn thẻ tra giá gom về «Giá nhập khẩu»).
    return parent?.children?.filter((child) => !child.hidden).map((child) => child.path) ?? []
  }

  it('người chỉ ĐỌC dữ liệu hải quan thấy mọi mục trừ «Cấu hình» (kể cả «Thuốc BVTV»)', () => {
    const paths = customsChildren(grants('customs_price.read'))
    //  01/10/2026: «Giá nhập khẩu» (gom 5 thẻ) · Pháp lý · Thuốc BVTV · Lịch sử nạp.
    expect(paths).toEqual([
      '/procurement/customs-prices',
      '/procurement/customs-prices/legal',
      '/procurement/customs-prices/pesticides',
      '/procurement/customs-prices/history',
    ])
    expect(paths).not.toContain('/procurement/customs-prices/config')
  })

  //  Bốn thẻ tra giá không còn mục menu RIÊNG — gõ thẳng URL vẫn phải bị chặn bằng
  //  khóa `customs_price`, không rơi về nhánh "cho xem" của `canAccessRoute`.
  it('the four tab routes still require customs_price.read', () => {
    for (const section of ['chart', 'importers', 'compare', 'tariff']) {
      const path = `/procurement/customs-prices/${section}`
      expect(canAccessRoute(procurement as ErpModule, path, grants())).toBe(false)
      expect(canAccessRoute(procurement as ErpModule, path, grants('customs_price.read'))).toBe(true)
    }
  })

  //  «Cấu hình» có hai mức quyền trên hai khóa: QUẢN LÝ `customs_price` (từ khóa + đồng
  //  nghĩa) hoặc chỉ ĐỌC `customs_regulation` (danh mục hóa chất) — `alsoReadable`.
  it('chỉ đọc được danh mục hóa chất vẫn thấy và vào được «Cấu hình»', () => {
    const can = grants('customs_price.read', 'customs_regulation.read')
    expect(customsChildren(can)).toContain('/procurement/customs-prices/config')
    expect(
      canAccessRoute(procurement as ErpModule, '/procurement/customs-prices/config', can),
    ).toBe(true)
  })

  it('quản lý customs_price thì thấy «Cấu hình» dù không đọc được hóa chất', () => {
    expect(customsChildren(grants('customs_price.read', 'customs_price.write'))).toContain(
      '/procurement/customs-prices/config',
    )
  })

  it('gõ thẳng /config khi không có quyền nào của nó thì bị chặn', () => {
    expect(
      canAccessRoute(
        procurement as ErpModule,
        '/procurement/customs-prices/config',
        grants('customs_price.read'),
      ),
    ).toBe(false)
  })

  it('không có customs_price.read thì cả cụm biến mất', () => {
    expect(customsChildren(grants('customs_regulation.read'))).toEqual([])
  })
})


/**
 * ─── Gác KÉP báo cáo theo `reportKeys` (`ModuleNavItem.reportKeys` /
 * `NavContext.reportKeys`, 02/10/2026) ───
 *
 * Thiết kế ngược chiều mặc định "mục không khai entity thì luôn hiện": mục
 * CÓ khai `reportKeys` mà bối cảnh thiếu/rỗng/không chứa khóa thì luôn ẨN
 * (fail-closed), đúng chốt "chưa gán = đóng" của phân hệ Báo cáo.
 */
describe('reportKeys — gác kép báo cáo (fail-closed)', () => {
  function reportNav(reportKeys: readonly number[]): ErpModule['nav'] {
    return [
      { label: 'Báo cáo X', path: '/report/x', entity: 'report', reportKeys, icon: FileText },
    ] as ErpModule['nav']
  }

  it('ẩn khi ctx không có reportKeys (undefined) dù entity đọc được', () => {
    const m = module(reportNav([1]))
    expect(visibleNavItems(m, allow('report'), {})).toHaveLength(0)
  })

  it('ẩn khi ctx.reportKeys là mảng rỗng', () => {
    const m = module(reportNav([1]))
    expect(visibleNavItems(m, allow('report'), { reportKeys: [] })).toHaveLength(0)
  })

  it('ẩn khi ctx.reportKeys không chứa khóa của mục', () => {
    const m = module(reportNav([1]))
    expect(visibleNavItems(m, allow('report'), { reportKeys: [2, 3] })).toHaveLength(0)
  })

  it('hiện khi ctx.reportKeys chứa khóa VÀ đọc được entity', () => {
    const m = module(reportNav([1]))
    expect(visibleNavItems(m, allow('report'), { reportKeys: [1] })).toHaveLength(1)
  })

  it('có khóa đúng mà THIẾU entity thì vẫn ẩn — gác kép, thiếu một là đóng', () => {
    const m = module(reportNav([1]))
    expect(visibleNavItems(m, allow(), { reportKeys: [1] })).toHaveLength(0)
  })

  it('mục không khai reportKeys thì không bị luật này đụng tới', () => {
    const nav = [
      { label: 'Thường', path: '/x/binh-thuong', entity: 'report', icon: FileText },
    ] as ErpModule['nav']
    const m = module(nav)
    expect(visibleNavItems(m, allow('report'), {})).toHaveLength(1)
  })

  it("canAccessRoute('/report/work') false khi thiếu khóa — gõ thẳng URL vẫn bị chặn", () => {
    const report = moduleRegistry.find((mm) => mm.id === 'report')
    expect(report).toBeDefined()
    if (!report) return

    expect(canAccessRoute(report, '/report/work', allow('work_task'), {})).toBe(false)
    expect(canAccessRoute(report, '/report/work', allow('work_task'), { reportKeys: [13] })).toBe(
      true,
    )
  })

  it('firstAccessibleNavPath bỏ qua báo cáo CHƯA được gán, dù entity đọc được', () => {
    const nav = [
      { label: 'Tổng quan', path: '/report', entity: 'report', reportKeys: [1, 2], icon: FileText },
      { label: 'Báo cáo A', path: '/report/a', entity: 'report', reportKeys: [1], icon: FileText },
      { label: 'Báo cáo B', path: '/report/b', entity: 'report', reportKeys: [2], icon: FileText },
    ] as ErpModule['nav']
    const m = { ...module(nav), path: '/report' } as ErpModule

    //  Chỉ được gán khóa 2 (Báo cáo B) — khóa 1 (Báo cáo A) tuy đọc được entity
    //  vẫn phải bị BỎ QUA.
    expect(firstAccessibleNavPath(m, allow('report'), { reportKeys: [2] })).toBe('/report/b')
  })

  it('canOpenModule báo cáo false khi reportKeys=[] dù entity đọc được', () => {
    const m = module(reportNav([1]), 'report')
    expect(canOpenModule(m, allow('report'), { reportKeys: [] })).toBe(false)
    expect(canOpenModule(m, allow('report'), { reportKeys: [1] })).toBe(true)
  })

  it('trên phân hệ Báo cáo THẬT: mục Tổng quan vẫn ẩn nếu không được gán báo cáo nào', () => {
    const report = moduleRegistry.find((mm) => mm.id === 'report')
    expect(report).toBeDefined()
    if (!report) return

    //  Đọc được MỌI entity nguồn nhưng không được gán khóa nào — mô phỏng đúng
    //  hồ sơ cũ lưu trong localStorage trước khi `report_keys` ra đời.
    const allowEverything = () => true
    expect(canOpenModule(report, allowEverything, {})).toBe(false)
    expect(canOpenModule(report, allowEverything, { reportKeys: [1] })).toBe(true)
  })
})

describe('Lịch làm việc (hrModule) — nav gác mặc định MỞ nên phải có ca riêng', () => {
  //  Không dùng `!`: module vắng thì ném lỗi rõ ràng thay vì nổ ở dòng khẳng định.
  const hr = (() => {
    const found = allModules.find((m) => m.id === 'hr')
    if (!found) throw new Error('Module hr chưa đăng ký trong module-registry')
    return found
  })()

  function makeCan(perms: Record<string, string[]>) {
    return (entity: PermissionEntity, action: PermissionAction = 'read') =>
      perms[entity]?.includes(action) ?? false
  }

  const PATHS = [
    '/hr/work-schedules',
    '/hr/work-schedules/new',
    '/hr/work-schedules/5',
    '/hr/work-schedule-assignments',
  ]

  //  `/hr/work-roster` gác `employee.read` — KHÔNG phải quyền quản lý lịch. Nav gác mặc định MỞ,
  //  nên route này mà thiếu mục menu gác thì ai đăng nhập cũng vào.
  it.each(['/hr/work-roster'])('%s: chỉ cần employee.read', (path) => {
    expect(canAccessRoute(hr, path, makeCan({ employee: ['read'] }))).toBe(true)
    expect(canAccessRoute(hr, path, makeCan({ work_schedule: ['write', 'create', 'delete'] }))).toBe(false)
    expect(canAccessRoute(hr, path, makeCan({ work_schedule: ['read'] }))).toBe(false)
    expect(canAccessRoute(hr, path, makeCan({}))).toBe(false)
  })

  it('có employee.read nhưng thiếu quyền quản lý lịch: vẫn KHÔNG vào được hai màn quản lý', () => {
    for (const path of PATHS) {
      expect(canAccessRoute(hr, path, makeCan({ employee: ['read', 'write'] }))).toBe(false)
    }
  })

  it.each(PATHS)('%s: có quyền sửa/tạo/xóa work_schedule thì vào được', (path) => {
    for (const action of ['write', 'create', 'delete']) {
      expect(canAccessRoute(hr, path, makeCan({ work_schedule: [action] }))).toBe(true)
    }
  })

  it.each(PATHS)('%s: chỉ read, không quyền nào, hoặc quyền khóa khác thì KHÔNG vào được', (path) => {
    expect(canAccessRoute(hr, path, makeCan({ work_schedule: ['read'] }))).toBe(false)
    expect(canAccessRoute(hr, path, makeCan({}))).toBe(false)
    expect(canAccessRoute(hr, path, makeCan({ holiday: ['write'] }))).toBe(false)
    expect(canAccessRoute(hr, path, makeCan({ leave_type: ['write', 'create', 'delete'] }))).toBe(false)
  })

  it('người chỉ có employee.read thấy nhóm «Lịch làm việc» nhưng CHỈ với con «Xem lịch»', () => {
    const viewer = visibleNavItems(hr, makeCan({ employee: ['read'], work_schedule: ['read'] }))
    const item = viewer.find((i) => i.label === 'Lịch làm việc')
    expect(item?.children?.map((c) => c.label)).toEqual(['Xem lịch'])
  })

  it('không có employee.read thì không thấy nhóm «Lịch làm việc» (dù đọc được work_schedule)', () => {
    const nav = visibleNavItems(hr, makeCan({ work_schedule: ['read'] }))
    expect(nav.some((i) => i.label === 'Lịch làm việc')).toBe(false)
  })

  it('người sửa được work_schedule thấy hai mục quản lý; có thêm employee.read thì thấy cả ba, Xem lịch đứng đầu', () => {
    const editor = visibleNavItems(hr, makeCan({ work_schedule: ['write'] }))
    expect(editor.find((i) => i.label === 'Lịch làm việc')?.children?.map((c) => c.label)).toEqual([
      'Mẫu lịch tuần',
      'Gán lịch',
    ])

    const both = visibleNavItems(hr, makeCan({ employee: ['read'], work_schedule: ['write'] }))
    expect(both.find((i) => i.label === 'Lịch làm việc')?.children?.map((c) => c.label)).toEqual([
      'Xem lịch',
      'Mẫu lịch tuần',
      'Gán lịch',
    ])
  })
})
