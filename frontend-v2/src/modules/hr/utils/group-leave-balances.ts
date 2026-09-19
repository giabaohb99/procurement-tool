import type { LeaveBalance } from '../types/leave'

/**
 * GOM DÒNG QUỸ THEO NGƯỜI cho bảng `/hr/leave-balances`.
 *
 * Vì sao phải gom: backend trả một dòng cho mỗi **(người × năm × loại nghỉ)**.
 * Một công ty khai tám loại nghỉ là mỗi nhân sự tám dòng, mà sáu trong tám dòng
 * đó hạn mức 0 (tang chế, cưới hỏi, nghỉ bù…). Bày phẳng thì bảng dài gấp tám
 * lần số người, và câu hỏi người ta mở màn này để hỏi — *"anh A còn mấy ngày"* —
 * phải tự cộng tám dòng mới trả lời được.
 *
 * ⚠️ **Gom ở đây nghĩa là PHÂN TRANG ĐẾM THEO NGƯỜI, không theo dòng quỹ.** Nên
 * trang gọi phải kéo TRỌN danh sách của năm đang xem về (một lượt, `page_size`
 * sát trần backend) rồi tự cắt trang — cắt trang ở backend thì một người có thể
 * bị xé đôi qua hai trang và tổng của họ sai ở cả hai.
 */

/** Tổng các cột số của một nhóm — đúng bộ cột mà bảng bày ra. */
export interface LeaveBalanceTotals {
  allocated_days: number
  seniority_days: number
  carried_days: number
  adjusted_days: number
  carried_out_days: number
  carried_expired_days: number
  used_days: number
  pending_days: number
  total_days: number
  remaining_days: number
}

export interface LeaveBalanceGroup {
  employeeId: number
  /** Tên hiển thị; rỗng ở mọi dòng thì lùi về `#<id>`. */
  employeeName: string
  /** Giữ nguyên thứ tự backend trả về — nó đã sắp theo loại nghỉ. */
  balances: LeaveBalance[]
  totals: LeaveBalanceTotals
  /**
   * Nhóm này có quỹ THẬT không — quyết định số `0 còn lại` tô đỏ (hết phép) hay
   * để mờ (loại nghỉ vốn không cấp hạn mức). Xem `hasQuota`.
   */
  hasQuota: boolean
}

/**
 * Một hàng trên bảng. Ba dạng, cố ý tách bằng `kind` chứ không suy từ việc có
 * `children` hay không: hàng `single` và hàng `child` bày cùng một dòng quỹ
 * nhưng thụt lề khác nhau và bấm vào cho kết quả khác nhau.
 */
export type LeaveBalanceRow =
  /** Người có TỪ HAI loại nghỉ trở lên — bày số tổng, bấm vào thì bung/thu. */
  | { kind: 'group'; id: string; group: LeaveBalanceGroup }
  /** Người chỉ có MỘT loại nghỉ — không có gì để bung, bày thẳng dòng quỹ đó. */
  | { kind: 'single'; id: string; group: LeaveBalanceGroup; balance: LeaveBalance }
  /**
   * Dòng con của một nhóm đang bung.
   *
   * `isLast` để vẽ khuỷu `└` thay vì `├` — thân cây phải DỪNG ở dòng cuối, nếu
   * không nó chạy tiếp xuống hàng của người kế bên và đọc ra như thể người đó
   * cũng thuộc nhóm này.
   */
  | { kind: 'child'; id: string; balance: LeaveBalance; isLast: boolean }

const SUM_FIELDS = [
  'allocated_days',
  'seniority_days',
  'carried_days',
  'adjusted_days',
  'carried_out_days',
  'carried_expired_days',
  'used_days',
  'pending_days',
  'total_days',
  'remaining_days',
] as const satisfies readonly (keyof LeaveBalanceTotals)[]

/**
 * Làm tròn hai chữ số sau dấu phẩy.
 *
 * ⚠️ Không phải làm đẹp: số ngày đi theo bước nửa ngày, và `0.1 + 0.2` trong
 * JavaScript ra `0.30000000000000004`. Cộng tám dòng như vậy là cột «Còn lại»
 * hiện ra một con số hai chục chữ số giữa một bảng toàn số tròn.
 */
function round2(value: number): number {
  return Math.round(value * 100) / 100
}

/** Số hợp lệ hay không — dòng thiếu cột (backend cũ, dữ liệu lỗi) coi như 0. */
function num(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

/**
 * Dòng quỹ này có quỹ THẬT không.
 *
 * Trùng ý với `hasQuota` ở `leave-balance-quota.ts` nhưng chịu được dòng thiếu
 * cột (xem `num`), vì hàm này chạy trên dữ liệu vừa xuống dây chứ không phải
 * trên một dòng đã qua kiểm.
 */
function rowHasQuota(balance: LeaveBalance): boolean {
  return (
    num(balance.allocated_days) > 0 ||
    num(balance.seniority_days) > 0 ||
    num(balance.carried_days) > 0 ||
    num(balance.adjusted_days) !== 0
  )
}

/**
 * Gom danh sách dòng quỹ thành danh sách nhóm theo nhân sự.
 *
 * Thứ tự nhóm = thứ tự NGƯỜI XUẤT HIỆN LẦN ĐẦU trong danh sách gốc, nên bảng
 * giữ nguyên cách sắp xếp của backend thay vì tự đảo theo tên hay theo id.
 */
export function groupLeaveBalances(items: readonly LeaveBalance[] | undefined): LeaveBalanceGroup[] {
  const byEmployee = new Map<number, LeaveBalanceGroup>()

  for (const balance of items ?? []) {
    const employeeId = num(balance.employee_id)
    let group = byEmployee.get(employeeId)

    if (!group) {
      group = {
        employeeId,
        employeeName: '',
        balances: [],
        totals: {
          allocated_days: 0,
          seniority_days: 0,
          carried_days: 0,
          adjusted_days: 0,
          carried_out_days: 0,
          carried_expired_days: 0,
          used_days: 0,
          pending_days: 0,
          total_days: 0,
          remaining_days: 0,
        },
        hasQuota: false,
      }
      byEmployee.set(employeeId, group)
    }

    group.balances.push(balance)
    //  Tên lấy ở dòng ĐẦU TIÊN có tên: backend gửi kèm tên ở mọi dòng, nhưng
    //  hồ sơ vừa bị xóa thì tên rỗng — một dòng rỗng không được xóa tên đã có.
    if (!group.employeeName && balance.employee_name?.trim()) {
      group.employeeName = balance.employee_name.trim()
    }
    for (const field of SUM_FIELDS) {
      group.totals[field] += num(balance[field])
    }
    if (rowHasQuota(balance)) group.hasQuota = true
  }

  const groups = [...byEmployee.values()]
  for (const group of groups) {
    if (!group.employeeName) group.employeeName = `#${group.employeeId}`
    for (const field of SUM_FIELDS) {
      group.totals[field] = round2(group.totals[field])
    }
  }
  return groups
}

/**
 * Trải danh sách nhóm thành danh sách HÀNG cho `DataTable`.
 *
 * ⚠️ Nhóm chỉ có MỘT dòng quỹ thì không có mũi tên bung: bung ra để thấy đúng
 * một dòng chép lại con số vừa đọc là một thao tác không trả lại gì. Đó cũng là
 * đa số hiện nay — công ty mới khai mỗi «Phép năm» thì mọi nhân sự đều một dòng,
 * và một bảng 261 mũi tên vô dụng còn tệ hơn bảng phẳng cũ.
 */
export function flattenLeaveBalanceGroups(
  groups: readonly LeaveBalanceGroup[],
  expanded: ReadonlySet<number>,
): LeaveBalanceRow[] {
  const rows: LeaveBalanceRow[] = []

  for (const group of groups) {
    if (group.balances.length === 1) {
      const balance = group.balances[0]
      rows.push({ kind: 'single', id: `b${balance.id}`, group, balance })
      continue
    }

    rows.push({ kind: 'group', id: `g${group.employeeId}`, group })
    if (expanded.has(group.employeeId)) {
      group.balances.forEach((balance, i) => {
        rows.push({
          kind: 'child',
          id: `b${balance.id}`,
          balance,
          isLast: i === group.balances.length - 1,
        })
      })
    }
  }

  return rows
}

/** Dòng quỹ mà hàng này đại diện — `null` với hàng nhóm (nhóm không có id quỹ). */
export function rowBalance(row: LeaveBalanceRow): LeaveBalance | null {
  return row.kind === 'group' ? null : row.balance
}

/** Bộ số mà hàng này bày ra: tổng của nhóm, hoặc chính dòng quỹ đó. */
export function rowTotals(row: LeaveBalanceRow): LeaveBalanceTotals | LeaveBalance {
  return row.kind === 'group' ? row.group.totals : row.balance
}

/** Hàng này có quỹ thật không — dùng để quyết «0 còn lại» tô đỏ hay để mờ. */
export function rowHasRealQuota(row: LeaveBalanceRow): boolean {
  return row.kind === 'group' ? row.group.hasQuota : rowHasQuota(row.balance)
}

/**
 * NHÁNH CÂY của hàng con — thân dọc cộng một nhánh ngang đâm vào tên loại nghỉ,
 * và dòng cuối cụm thì thân dừng lại ở giữa thành khuỷu `└`.
 *
 *     ├─ Phép năm
 *     ├─ Nghỉ ốm đau
 *     └─ Nghỉ bù
 *
 * Bản đầu chỉ có thân dọc, không nhánh ngang — khách nói ngay là "chưa ra tree"
 * (19/09/2026). Đúng: một vạch dọc trơn nói *"mấy hàng này cùng một khối"*,
 * nhưng không nói hàng nào **nối vào** đâu; chính nhánh ngang mới làm việc đó.
 * Và thiếu khuỷu `└` thì thân chạy hết chiều cao hàng cuối rồi đâm sang hàng
 * của người kế bên — đọc ra như thể người đó cũng thuộc nhóm.
 *
 * ⚠️ Vẽ bằng ẢNH NỀN của ô (hai lớp), không bằng `border-l` cũng không bằng
 * phần tử con:
 *
 *  · `border-l` chỉ nằm được ở MÉP ô (x = 0), mà thân cây phải thẳng hàng với
 *    mũi tên của hàng cha — tức x = 24px (12px đệm ô + nửa nút 24px);
 *  · phần tử con thì bị `DataTable` bọc trong một `div.truncate`
 *    (`overflow: hidden`), nên nó không tràn ra được phần đệm dọc `py-1.5` của
 *    ô — thân đứt quãng 12px ở mỗi mối nối giữa hai hàng;
 *  · `inset shadow` — cách cả tệp `data-table.tsx` đang dùng để kẻ vạch — chỉ
 *    vẽ được DẢI BÁM MÉP, không đặt được một nét 1px ở giữa ô.
 *
 * Lớp 1 = thân dọc `1px × (100% | 50%)` tại `x = 24px`; lớp 2 = nhánh ngang
 * `12px × 1px` tại `x = 24px, y = 50%`. Hai lớp gặp nhau đúng tâm hàng. Tên loại
 * nghỉ thụt `pl-7` nên nó bắt đầu ở x = 40px, chừa 4px sau đầu nhánh.
 */
const TREE_IMAGE =
  '[&>td:first-child]:bg-[image:linear-gradient(var(--tree-line),var(--tree-line)),linear-gradient(var(--tree-line),var(--tree-line))]'
const TREE_POSITION = '[&>td:first-child]:bg-[position:24px_0,24px_50%]'
const TREE_COMMON = `${TREE_IMAGE} ${TREE_POSITION} [&>td:first-child]:bg-no-repeat`

//  Thân chạy trọn chiều cao hàng — còn dòng con phía dưới để nối tiếp.
const TREE_BRANCH = `${TREE_COMMON} [&>td:first-child]:bg-[length:1px_100%,12px_1px]`
//  Dòng CUỐI cụm: thân dừng ở 50% — đúng chỗ nhánh ngang cắt ngang — thành `└`.
const TREE_END = `${TREE_COMMON} [&>td:first-child]:bg-[length:1px_50%,12px_1px]`

/**
 * Gốc cây trên hàng CHA đang bung: một đoạn thân ở NỬA DƯỚI ô, mọc từ tâm hàng
 * (chỗ mũi tên) xuống mép dưới, để nối liền vào thân của dòng con đầu tiên.
 *
 * Thiếu đoạn này thì cây bắt đầu lơ lửng ở mép trên hàng con đầu, hở đúng nửa
 * hàng ngay dưới mũi tên — chỗ mắt tìm đầu tiên khi hỏi *"cụm này bắt đầu từ
 * đâu"*. Một lớp, không có nhánh ngang: hàng cha là gốc, không phải một nhánh.
 */
const TREE_ROOT = [
  '[&>td:first-child]:bg-[image:linear-gradient(var(--tree-line),var(--tree-line))]',
  '[&>td:first-child]:bg-[length:1px_50%]',
  '[&>td:first-child]:bg-[position:24px_100%]',
  '[&>td:first-child]:bg-no-repeat',
].join(' ')

/**
 * Nền của một hàng — xem `DataTableProps.rowClassName`.
 *
 * Ba mức, và mức giữa là mức phải có: **hàng cha ĐANG BUNG tô nổi bật**. Thiếu
 * nó thì cha và con chỉ khác nhau một sắc xám, mà giữa một khối bốn năm hàng
 * liền nhau người đọc không còn thấy hàng nào mở ra hàng nào — nhất là khi cuộn
 * tới giữa bảng và hàng cha đã trôi khỏi tầm mắt (khách nêu 19/09/2026).
 *
 * ⚠️ **Mỗi mức phải khai BA lớp cùng một màu** — `odd:` · `even:` ·
 * `has-aria-expanded:`. Hàng nền của bảng có HAI luật nền đang tranh nhau, và
 * cả hai đều thắng lớp trần vì chúng là biến thể giả-lớp:
 *
 *  1. kẻ sọc của `DataTable` — `odd:bg-card even:bg-row-stripe`;
 *  2. `has-aria-expanded:bg-muted` nằm sẵn trong `TableRow` của shadcn
 *     (`shared/ui/table.tsx`, xem `docs/ui/table.md` mục 5 bẫy số 6). Nó bắt
 *     theo **sự CÓ MẶT** của thuộc tính `aria-expanded`, không theo giá trị —
 *     mà hàng nhóm nào cũng có nút mũi tên, nên luật này phủ lên MỌI hàng nhóm,
 *     bung hay chưa bung.
 *
 * Hai luật đó cùng độ đặc hiệu `(0,2,0)`, tức thứ tự sinh CSS quyết định ai vẽ —
 * thứ không nên đem ra cược. Khai cả ba lớp về CÙNG một màu thì ai thắng cũng ra
 * đúng màu đó, khỏi cần `!important` và không đụng gì tới hover.
 *
 * Kẻ sọc chẵn/lẻ bị tắt ở cả ba mức: sọc chạy theo thứ tự HÀNG chứ không theo
 * nhóm, nên nó cắt ngang đúng thứ bậc cha-con mà bảng vừa dựng ra.
 */
export function leaveBalanceRowClass(row: LeaveBalanceRow, expanded: boolean): string {
  //  Hàng con không có nút mũi tên nên `has-aria-expanded:` không bao giờ khớp.
  if (row.kind === 'child') {
    return `odd:bg-muted/40 even:bg-muted/40 ${row.isLast ? TREE_END : TREE_BRANCH}`
  }
  if (row.kind === 'group' && expanded) {
    return `odd:bg-row-selected even:bg-row-selected has-aria-expanded:bg-row-selected font-medium ${TREE_ROOT}`
  }
  return 'odd:bg-card even:bg-card has-aria-expanded:bg-card'
}
