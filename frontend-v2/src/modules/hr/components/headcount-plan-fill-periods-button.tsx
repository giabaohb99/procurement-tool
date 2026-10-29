import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { NumberInput } from '@/shared/ui/number-input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'

interface HeadcountPlanFillPeriodsButtonProps {
  /** «Giống nhau cả năm» (kỳ Năm) · «Giống nhau cả kỳ» (Bán niên / Quý). */
  label: string
  positionLabel: string
  onFill: (value: number) => void
}

/** Nút nhỏ dưới tên vị trí: nhập MỘT số người rồi điền cho mọi kỳ con của dòng. */
export function HeadcountPlanFillPeriodsButton({ label, positionLabel, onFill }: HeadcountPlanFillPeriodsButtonProps) {
  const [open, setOpen] = useState(false)
  const [value, setValue] = useState(0)
  const apply = () => {
    onFill(value)
    setOpen(false)
  }

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (next) setValue(0)
      }}
    >
      <PopoverTrigger asChild>
        <button type="button" className="text-xs text-primary hover:underline">
          {label}
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-60 space-y-2 p-3">
        <p className="text-sm">Số người cần có ở mọi kỳ</p>
        <div
          className="flex items-center gap-2"
          onKeyDown={(e) => {
            if (e.key !== 'Enter') return
            //  `NumberInput` báo số theo từng phím nên `value` đã là số vừa gõ. Chặn Enter lan ra form cha.
            e.preventDefault()
            apply()
          }}
        >
          <NumberInput
            aria-label={`Số người mọi kỳ của ${positionLabel}`}
            value={value}
            decimals={false}
            placeholder="0"
            className="h-8 w-20 text-right"
            onChange={setValue}
          />
          <Button type="button" size="sm" onClick={apply}>
            Điền
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
