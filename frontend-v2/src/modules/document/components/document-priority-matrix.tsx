import { cn } from '@/shared/utils/cn'
import type { PriorityMatrix } from '../types/document-dashboard'

/**
 * MA TRẬN ƯU TIÊN — bốn ô *quan trọng × khẩn cấp*.
 *
 * Bốn con số này trả lời một câu mà biểu đồ tròn "cơ cấu theo loại" không trả
 * lời được: *"trong đống văn bản đang áp dụng, cái nào phải để mắt tới"*. Ô đỏ
 * (quan trọng + khẩn) là thứ cần nhìn trước khi nhìn bất cứ thứ gì khác, nên nó
 * được đặt ở góc trên–trái, chỗ mắt người đọc chạm vào đầu tiên.
 *
 * Màu đi theo mức độ chứ không theo trang trí: đỏ → vàng → xám. Hai ô "một
 * trong hai" cùng vàng vì chúng thật sự ngang nhau về mức phải chú ý.
 *
 * ⚠️ **"Quan trọng" là thuộc tính của LOẠI văn bản** (loại có cờ cần duyệt hoặc
 * cần Quyết định ban hành), không phải của từng văn bản — hệ thống chưa có cột
 * nào như vậy. Nên hai văn bản cùng loại luôn nằm cùng một nửa. Chú thích dưới
 * bảng nói thẳng điều đó, vì người đọc con số có quyền biết nó được tính ra sao.
 */
interface DocumentPriorityMatrixProps {
  data?: PriorityMatrix
}

/** Bốn ô, khai theo đúng thứ tự đọc từ trái sang phải, trên xuống dưới. */
const O = [
  { key: 'important_urgent', tone: 'danger' },
  { key: 'important_normal', tone: 'warning' },
  { key: 'normal_urgent', tone: 'warning' },
  { key: 'normal_normal', tone: 'muted' },
] as const

const TONE_CLASS = {
  danger: 'border-red-200 bg-red-50 text-red-600',
  warning: 'border-amber-200 bg-amber-50 text-amber-600',
  muted: 'border-slate-200 bg-slate-50 text-slate-500',
} as const

export function DocumentPriorityMatrix({ data }: DocumentPriorityMatrixProps) {
  const so = (key: (typeof O)[number]['key']) => data?.[key] ?? 0

  return (
    <div className="space-y-3">
      {/*  Lưới 3 cột: cột đầu là nhãn hàng, hai cột sau là hai ô số. Dùng lưới
           chứ không dùng `<table>` vì đây là bốn thẻ số, không phải dữ liệu
           bảng — bảng thì trình đọc màn hình sẽ đọc thành "hàng 1, cột 2…". */}
      <div className="grid grid-cols-[auto_1fr_1fr] gap-2">
        <div />
        <ColumnHeader>Khẩn cấp</ColumnHeader>
        <ColumnHeader>Không khẩn cấp</ColumnHeader>

        <RowHeader>Quan trọng</RowHeader>
        <Cell tone={O[0].tone} value={so(O[0].key)} />
        <Cell tone={O[1].tone} value={so(O[1].key)} />

        <RowHeader>Không quan trọng</RowHeader>
        <Cell tone={O[2].tone} value={so(O[2].key)} />
        <Cell tone={O[3].tone} value={so(O[3].key)} />
      </div>

      <p className="text-xs text-muted-foreground">
        <b>Khẩn cấp</b> = độ khẩn của văn bản từ mức «Khẩn» trở lên. <b>Quan trọng</b> = văn
        bản thuộc loại bắt buộc qua duyệt hoặc bắt buộc kèm Quyết định ban hành.
      </p>
    </div>
  )
}

function ColumnHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="pb-1 text-center text-sm font-medium text-muted-foreground">{children}</div>
  )
}

function RowHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center pr-3 text-right text-sm font-medium text-muted-foreground">
      {children}
    </div>
  )
}

function Cell({ tone, value }: { tone: keyof typeof TONE_CLASS; value: number }) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border py-6',
        TONE_CLASS[tone],
      )}
    >
      <span className="text-3xl font-semibold tabular-nums">{value}</span>
      <span className="mt-0.5 text-xs font-medium">văn bản</span>
    </div>
  )
}
