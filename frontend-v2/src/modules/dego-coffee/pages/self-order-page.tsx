import { Coffee, CupSoda, Minus, Plus, Send, ShoppingCart, Trash2, Wallet } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { cn } from '@/shared/utils/cn'
import { CoffeeBlock } from '../components/coffee-block'
import { useCoffeeMenu, useMyWallet, useSelfOrder } from '../hooks/use-coffee'
import type { MenuItem } from '../types/coffee'
import { formatPoints } from '../utils/format-points'

interface CartLine {
  item: MenuItem
  quantity: number
}

/**
 * TỰ ĐẶT NƯỚC (chốt 08/09/2026): menu + ảnh đọc thẳng từ POS365, nhân sự bấm
 * đặt → DEGO tạo đơn trên POS365 (trả trọn bằng «Trừ điểm», gắn khách đã ghép)
 * → quầy thấy đơn và pha → điểm trừ vào ví qua vòng kéo.
 */
export function SelfOrderPage() {
  const { data: wallet } = useMyWallet()
  const { data: menu, isLoading, isError, error } = useCoffeeMenu()
  const selfOrder = useSelfOrder()
  const [cart, setCart] = useState<CartLine[]>([])
  const [note, setNote] = useState('')

  const unlimited = wallet?.member?.unlimited ?? false
  const balance = wallet?.balance ?? 0
  const notMember = wallet !== undefined && wallet.member === null
  const notMatched = Boolean(wallet?.member && wallet.member.pos_partner_id === 0)

  const total = cart.reduce((sum, line) => sum + line.item.price * line.quantity, 0)
  const overBudget = !unlimited && total > balance

  const groups = useMemo(() => {
    const byCategory = new Map<string, MenuItem[]>()
    for (const item of menu?.items ?? []) {
      const list = byCategory.get(item.category) ?? []
      list.push(item)
      byCategory.set(item.category, list)
    }
    return [...byCategory.entries()]
  }, [menu?.items])

  function addToCart(item: MenuItem) {
    setCart((prev) => {
      const found = prev.find((l) => l.item.product_id === item.product_id)
      if (found) {
        return prev.map((l) =>
          l.item.product_id === item.product_id
            ? { ...l, quantity: Math.min(l.quantity + 1, 20) }
            : l,
        )
      }
      return [...prev, { item, quantity: 1 }]
    })
  }

  function changeQuantity(productId: number, delta: number) {
    setCart((prev) =>
      prev
        .map((l) =>
          l.item.product_id === productId ? { ...l, quantity: l.quantity + delta } : l,
        )
        .filter((l) => l.quantity > 0),
    )
  }

  function submitOrder() {
    selfOrder.mutate(
      {
        items: cart.map((l) => ({ product_id: l.item.product_id, quantity: l.quantity })),
        note,
      },
      {
        onSuccess: (result) => {
          toast.success(
            `Đã gửi đơn ${result.code} sang quầy — ${formatPoints(result.total)} điểm` +
              (result.balance === null ? '' : `, ví còn ${formatPoints(result.balance)}`),
          )
          setCart([])
          setNote('')
        },
      },
    )
  }

  if (notMember || notMatched) {
    return (
      <PageContainer>
        <PageHeader title="Đặt nước" />
        <Card className="flex flex-col items-center gap-3 p-10 text-center">
          <Coffee className="size-10 text-muted-foreground" />
          <div className="font-medium">
            {notMember ? 'Bạn chưa thuộc chương trình điểm cà phê' : 'Hồ sơ chưa ghép với POS365'}
          </div>
          <p className="max-w-md text-sm text-muted-foreground">
            Liên hệ phòng Nhân sự để được {notMember ? 'gán cấp phúc lợi' : 'ghép với quầy'} —
            sau đó bạn đặt nước ngay tại đây, quầy nhận đơn và pha.
          </p>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer fill className="gap-6">
      <PageHeader
        title="Đặt nước"
        description="Chọn món — đơn gửi thẳng sang quầy POS365, điểm trừ vào ví sau khi quầy ghi nhận."
        actions={
          <Badge variant="outline" className="gap-1.5 px-3 py-1.5 text-sm">
            <Wallet className="size-4" />
            {unlimited ? '∞ điểm' : `${formatPoints(balance)} điểm`}
          </Badge>
        }
      />

      {isError ? (
        <Card className="p-10 text-center text-sm text-muted-foreground">
          Không đọc được thực đơn từ POS365: {extractErrorMessage(error)}
        </Card>
      ) : (
        <div className="grid min-h-0 flex-1 gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="min-h-0 overflow-y-auto pr-1">
            {isLoading && (
              <p className="p-6 text-sm text-muted-foreground">Đang tải thực đơn…</p>
            )}
            {groups.map(([category, items]) => (
              <section key={category} className="mb-6">
                <h3 className="mb-2 border-b pb-1 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                  {category}
                </h3>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
                  {items.map((item) => (
                    <button
                      key={item.product_id}
                      type="button"
                      onClick={() => addToCart(item)}
                      className="group flex flex-col overflow-hidden rounded-lg border bg-card text-left transition-colors hover:border-primary/50 hover:bg-accent/40"
                    >
                      <div className="relative aspect-[4/3] w-full overflow-hidden bg-muted">
                        {item.image ? (
                          <img
                            src={item.image}
                            alt={item.name}
                            loading="lazy"
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center">
                            <CupSoda className="size-8 text-muted-foreground" />
                          </div>
                        )}
                        <span className="absolute right-1.5 bottom-1.5 rounded-md bg-background/90 px-1.5 py-0.5 text-xs font-medium tabular-nums">
                          {formatPoints(item.price)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between gap-1 p-2">
                        <span className="truncate text-sm font-medium">{item.name}</span>
                        <Plus className="size-4 shrink-0 text-muted-foreground group-hover:text-primary" />
                      </div>
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </div>

          <CoffeeBlock
            icon={ShoppingCart}
            title="Đơn của bạn"
            className="flex h-fit flex-col gap-3 lg:sticky lg:top-0"
          >
            {cart.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                Bấm vào món để thêm vào đơn.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {cart.map((line) => (
                  <div key={line.item.product_id} className="flex items-center gap-2">
                    <span className="min-w-0 flex-1 truncate text-sm">{line.item.name}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="size-7"
                      onClick={() => changeQuantity(line.item.product_id, -1)}
                    >
                      {line.quantity === 1 ? (
                        <Trash2 className="size-3.5" />
                      ) : (
                        <Minus className="size-3.5" />
                      )}
                    </Button>
                    <span className="w-5 text-center text-sm tabular-nums">{line.quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      className="size-7"
                      onClick={() => changeQuantity(line.item.product_id, 1)}
                    >
                      <Plus className="size-3.5" />
                    </Button>
                    <span className="w-16 text-right text-sm tabular-nums">
                      {formatPoints(line.item.price * line.quantity)}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <Input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Ghi chú cho quầy (ít đá, ít đường…)"
              maxLength={200}
            />
            <div className="flex items-center justify-between border-t pt-2">
              <span className="text-sm text-muted-foreground">Tổng</span>
              <span
                className={cn('text-lg font-semibold tabular-nums', overBudget && 'text-destructive')}
              >
                {formatPoints(total)}
              </span>
            </div>
            {overBudget && (
              <p className="text-sm text-destructive">
                Không đủ điểm — ví còn {formatPoints(balance)}.
              </p>
            )}
            <Button
              disabled={cart.length === 0 || overBudget || selfOrder.isPending}
              onClick={submitOrder}
            >
              <Send className="size-4" />
              Đặt nước
            </Button>
          </CoffeeBlock>
        </div>
      )}
    </PageContainer>
  )
}
