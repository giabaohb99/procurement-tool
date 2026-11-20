/**
 * duoc-CR-784 — TIÊU ĐỀ GỘP NHÓM CỘT (hàng tiêu đề thứ hai phía trên hàng tên cột).
 *
 * Cột khai `group: 'Lần 1'` thì mọi cột LIỀN NHAU cùng nhãn gộp thành một ô tiêu đề nhóm (`colSpan`). Bảng không có
 * cột nào khai `group` thì `layoutColumnGroups` trả `null` và `DataTable` vẽ y như cũ.
 *
 * Nhóm luôn tính theo thứ tự cột ĐANG HIỆN (sau khi ẩn / đổi chỗ / ghim): cột ẩn thì nhóm co lại, nhóm hết cột thì biến
 * mất. Kéo cột chỉ được trong cùng nhóm (`canMoveWithinGroup`) để nhóm không vỡ vụn; ghim một cột giữa nhóm vẫn được —
 * cột ghim dồn ra đầu bảng nên nhóm đó tách làm hai ô; nhãn chỉ ghi ở ô không ghim, ô ghim để trống.
 */
export interface GroupableColumn {
  key: string
  group?: string
  groupTone?: number
}

export interface HeaderGroupSegment {
  /** Khóa ổn định cho React: khóa cột đầu tiên của ô. */
  id: string
  /** Nhãn nhóm; rỗng với đoạn cột không khai nhóm. */
  label: string
  span: number
  /** Cột đầu của ô — mốc `left` khi ô nằm trên cột ghim. */
  firstKey: string
  /** Ô nằm trên cột GHIM (dính khi cuộn ngang). */
  pinned: boolean
  /** Màu tiêu đề nhóm (`groupTone` của cột đầu ô); không khai thì nền tiêu đề thường. */
  tone?: number
  /** Có kẻ vạch đậm bên phải (cuối nhóm, trừ nhóm cuối cùng của bảng). */
  dividerAfter: boolean
}

export interface ColumnGroupLayout {
  segments: HeaderGroupSegment[]
  /** Khóa cột cuối mỗi nhóm (trừ cột cuối bảng) — kẻ vạch ngăn nhóm. */
  groupEndKeys: ReadonlySet<string>
}

export function layoutColumnGroups(
  columns: readonly GroupableColumn[],
  pinnedKeys: readonly string[],
): ColumnGroupLayout | null {
  if (!columns.some((column) => column.group)) return null

  const pinned = new Set(pinnedKeys)
  const segments: HeaderGroupSegment[] = []
  const groupEndKeys = new Set<string>()

  let runLabel: string | null = null
  columns.forEach((column, index) => {
    const label = column.group ?? ''
    const isPinned = pinned.has(column.key)
    const next = columns[index + 1]
    const newRun = label !== runLabel
    if (newRun) runLabel = label

    const last = segments.at(-1)
    if (!newRun && last && last.pinned === isPinned) {
      last.span += 1
    } else {
      segments.push({
        id: column.key,
        label,
        span: 1,
        firstKey: column.key,
        pinned: isPinned,
        tone: column.groupTone,
        dividerAfter: false,
      })
    }

    const endsRun = !next || (next.group ?? '') !== label
    if (endsRun && next) {
      groupEndKeys.add(column.key)
      segments[segments.length - 1].dividerAfter = true
    }
  })

  //  Nhóm bị tách CHỈ vì ghim: nhãn ghi MỘT lần, ở đoạn không ghim (đoạn rộng hơn, cuộn cùng nội dung); đoạn ghim
  //  để ô trống, không vạch giữa hai đoạn. Cả nhóm bị ghim hết thì không còn đoạn không ghim — nhãn ở lại đoạn ghim.
  segments.forEach((segment, index) => {
    const following = segments[index + 1]
    if (segment.pinned && following && !following.pinned && following.label === segment.label) segment.label = ''
  })

  return { segments, groupEndKeys }
}

/** Kéo cột chỉ được trong cùng nhóm (cột không khai nhóm coi như một nhóm "trống" chung). */
export function canMoveWithinGroup(
  columns: readonly GroupableColumn[],
  fromKey: string,
  toKey: string,
): boolean {
  const group = (key: string) => columns.find((column) => column.key === key)?.group ?? ''
  return group(fromKey) === group(toKey)
}
