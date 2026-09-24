import { FolderLock, FolderOpen, Folder as FolderIcon } from 'lucide-react'

import { stripDiacritics } from '@/shared/utils/vn-text'
import { cn } from '@/shared/utils/cn'
import { FOLDER_ACCESS_LEVEL, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Icon TRƯỚC tên node — pháp nhân · thư mục thường (mở/đóng) · thư mục
 * RIÊNG TƯ (đọc `my_level === 0`, tức `FOLDER_ACCESS_LEVEL.private`: người
 * này thấy được node vì có quyền tường minh, nhưng mức nền của nhánh đang
 * khóa với người chỉ có phạm vi theo pháp nhân — khác hẳn "chưa mở/đang mở").
 */
export function FolderNodeIcon({
  data,
  expanded,
  className: sizeClassName,
}: {
  data?: DocFolderTreeNode
  expanded?: boolean
  /** Đè cỡ icon (mặc định `size-4`) — tiêu đề khung nội dung dùng bản to hơn. */
  className?: string
}) {
  if (!data) return null
  const archived = data.status === FOLDER_STATUS.archived
  //  MỌI thư mục dùng CHUNG một icon + một màu (đen), kể cả thư mục pháp nhân (chốt
  //  24/09/2026: tên công ty chỉ là tên thư mục — nơi lưu trữ + phân quyền,
  //  không có gì đặc biệt để vẽ khác). Bản trước vẽ pháp nhân bằng icon tòa
  //  nhà xanh da trời.
  const className = cn(
    'size-4 shrink-0',
    //  Đen trơn (chốt 24/09/2026 — bỏ màu vàng, kiểu icon thư mục Google
    //  Drive). Ngừng dùng thì mờ đi để vẫn phân biệt được.
    archived ? 'text-muted-foreground' : 'text-foreground',
    sizeClassName,
  )
  if (data.my_level === FOLDER_ACCESS_LEVEL.private) return <FolderLock className={className} />
  return expanded ? <FolderOpen className={className} /> : <FolderIcon className={className} />
}

/**
 * Số văn bản cả nhánh — đã lọc theo quyền ĐỌC văn bản của người xem (phase 04).
 *
 * Kiểu VS Code: KHÔNG bày số trên MỌI dòng (rối mắt, nhất là dòng `0` — một
 * thư mục vừa tạo chưa có gì thì không cần ai nhắc), chỉ hiện khi RÊ CHUỘT
 * hoặc dòng ĐANG CHỌN (`group-hover`/`group-aria-selected`, `.group` đã có sẵn
 * trên chính dòng cây ở `tree-row.tsx`).
 */
export function FolderCountBadge({ data }: { data?: DocFolderTreeNode }) {
  if (!data || data.document_count_branch <= 0) return null
  return (
    <span
      className={cn(
        'ml-1 shrink-0 text-xs text-muted-foreground tabular-nums opacity-0 transition-opacity',
        'group-focus-within:opacity-100 group-hover:opacity-100 group-aria-selected:opacity-100',
      )}
      title="Số văn bản cả nhánh bạn đọc được"
    >
      {data.document_count_branch}
    </span>
  )
}

/** Vị trí đoạn KHỚP từ khóa tìm — bỏ dấu để so, nhưng CẮT trên chuỗi GỐC còn nguyên dấu. */
function findMatchRange(label: string, keyword: string): [number, number] | null {
  const kw = stripDiacritics(keyword)
  if (!kw) return null
  const idx = stripDiacritics(label).indexOf(kw)
  if (idx === -1) return null
  return [idx, idx + kw.length]
}

/** Nhãn thường (không đang sửa) — tô sáng đoạn khớp ô tìm thư mục nếu có. */
export function FolderNodeLabel({ label, keyword }: { label: string; keyword?: string }) {
  const range = keyword ? findMatchRange(label, keyword) : null
  if (!range) return <span className="min-w-0 flex-1 truncate">{label}</span>
  const [start, end] = range
  return (
    <span className="min-w-0 flex-1 truncate">
      {label.slice(0, start)}
      <mark className="rounded-sm bg-amber-200 text-inherit">{label.slice(start, end)}</mark>
      {label.slice(end)}
    </span>
  )
}

interface FolderRenameInputProps {
  value: string
  onChange: (value: string) => void
  onCommit: () => void
  onCancel: () => void
  label: string
  placeholder?: string
}

/**
 * Ô nhập thay thế nhãn một dòng cây — dùng CHUNG cho hai việc: "Đổi tên tại
 * chỗ" (nhãn = tên hiện tại của thư mục) VÀ dòng tạm "thư mục mới" kiểu VS
 * Code (`insertTempChildNode`, nhãn = "thư mục mới", `value` bắt đầu rỗng).
 * Enter lưu (hoặc tạo), Esc hủy, rời ô = lưu — cả hai nơi gọi đều tự quyết
 * định "lưu tên rỗng" nghĩa là gì (đổi tên bỏ qua, tạo mới thì hủy hẳn dòng).
 */
export function FolderRenameInput({
  value,
  onChange,
  onCommit,
  onCancel,
  label,
  placeholder,
}: FolderRenameInputProps) {
  return (
    <input
      autoFocus
      value={value}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => {
        //  Chặn nổi bọt lên `TreeView`: nếu không, gõ mũi tên trong lúc sửa
        //  tên lại bị nó đọc thành "chuyển tiêu điểm sang dòng khác".
        event.stopPropagation()
        if (event.key === 'Enter') onCommit()
        if (event.key === 'Escape') onCancel()
      }}
      onBlur={onCommit}
      aria-label={label}
      className="min-w-0 flex-1 rounded border border-primary bg-background px-1 py-0.5 text-[13px] outline-none"
    />
  )
}
