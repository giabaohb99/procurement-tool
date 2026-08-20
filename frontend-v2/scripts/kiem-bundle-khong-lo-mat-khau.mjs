/**
 * CHẶN MẬT KHẨU DEMO LỌT VÀO BẢN BUILD THẬT.
 *
 * `DemoAccountSwitcher` (đổi tài khoản nhanh khi trình diễn) đọc một danh sách
 * CÓ MẬT KHẨU. Chỗ chặn duy nhất là `import.meta.env.DEV` — Vite thay nó bằng
 * `false` lúc build nên Rollup cắt sạch nhánh chết lẫn mô-đun `demo-accounts`.
 *
 * Đó là suy luận, không phải bằng chứng. Script này mở thẳng bản build ra đếm.
 * Chạy sau mỗi lần đụng vào bộ chuyển tài khoản:
 *
 *   docker compose exec -T erp npm run build && \
 *   docker compose exec -T erp npm run kiem:bundle
 */
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const THU_MUC = join('dist', 'assets')

//  Mật khẩu và định danh chỉ có trong mã dành cho bản DEV. Thấy bất kỳ chuỗi nào
//  trong bản build nghĩa là nhánh chết KHÔNG bị cắt — dừng build lại ngay.
const CAM = [
  'demo123',
  'helpadmin',
  'TESTCONAGRI',
  'TESTMEDEGO',
  'DEMO_MANAGER',
  'DEMO_PURCHASER',
  'DEMO_ACCOUNTS',
  'Đổi tài khoản nhanh',
  //  12 văn thư pháp nhân con — mật khẩu CHÍNH LÀ mã này, nên liệt kê đủ cả 12
  //  chứ không lấy mẫu vài cái. Đã có lần rút gọn danh sách bằng `.map()` trong
  //  `demo-accounts.ts` và cả 12 lọt vào bản build; chỉ có đếm đủ mới bắt được.
  'VTAGRIPLANT',
  'VTSAM',
  'VTICARE',
  'VTIDA',
  'VTABA',
  'VTNNABA',
  'VTNNDEGO',
  'VTN2SBIO',
  'VTBAMBOO',
  'VTDRXANH',
  'VTHKDDRXANH',
  'VTDEGOHOLDING',
]

let js
try {
  js = readdirSync(THU_MUC).filter((f) => f.endsWith('.js'))
} catch {
  console.error(`Chưa có bản build ở ${THU_MUC}. Chạy \`npm run build\` trước.`)
  process.exit(2)
}

const noiDung = js.map((f) => readFileSync(join(THU_MUC, f), 'utf8')).join('')
console.log(`Đã đọc ${js.length} tệp js · ${noiDung.length.toLocaleString('vi-VN')} ký tự`)

const loLot = []
for (const chuoi of CAM) {
  const dem = noiDung.split(chuoi).length - 1
  console.log(`  ${chuoi.padEnd(22)} ${dem === 0 ? 'không có' : `LỌT ${dem} lần`}`)
  if (dem > 0) loLot.push(chuoi)
}

if (loLot.length) {
  console.error(`\nHỎNG: ${loLot.length} chuỗi của bản DEV lọt vào bản build thật.`)
  process.exit(1)
}
console.log('\nSẠCH — không chuỗi nào của bản DEV lọt vào bản build thật.')
