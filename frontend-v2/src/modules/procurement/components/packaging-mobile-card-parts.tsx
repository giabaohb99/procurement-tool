/**
 * duoc-CR-784 — khung dùng chung của THẺ điện thoại cụm Giá bao bì (`DataTableProps.mobileCard`, màn < 768px).
 *
 * Mọi thẻ của cụm cùng ba tầng: (1) tiêu đề = mã + tên đậm, bên phải là huy hiệu / số chính; (2) dải SỐ CHÍNH nền nhạt
 * (chi phí cũ → mới, tăng / giảm…) chữ to hơn; (3) lưới "nhãn: giá trị" hai cột cho trường phụ. Nhãn lấy đúng chữ tiêu đề
 * cột của bảng để hai chế độ nói cùng một câu.
 *
 * ⚠️ Thẻ của màn CRUD (Báo giá, Định mức) nằm TRONG `<button>` của `DataTableMobileCards` (bấm thẻ = mở hộp sửa) nên
 * không được chứa link / nút; các màn còn lại không bấm cả thẻ nên mã bấm được sang Lịch sử như ở bảng.
 */
import { ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface PackagingCardTitleProps {
  /** Mã (thường là `PackagingCodeLink`, hoặc chữ trơn ở thẻ nằm trong nút). */
  code: ReactNode
  name?: string
  /** Huy hiệu / con số đứng bên phải tiêu đề. */
  aside?: ReactNode
  /** Mũi tên "thẻ bấm được" — chỉ thẻ màn CRUD (bấm cả thẻ mở hộp sửa). */
  chevron?: boolean
}

export function PackagingCardTitle({ code, name, aside, chevron = false }: PackagingCardTitleProps) {
  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1">
        <div className="font-semibold tabular-nums">{code}</div>
        {/*  Tên vật tư / sản phẩm dài (tên pháp lý đầy đủ): tối đa hai dòng rồi "…", đủ chữ ở `title`. */}
        <div className="line-clamp-2 text-sm font-semibold text-foreground" title={name}>
          {name || <span className="font-normal text-muted-foreground">(chưa có tên)</span>}
        </div>
      </div>
      {aside && <div className="flex shrink-0 flex-col items-end gap-1">{aside}</div>}
      {chevron && (
        <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
      )}
    </div>
  )
}

export interface PackagingCardItem {
  label: string
  value: ReactNode
  /** Chiếm trọn hai cột (tên nhà cung cấp, kho, ghi chú). */
  wide?: boolean
}

/** Dải SỐ CHÍNH: nền nhạt, chữ to — thứ người ta mở thẻ ra để đọc. */
export function PackagingCardStats({
  items,
  columns = 2,
}: {
  items: PackagingCardItem[]
  columns?: 2 | 3
}) {
  return (
    <dl
      className={cn(
        'grid gap-x-3 gap-y-2 rounded-md bg-muted/60 px-2.5 py-2',
        columns === 3 ? 'grid-cols-3' : 'grid-cols-2',
      )}
    >
      {items.map((item) => (
        <div
          key={item.label}
          className={cn('min-w-0', item.wide && (columns === 3 ? 'col-span-3' : 'col-span-2'))}
        >
          <dt className="truncate text-xs text-muted-foreground">{item.label}</dt>
          <dd className="truncate text-base font-semibold">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}

/**
 * Ô SỐ của lưới 2×2 (thẻ Sản phẩm): nhãn nhỏ mờ trên, giá trị đậm dưới, nền nhạt như dải số chính. Vùng giá trị luôn cao
 * tối thiểu 32px (bằng ô nhập) để bốn ô của lưới cao bằng nhau dù ô có chữ hay ô có ô nhập.
 */
export function PackagingCardTile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0 rounded-md bg-muted/60 px-2.5 py-2">
      <div className="truncate text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 flex min-h-8 min-w-0 items-start text-base font-semibold">{children}</div>
    </div>
  )
}

/** Lưới "nhãn: giá trị" hai (hoặc ba) cột cho trường phụ. Giá trị một dòng, dài thì "…". */
export function PackagingCardFields({
  items,
  columns = 2,
}: {
  items: PackagingCardItem[]
  columns?: 2 | 3
}) {
  return (
    <dl
      className={cn(
        'grid gap-x-3 gap-y-1.5 text-sm',
        columns === 3 ? 'grid-cols-3' : 'grid-cols-2',
      )}
    >
      {items.map((item) => (
        <div
          key={item.label}
          className={cn('min-w-0', item.wide && (columns === 3 ? 'col-span-3' : 'col-span-2'))}
        >
          <dt className="text-xs text-muted-foreground">{item.label}</dt>
          <dd className="truncate">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}

/**
 * Một dòng thành phần gọn trên MỘT hàng: nhãn trái, mã, rồi phần chi tiết sát mép phải — dùng cho năm thành phần chai ·
 * nắp · nhãn · nhãn thùng · thùng. Chi tiết là GIÁ ("cũ → mới") thì giữ trọn số, nhãn dài ("Nhãn thùng (giá /thùng)") cắt
 * "…" trước; chi tiết là TÊN vật tư thì tên cắt "…" (đủ chữ ở `title`).
 */
export function PackagingCardPartLine({
  label,
  code,
  detail,
  detailTitle,
  highlight = false,
}: {
  label: string
  code: ReactNode
  /** Số (giá) — luôn hiện trọn. */
  detail?: ReactNode
  /** Có `detailTitle` = chi tiết là chữ dài (tên vật tư): cắt "…" thay vì nhãn. */
  detailTitle?: string
  /** Mã đang được chọn ở màn Tác động — tô nền như ô của bảng. */
  highlight?: boolean
}) {
  const textDetail = detailTitle !== undefined
  return (
    <li
      className={cn(
        'flex items-baseline gap-x-2 text-xs',
        highlight && '-mx-1 rounded bg-amber-100 px-1 py-0.5 dark:bg-amber-900',
      )}
    >
      <span
        className={cn('text-muted-foreground', textDetail ? 'shrink-0' : 'min-w-0 truncate')}
        title={label}
      >
        {label}
      </span>
      <span className="shrink-0 font-medium tabular-nums">{code}</span>
      {detail && (
        <span
          className={cn(
            'ml-auto text-right',
            textDetail ? 'min-w-0 truncate' : 'shrink-0 whitespace-nowrap',
          )}
          title={detailTitle}
        >
          {detail}
        </span>
      )}
    </li>
  )
}
