import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown } from 'lucide-react'

import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { firstLeaves, type HelpNode } from '@/lib/help-tree'
import { cn } from '@/lib/utils'

// Thanh điều hướng chính ở header khu người dùng.
// Nhãn nav là NHÓM ngắn gọn khai báo bên dưới (không phải tiêu đề bài viết — tiêu đề mục gốc
// dài quá, đưa ngang lên header sẽ bị cắt cụt); nội dung nằm trong menu xổ xuống.
// Menu mở khi RÊ CHUỘT (bấm vẫn mở được), đóng trễ ~150ms để chuột kịp đi từ nhãn xuống menu.
// Nav KHÔNG đánh dấu nhóm đang đọc — breadcrumb và sidebar trái đã làm việc đó.

/** Số lối tắt trong menu "Bắt đầu" — giữ bằng số tile của khối "Bắt đầu ngay" ở trang chủ. */
const QUICK_COUNT = 3

/** Trễ đóng menu khi chuột rời nhãn/menu (ms) — đủ để chuột băng qua khoảng hở giữa hai vùng. */
const CLOSE_DELAY = 150

interface NavLink {
  to: string
  title: string
}

interface NavGroup {
  label: string
  /** Tiền tố tiêu đề mục gốc thuộc nhóm này (so khớp không phân biệt hoa/thường). */
  prefixes: string[]
  /** true = menu hiện các lối tắt "Bắt đầu ngay" thay vì liệt kê mục gốc của nhóm. */
  quickStart?: boolean
  /** Link tĩnh chèn thêm vào cuối menu (trang không nằm trong cây tài liệu). */
  extras?: NavLink[]
}

// Gom theo tiền tố tiêu đề chứ không theo id, để local và prod dùng chung được cấu hình này.
// Mục gốc KHÔNG khớp nhóm nào sẽ rơi vào nhóm cuối — thêm mục gốc mới ở /admin vẫn lên nav,
// chỉ là muốn xếp đúng nhóm thì bổ sung tiền tố vào đây.
const NAV_GROUPS: NavGroup[] = [
  { label: 'Bắt đầu', prefixes: ['bắt đầu', '1.'], quickStart: true },
  { label: 'Sử dụng', prefixes: ['2.', '3.', '4.'] },
  {
    label: 'Tài nguyên khác',
    prefixes: ['5.', '6.'],
    extras: [{ to: '/cau-hoi-thuong-gap', title: 'Câu hỏi thường gặp' }],
  },
]

interface NavGroupLinks {
  label: string
  /** Mục hiện trong menu xổ xuống. */
  links: NavLink[]
}

/** Xếp mục gốc vào nhóm theo tiền tố tiêu đề; phần không khớp dồn vào nhóm cuối. */
function buildGroups(tree: HelpNode[]): NavGroupLinks[] {
  const roots = NAV_GROUPS.map(() => [] as HelpNode[])

  tree.forEach((node) => {
    const title = node.title.trim().toLowerCase()
    const idx = NAV_GROUPS.findIndex((g) => g.prefixes.some((p) => title.startsWith(p)))
    roots[idx === -1 ? roots.length - 1 : idx].push(node)
  })

  const toLink = (n: HelpNode): NavLink => ({ to: `/${n.id}`, title: n.title })

  return NAV_GROUPS.map((group, i) => ({
    label: group.label,
    // Nhóm "Bắt đầu" chỉ đường tới đúng 3 bài mà khối "Bắt đầu ngay" ở trang chủ giới thiệu,
    // thay vì lặp lại tên mục gốc — người mới vào đọc được ngay bài đầu tiên.
    links: [
      ...(group.quickStart ? firstLeaves(tree, QUICK_COUNT) : roots[i]).map(toLink),
      ...(group.extras || []),
    ],
  })).filter((g) => g.links.length > 0)
}

export default function HelpMainNav({ tree }: { tree: HelpNode[] }) {
  // Nhãn nhóm đang mở — giữ ở CẤP THANH NAV (không phải trong từng mục) để rê ngang sang nhóm
  // khác là menu cũ đóng ngay, không có cảnh hai menu chồng nhau trong lúc chờ hết CLOSE_DELAY.
  const [openLabel, setOpenLabel] = useState<string | null>(null)
  const closeTimer = useRef<number>(undefined)

  const cancelClose = useCallback(() => {
    if (closeTimer.current !== undefined) {
      clearTimeout(closeTimer.current)
      closeTimer.current = undefined
    }
  }, [])

  const openNow = useCallback((label: string | null) => {
    cancelClose()
    setOpenLabel(label)
  }, [cancelClose])

  const closeSoon = useCallback(() => {
    cancelClose()
    closeTimer.current = window.setTimeout(() => setOpenLabel(null), CLOSE_DELAY)
  }, [cancelClose])

  useEffect(() => cancelClose, [cancelClose])

  if (tree.length === 0) return null

  return (
    // Từ xl mới hiện: dưới 1280px header còn logo + ô tìm kiếm + cụm tài khoản là vừa chỗ,
    // nhồi thêm nav sẽ làm nhãn xuống dòng và header phình cao.
    <nav className="hidden items-center gap-1 self-stretch xl:flex">
      {buildGroups(tree).map((group) => (
        <NavItem
          key={group.label}
          label={group.label}
          links={group.links}
          open={openLabel === group.label}
          onOpenChange={(next) => openNow(next ? group.label : null)}
          onHoverIn={() => openNow(group.label)}
          onHoverOut={closeSoon}
          onMenuHoverIn={cancelClose}
        />
      ))}
    </nav>
  )
}

function NavItem({
  label,
  links,
  open,
  onOpenChange,
  onHoverIn,
  onHoverOut,
  onMenuHoverIn,
}: {
  label: string
  links: NavLink[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onHoverIn: () => void
  onHoverOut: () => void
  onMenuHoverIn: () => void
}) {
  return (
    // modal={false} là BẮT BUỘC với menu mở bằng hover: ở chế độ modal, Radix đặt
    // `pointer-events: none` lên <body>, nút nav lập tức mất hover -> mouseleave -> menu đóng ->
    // body trả lại pointer-events -> chuột vẫn nằm trên nút -> mouseenter -> mở lại... giật vô hạn.
    <DropdownMenu modal={false} open={open} onOpenChange={onOpenChange}>
      {/* Nav KHÔNG đánh dấu mục đang đọc (không tô primary / gạch chân): breadcrumb + sidebar trái
          đã chỉ rõ đang ở đâu, nav chỉ để nhảy nhanh sang nhóm khác. */}
      <DropdownMenuTrigger
        onMouseEnter={onHoverIn}
        onMouseLeave={onHoverOut}
        className={cn(
          'flex h-full cursor-pointer items-center gap-1 whitespace-nowrap px-3 text-[15px] font-semibold text-ink outline-none transition-colors hover:text-primary',
          '[&[data-state=open]>svg]:rotate-180',
        )}
      >
        {label}
        <ChevronDown className="size-4 shrink-0 transition-transform" />
      </DropdownMenuTrigger>

      {/* Menu rộng rãi hơn mặc định shadcn: tiêu đề bài viết dài được xuống dòng, không cắt cụt */}
      <DropdownMenuContent
        align="start"
        sideOffset={4}
        onMouseEnter={onMenuHoverIn}
        onMouseLeave={onHoverOut}
        className="w-72 rounded-xl p-2 shadow-[0_12px_32px_rgba(15,23,42,0.12)]"
      >
        {links.map((link) => (
          <DropdownMenuItem key={link.to} asChild>
            <Link
              to={link.to}
              className="cursor-pointer rounded-lg px-4 py-2.5 text-[15px] leading-snug whitespace-normal text-ink focus:text-primary"
            >
              {link.title}
            </Link>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
