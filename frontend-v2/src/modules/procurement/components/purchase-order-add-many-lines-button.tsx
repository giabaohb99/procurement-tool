import { Rows3 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { parseAddManyLinesCount } from './purchase-order-add-many-lines-count'

interface PurchaseOrderAddManyLinesButtonProps {
  onAdd: (count: number) => void
}

/**
 * Nút *Thêm nhiều* ở tiêu đề thẻ Dòng hàng (duoc-CR-741, bản v1 có, v2 thiếu): hỏi số dòng
 * (mặc định 3) rồi thêm chừng ấy dòng trống. Hộp hỏi dựng như hộp nhập của v1 — tiêu đề
 * *Nhập thông tin*, nút *Xác nhận* / *Hủy*.
 */
export function PurchaseOrderAddManyLinesButton({ onAdd }: PurchaseOrderAddManyLinesButtonProps) {
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState('3')

  function openDialog() {
    setValue('3')
    setOpen(true)
  }

  function confirm() {
    onAdd(parseAddManyLinesCount(value))
    setOpen(false)
  }

  return (
    <>
      <Button type="button" variant="outline" size="sm" onClick={openDialog}>
        <Rows3 />
        Thêm nhiều
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Nhập thông tin</DialogTitle>
            <DialogDescription>Thêm bao nhiêu dòng?</DialogDescription>
          </DialogHeader>
          <Input
            aria-label="Số dòng cần thêm"
            inputMode="numeric"
            autoFocus
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={(event) => {
              //  Enter = Xác nhận, và không để phím lọt ra form cha (bẫy biểu mẫu thứ hai).
              if (event.key === 'Enter') {
                event.preventDefault()
                confirm()
              }
            }}
          />
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Hủy
            </Button>
            <Button type="button" onClick={confirm}>
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
