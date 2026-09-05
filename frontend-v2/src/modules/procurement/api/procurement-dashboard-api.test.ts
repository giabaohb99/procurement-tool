import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

/**
 * ─── D4: mọi khóa KPI của Trang chủ đều phải đọc kèm `?? 0` ───
 *
 * `GET /api/dashboard/overview` chỉ đòi ĐĂNG NHẬP, rồi gác TỪNG KHỐI bên trong
 * bằng `can(entity)` và **bỏ hẳn khóa** khi thiếu quyền (xem
 * `backend/app/modules/dashboard/controller.py`, biến `kpi` khởi tạo rỗng rồi
 * mỗi nhánh `if can(...)` mới gán vào). Nghĩa là:
 *
 *  - đọc nhầm khóa của phân hệ khác thì **không ai ăn 403** — chỉ thấy số 0
 *    vĩnh viễn, không có gì đỏ lên ở đâu cả;
 *  - đọc thiếu `?? 0` thì ô KPI hiện `undefined` cho đúng nhóm người bị hạn
 *    chế quyền, còn người khai quyền rộng thì không bao giờ tái hiện được.
 *
 * Hai khóa dễ lẫn nhất, ghi lại để khỏi phải tra: `top_suppliers` = **CHI TIÊU**
 * theo NCC (khối `purchase_order`), `top_debt_suppliers` = **NỢ CÒN LẠI** (khối
 * `payable`).
 *
 * Bài kiểm quét MÃ NGUỒN vì đây là ràng buộc trên cách VIẾT, không phải trên một
 * giá trị chạy được: nó phải đỏ ngay lúc ai đó thêm `kpi?.mot_khoa_moi` trần.
 */
const PAGES = [
  '../pages/procurement-dashboard-page.tsx',
  '../../finance/pages/finance-dashboard-page.tsx',
]

/** Mã nguồn ĐÃ BỎ chú thích — chú thích ở đây có nhắc tên khóa để giải thích. */
function readPage(rel: string): string {
  const src = readFileSync(fileURLToPath(new URL(rel, import.meta.url)), 'utf-8')
  return src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '')
}

describe('D4 — khóa KPI của Trang chủ là TÙY CHỌN', () => {
  it('mọi lần đọc `kpi?.x` đều có `?? 0` (hoặc dùng làm điều kiện bật/tắt)', () => {
    const sai: string[] = []
    for (const page of PAGES) {
      const src = readPage(page)
      //  Bắt `kpi?.khoa` không đi kèm `??` ngay sau. Cho phép dạng dùng làm cờ
      //  (`kpi?.x ? 'warning' : …`, `kpi?.x && …`) vì `undefined` ở đó là falsy
      //  đúng ý, không rò ra màn hình.
      for (const m of src.matchAll(/kpi\?\.([a-z_0-9]+)\s*([^\s]{0,2})/g)) {
        const duoi = m[2]
        const okie = duoi.startsWith('??') || duoi.startsWith('?') || duoi.startsWith('&&')
        if (!okie) sai.push(`${page}: kpi?.${m[1]} ${duoi}`)
      }
    }
    expect(sai).toEqual([])
  })

  it('không trang nào đọc `kpi.` trần (thiếu `?.`) — `kpi` vắng mặt là sập trang', () => {
    const sai: string[] = []
    for (const page of PAGES) {
      const src = readPage(page)
      for (const m of src.matchAll(/(?<![?.\w])kpi\.[a-z_]/g)) sai.push(`${page}: ${m[0]}`)
    }
    expect(sai).toEqual([])
  })

  it('hợp đồng kiểu: mọi khóa trong `DashboardOverview.kpi` khai `?`', () => {
    //  Chốt ở tầng kiểu để `tsc` bắt hộ lần sau: thêm một khóa KPI không có `?`
    //  là hứa với cả app rằng backend luôn gửi nó — mà backend thì không.
    const src = readPage('./procurement-dashboard-api.ts')
    const mo = src.indexOf('kpi: {') + 'kpi: {'.length
    const block = src.slice(mo, src.indexOf('}', mo))
    const khoa = [...block.matchAll(/^\s*([a-z_0-9]+)(\??):/gm)]
    expect(khoa.length).toBeGreaterThan(5)
    expect(khoa.filter((m) => m[2] !== '?').map((m) => m[1])).toEqual([])
  })
})
