import { ChevronsUpDown, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import type { ProductOption } from '../api/purchase-request-support-api'
import { usePurchaseRequestProducts } from '../hooks/use-purchase-request-support'

interface PurchaseRequestProductPickerProps {
  code: string
  name: string
  onPick: (product: ProductOption | null) => void
}

/**
 * Ô tìm sản phẩm theo mã hoặc tên. Danh mục có thể có hàng nghìn bản ghi nên
 * lọc phía server và debounce giống ProductPicker của frontend cũ.
 */
export function PurchaseRequestProductPicker({
  code,
  name,
  onPick,
}: PurchaseRequestProductPickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const debouncedKeyword = useDebouncedValue(keyword, 250)
  const products = usePurchaseRequestProducts(debouncedKeyword, open)

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setKeyword('')
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          className={cn(
            'h-9 w-full min-w-0 justify-between px-3 font-normal',
            !code && 'text-muted-foreground',
          )}
          title={code ? `${code} - ${name}` : undefined}
        >
          <span className="truncate">{code || 'Gõ mã/tên để tìm...'}</span>
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-[min(28rem,calc(100vw-2rem))] p-2"
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <Input
          autoFocus
          value={keyword}
          placeholder="Gõ mã hoặc tên sản phẩm..."
          onChange={(event) => setKeyword(event.target.value)}
        />

        <div className="mt-2 max-h-64 overflow-y-auto">
          {products.isLoading && (
            <p className="flex items-center justify-center gap-2 p-4 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Đang tìm sản phẩm...
            </p>
          )}

          {products.isError && (
            <p className="p-4 text-center text-sm text-destructive">
              Không tải được danh mục sản phẩm.
            </p>
          )}

          {!products.isLoading && !products.isError && products.data?.items.length === 0 && (
            <p className="p-4 text-center text-sm text-muted-foreground">
              Không tìm thấy sản phẩm.
            </p>
          )}

          {code && (
            <button
              type="button"
              className="block w-full rounded-sm px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-accent"
              onClick={() => {
                onPick(null)
                setOpen(false)
              }}
            >
              Bỏ chọn sản phẩm
            </button>
          )}

          {products.data?.items.map((product) => (
            <button
              key={product.id}
              type="button"
              className={cn(
                'block w-full rounded-sm px-3 py-2 text-left transition-colors hover:bg-accent',
                product.code === code && 'bg-accent',
              )}
              onClick={() => {
                onPick(product)
                setOpen(false)
              }}
            >
              <span className="block text-sm font-semibold text-foreground">{product.code}</span>
              <span className="block truncate text-xs text-muted-foreground">{product.name}</span>
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
