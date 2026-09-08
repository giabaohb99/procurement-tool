import { describe, expect, it } from 'vitest'

import { FileText } from 'lucide-react'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { ErpModule } from './module-definition'
import { canAccessRoute, canOpenModule, visibleNavItems } from './module-visibility'
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
    ])
    //  Chỉ xét phân hệ ĐANG BẬT: phân hệ tắt (`sales`, `dego-coffee`,
    //  `approval-seal`) mới có mỗi mục «Tổng quan» chưa khai khóa, nhưng chúng
    //  không vào router nên không ai mở được.
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
