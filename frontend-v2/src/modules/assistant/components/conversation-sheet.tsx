import { MessagesSquare } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/shared/ui/sheet'
import { ConversationList, type ConversationListProps } from './conversation-list'

type ConversationSheetProps = Omit<ConversationListProps, 'trailing'>

/**
 * Danh sách hội thoại ở khổ ĐIỆN THOẠI — tờ trượt từ mép trái.
 *
 * ⚠️ **Cột hội thoại không thể đứng cạnh khung chat ở khổ này.** Nó rộng cố
 * định 256px, nên trên máy 390px phần chat chỉ còn ~130px và câu trả lời rớt
 * xuống mỗi dòng một từ. Nhưng cũng không bỏ hẳn được: không có nó thì hội
 * thoại cũ **không có đường nào mở lại**, và nút «Hội thoại mới» cũng mất theo.
 * Tờ trượt giữ đủ cả hai mà không ăn một pixel nào của khung chat lúc đang đọc.
 *
 * ⚠️ **Chọn một hội thoại là ĐÓNG tờ trượt.** Không đóng thì người dùng bấm
 * xong vẫn nhìn thấy danh sách, tưởng chưa ăn, rồi bấm lần nữa. Cùng lý do với
 * nút «Hội thoại mới».
 */
export function ConversationSheet({ onNew, onSelect, ...rest }: ConversationSheetProps) {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2 md:hidden">
          <MessagesSquare className="size-4" />
          Hội thoại
        </Button>
      </SheetTrigger>

      <SheetContent side="left" className="w-[86vw] max-w-sm gap-0 p-0">
        <SheetHeader className="border-b px-4 py-3">
          <SheetTitle className="text-base">Hội thoại</SheetTitle>
        </SheetHeader>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <ConversationList
            {...rest}
            onNew={() => {
              onNew()
              setOpen(false)
            }}
            onSelect={(id) => {
              onSelect(id)
              setOpen(false)
            }}
          />
        </div>
      </SheetContent>
    </Sheet>
  )
}
