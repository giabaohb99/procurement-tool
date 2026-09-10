import { PanelLeftOpen } from 'lucide-react'
import { useState } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/shared/ui/hover-card'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet'
import { useWorkSidebarStore } from '../store/sidebar-store'
import { WorkCreateDialog } from './work-create-dialog'
import { WorkSidebarTree } from './work-sidebar-tree'

/**
 * Nút mở lại cây dự án, đứng NGANG HÀNG với tiêu đề trang — chỉ hiện khi cây
 * đang ẩn.
 *
 * Đây là bản thứ ba của cùng một chỗ, hai bản trước khách bỏ:
 * 1. một cột nút dựng đứng bên trái — *"ẩn đi luôn"*;
 * 2. dải rìa vô hình 6px, rê vào thì cây trượt ra sát mép trái — *"hover nó ra
 *    cái popup over chứ ko ra cái sidebar nha"*.
 * Bản này: một cái nút NHÌN THẤY ĐƯỢC cạnh tiêu đề, rê vào thì cây bung ra dưới
 * dạng **thẻ nổi** neo vào chính cái nút. Khác nhau ở chỗ thẻ nổi có mỏ neo và
 * biên rõ ràng — mắt đọc ra ngay "đây là popup của cái nút này"; còn bản trượt
 * ra sát mép trái thì nhìn hệt như sidebar vừa bật lại, tức trông như thao tác
 * ẩn vừa rồi bị hỏng.
 *
 * Rê chuột = XEM, bấm = GHIM lại. Hai việc trên một nút vì chúng là hai mức của
 * cùng một ý muốn ("cho tôi xem cây"), mà chỗ cạnh tiêu đề không đủ cho hai nút.
 *
 * ⚠️ **Ở khổ hẹp nút này đổi hẳn cách chạy** — xem `MobilePeek` bên dưới.
 *
 * ⚠️ Hộp thoại tạo do CHÍNH component này giữ, không nhận từ trang cha: trạng
 * thái ấy nằm ở `WorkLayoutPage` (route CHA), mà nút này sống ở tiêu đề của
 * trang CON — luồn ngược lên thì mọi trang con phải khai một context chỉ để
 * chuyển tiếp hai hàm. Hộp thoại phải đặt NGOÀI `HoverCardContent`: nội dung
 * thẻ nổi bị gỡ khỏi cây khi thẻ đóng, mà mở hộp thoại thì thẻ đóng ngay (tiêu
 * điểm rời đi) — để bên trong là hộp thoại vừa bật đã biến mất.
 */
export function WorkSidebarPeekButton() {
  const isMobile = useIsMobile()
  const collapsed = useWorkSidebarStore((s) => s.collapsed)

  if (isMobile) return <MobilePeek />
  if (!collapsed) return null
  return <DesktopPeek />
}

function DesktopPeek() {
  const toggle = useWorkSidebarStore((s) => s.toggle)
  const [open, setOpen] = useState(false)
  const [dialog, setDialog] = useState<'list' | 'group' | null>(null)
  const [parentGroup, setParentGroup] = useState<number | null>(null)

  return (
    <>
      {/*  `openDelay` 0 để rê tới là ra ngay — nút bé, phải nhắm mới trúng nên
           không có chuyện bung nhầm; `closeDelay` rộng tay hơn vì đường chuột đi
           từ nút xuống thẻ có một quãng hở. */}
      <HoverCard open={open} openDelay={0} closeDelay={150} onOpenChange={setOpen}>
        <HoverCardTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="mt-0.5 size-7 shrink-0 text-muted-foreground hover:text-foreground"
            title="Hiện danh sách dự án"
            aria-label="Hiện danh sách dự án"
            onClick={() => {
              setOpen(false)
              toggle()
            }}
          >
            <PanelLeftOpen className="size-4" />
          </Button>
        </HoverCardTrigger>

        {/*  `p-0` vì `WorkSidebarTree` tự lo lề của nó; `w-auto` để thẻ lấy đúng
             bề rộng `w-64` của cây thay vì bề rộng mặc định của HoverCard. */}
        <HoverCardContent align="start" sideOffset={8} className="w-auto p-0">
          <div className="h-[min(28rem,60dvh)]">
            <WorkSidebarTree
              peeking
              onToggleCollapse={() => {
                setOpen(false)
                toggle()
              }}
              onCreateGroup={() => {
                setOpen(false)
                setParentGroup(null)
                setDialog('group')
              }}
              onCreateList={(groupId) => {
                setOpen(false)
                setParentGroup(groupId)
                setDialog('list')
              }}
            />
          </div>
        </HoverCardContent>
      </HoverCard>

      <WorkCreateDialog
        mode={dialog}
        parentGroupId={parentGroup}
        onClose={() => setDialog(null)}
      />
    </>
  )
}

/**
 * Bản khổ hẹp: bấm để cây trượt ra từ mép trái, phủ lên nội dung.
 *
 * Ba chỗ khác bản desktop, cả ba đều bắt buộc:
 *
 * ⚠️ **Nút LUÔN hiện, không đọc `collapsed`.** Dưới 768px `WorkLayoutPage`
 * không dựng cây cạnh nội dung nữa, nên trạng thái "đang mở" của desktop không
 * còn ứng với thứ gì trên màn hình. Cứ đọc `collapsed` như cũ thì người dùng
 * mở màn hình trên máy tính (cây đang mở), lấy điện thoại ra xem: cây không
 * dựng, mà nút mở cây cũng ẩn nốt — không còn đường nào tới danh sách dự án.
 *
 * ⚠️ **Tờ trượt, không phải thẻ nổi.** `HoverCard` mở bằng `pointerenter`; màn
 * cảm ứng không có sự kiện đó nên bản desktop chỉ còn nhánh `onClick` = ghim
 * cây lại — tức đúng cái bố cục vừa bỏ đi.
 *
 * ⚠️ **Chọn một dự án là ĐÓNG tờ trượt** (`onNavigate`). Tờ trượt che gần trọn
 * màn; không đóng thì route đổi phía sau tấm phủ và người dùng chỉ thấy cây
 * đứng im — nhìn ra như cú chạm bị rơi.
 */
function MobilePeek() {
  const [open, setOpen] = useState(false)
  const [dialog, setDialog] = useState<'list' | 'group' | null>(null)
  const [parentGroup, setParentGroup] = useState<number | null>(null)

  return (
    <>
      <Sheet open={open} onOpenChange={setOpen}>
        <Button
          variant="ghost"
          size="icon"
          className="mt-0.5 size-7 shrink-0 text-muted-foreground hover:text-foreground"
          title="Hiện danh sách dự án"
          aria-label="Hiện danh sách dự án"
          onClick={() => setOpen(true)}
        >
          <PanelLeftOpen className="size-4" />
        </Button>

        {/*  `p-0` + `w-64` để cây giữ đúng bề rộng của nó; `showCloseButton`
             tắt vì cây đã có nút riêng ở dải tiêu đề, hai dấu X cạnh nhau thì
             không đoán được cái nào đóng cái gì. */}
        <SheetContent side="left" showCloseButton={false} className="w-64 gap-0 p-0 sm:max-w-none">
          <SheetHeader className="sr-only">
            <SheetTitle>Danh sách dự án</SheetTitle>
          </SheetHeader>
          <WorkSidebarTree
            peeking
            onNavigate={() => setOpen(false)}
            onToggleCollapse={() => setOpen(false)}
            onCreateGroup={() => {
              setOpen(false)
              setParentGroup(null)
              setDialog('group')
            }}
            onCreateList={(groupId) => {
              setOpen(false)
              setParentGroup(groupId)
              setDialog('list')
            }}
          />
        </SheetContent>
      </Sheet>

      <WorkCreateDialog
        mode={dialog}
        parentGroupId={parentGroup}
        onClose={() => setDialog(null)}
      />
    </>
  )
}
