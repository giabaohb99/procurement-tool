import { Search } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { cn } from '@/shared/utils/cn'
import { coffeeApi } from '../api/coffee-api'
import type { CounterLookupResult } from '../types/coffee'
import { formatPoints } from '../utils/format-points'

/** Kết quả tự xóa sau chừng này giây — người sau không thấy số của người trước. */
const CLEAR_AFTER_MS = 30_000

/**
 * Tra cứu số dư cho QUẦY (C-04) — màn tối giản cho tablet đặt cạnh máy POS:
 * một ô nhập, một con số to. API chỉ trả {name, balance} nên màn không thể lộ
 * hơn kể cả viết ẩu. Đây là lớp vá số 2 cho việc POS365 không tự chặn hết điểm.
 */
export function CoffeeLookupPage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<CounterLookupResult | null>(null)
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(
    () => () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    },
    [],
  )

  async function handleLookup() {
    const q = query.trim()
    if (q.length < 3) {
      toast.error('Nhập mã nhân viên hoặc số điện thoại đầy đủ.')
      return
    }
    setLoading(true)
    try {
      const data = await coffeeApi.counterLookup(q)
      setResult(data)
      setQuery('')
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => setResult(null), CLEAR_AFTER_MS)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    } finally {
      setLoading(false)
    }
  }

  const balance = result?.balance ?? 0

  return (
    <PageContainer>
      <div className="mx-auto flex w-full max-w-xl flex-col gap-6 pt-10">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">Tra cứu điểm cà phê</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Nhập MÃ NHÂN VIÊN hoặc SỐ ĐIỆN THOẠI rồi Enter — kiểm tra trước khi bấm «Trừ điểm»
            với đơn lớn.
          </p>
        </div>

        <div className="flex gap-2">
          <Input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleLookup()
            }}
            placeholder="vd NV0012 hoặc 0909xxxxxx"
            className="h-12 text-lg"
          />
          <Button size="lg" className="h-12" onClick={() => void handleLookup()} disabled={loading}>
            <Search className="size-5" />
            Tra
          </Button>
        </div>

        {result &&
          (result.found && result.unlimited ? (
            <Card className="flex flex-col items-center gap-2 border-emerald-500/50 bg-emerald-500/5 p-10 text-center">
              <div className="text-xl font-medium">{result.name}</div>
              {/*  ∞ cùng cỡ text-6xl với con số của người thường — nhất quán một giọng. */}
              <div className="text-6xl font-bold tabular-nums text-emerald-600 dark:text-emerald-400">
                ∞
              </div>
              <div className="text-sm text-muted-foreground">
                Không giới hạn — cứ bấm «Trừ điểm», không cần hỏi
              </div>
            </Card>
          ) : result.found ? (
            <Card
              className={cn(
                'flex flex-col items-center gap-2 p-10 text-center',
                balance < 0 && 'border-destructive/50 bg-destructive/5',
                balance === 0 && 'border-amber-500/50 bg-amber-500/5',
              )}
            >
              <div className="text-xl font-medium">{result.name}</div>
              <div
                className={cn(
                  'text-6xl font-bold tabular-nums',
                  balance > 0 && 'text-emerald-600 dark:text-emerald-400',
                  balance === 0 && 'text-amber-600 dark:text-amber-400',
                  balance < 0 && 'text-destructive',
                )}
              >
                {formatPoints(balance)}
              </div>
              <div className="text-sm text-muted-foreground">
                {balance > 0
                  ? 'điểm còn dùng được'
                  : balance === 0
                    ? 'đã hết điểm — thu tiền mặt / chuyển khoản'
                    : 'ĐANG ÂM — báo quản trị, thu tiền phần vượt'}
              </div>
            </Card>
          ) : (
            <Card className="p-10 text-center text-muted-foreground">
              Không tìm thấy — người này chưa thuộc chương trình hoặc gõ chưa đúng mã/SĐT.
            </Card>
          ))}
      </div>
    </PageContainer>
  )
}
