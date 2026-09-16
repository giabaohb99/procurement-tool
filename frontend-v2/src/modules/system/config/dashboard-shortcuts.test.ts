import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { systemModule } from '../routes'
import { SYSTEM_DASHBOARD_SHORTCUTS } from './dashboard-shortcuts'

/** Mục menu trái ĐÁNG có lối tắt: bỏ trang Tổng quan (chính nó) và mục ẩn. */
const navTargets = systemModule.nav.filter(
  (item) => item.path !== appRoutes.system.root && !item.hidden,
)

/**
 * Ràng buộc DỮ LIỆU, không phải test hành vi: hai danh sách nằm hai nơi thì sớm
 * muộn cũng lệch, mà lệch ở đây thì im lặng — trang Tổng quan cứ bày thiếu, chẳng
 * có gì đỏ lên.
 *
 * Đã xảy ra thật (tới 14/09/2026): menu có 8 màn, trang Tổng quan chỉ bày 5 —
 * sót *Hộp thư gửi*, *Phiên đăng nhập*, *Xuất dữ liệu*. Thêm màn thì ai cũng nhớ
 * khai `nav`, không ai nhớ khai lối tắt.
 */
describe('SYSTEM_DASHBOARD_SHORTCUTS', () => {
  it('phủ hết mục menu trái — thêm màn mà quên khai lối tắt là trang Tổng quan bày thiếu', () => {
    const shortcutPaths = new Set(SYSTEM_DASHBOARD_SHORTCUTS.map((s) => s.path))
    const missing = navTargets
      .filter((item) => !shortcutPaths.has(item.path))
      .map((item) => item.label)

    expect(missing).toEqual([])
  })

  it('không có lối tắt nào trỏ ra ngoài menu — thẻ dẫn vào màn đã gỡ là một cú bấm hụt', () => {
    const navPaths = new Set(systemModule.nav.map((item) => item.path))
    const orphan = SYSTEM_DASHBOARD_SHORTCUTS.filter((s) => !navPaths.has(s.path)).map(
      (s) => s.label,
    )

    expect(orphan).toEqual([])
  })

  it('khóa quyền của lối tắt khớp ĐÚNG mục menu tương ứng', () => {
    //  Lệch một cái là thẻ hiện ra rồi bấm vào ăn 403, hoặc ngược lại: màn vào
    //  được mà trang Tổng quan giấu mất. Cả hai đều im lặng.
    const lech: string[] = []
    for (const shortcut of SYSTEM_DASHBOARD_SHORTCUTS) {
      const item = systemModule.nav.find((nav) => nav.path === shortcut.path)
      if (!item) continue // đã bắt ở khẳng định trên
      if (item.entity !== shortcut.entity) {
        lech.push(`${shortcut.label}: entity ${shortcut.entity} ≠ ${item.entity}`)
      }
      //  Màn khai NHIỀU khóa cũng phải khớp từng khóa và ĐÚNG thứ tự: thiếu một
      //  khóa bên này là thẻ biến mất với đúng nhóm người backend đã mở cửa cho.
      if ((item.entities ?? []).join(',') !== (shortcut.entities ?? []).join(',')) {
        lech.push(
          `${shortcut.label}: entities [${shortcut.entities ?? []}] ≠ [${item.entities ?? []}]`,
        )
      }
      if (Boolean(item.manage) !== Boolean(shortcut.manage)) {
        lech.push(`${shortcut.label}: manage ${Boolean(shortcut.manage)} ≠ ${Boolean(item.manage)}`)
      }
    }

    expect(lech).toEqual([])
  })

  it('đủ mười lối tắt — không để thẻ nào bị bỏ quên sau mỗi lần thêm màn', () => {
    //  Không phải con số thiêng: nó chốt rằng bốn màn bổ sung 14/09/2026 còn đó
    //  (ba màn sót + Mẫu email thông báo tách ra ở duoc-CR-397), cộng *Nhật ký
    //  hệ thống* thêm ở bao-CR-407.
    expect(SYSTEM_DASHBOARD_SHORTCUTS).toHaveLength(10)
  })
})
