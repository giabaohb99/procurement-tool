// Cột «Tìm kiếm» + «Tra cứu nhanh» của trang chi tiết thuốc BVTV (01/10/2026 — bê theo cột trái
// của trang nguồn danhmuc.thuocbvtv.com): đang đọc một thuốc mà muốn tra thuốc khác thì gõ / chọn
// ngay tại đây, không phải lùi về danh sách. Bấm «Lọc» hay một phân nhóm là mở mục «Thuốc BVTV»
// với đúng bộ lọc đó (`buildPesticideListSearch`).
import { Search, Zap } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'

import { buildCustomsSectionPath } from '../../config/customs-sections'
import { useCustomsPesticideOptions } from '../../hooks/use-customs-pesticides'
import { ALL_PESTICIDE_OPTIONS, buildPesticideListSearch } from '../../utils/customs-pesticide'
import { toSentenceCaseIfShouting } from '../../utils/customs-pesticide-display'

interface CustomsPesticideLookupSidebarProps {
  /** Phân nhóm của thuốc đang xem — tô đậm trong «Tra cứu nhanh» để biết mình đang ở nhóm nào. */
  currentPestGroup: string
  className?: string
}

const LIST_PATH = buildCustomsSectionPath('pesticides')

export function CustomsPesticideLookupSidebar({
  currentPestGroup,
  className,
}: CustomsPesticideLookupSidebarProps) {
  const navigate = useNavigate()
  const options = useCustomsPesticideOptions()
  const [keyword, setKeyword] = useState('')
  const [pestGroup, setPestGroup] = useState(ALL_PESTICIDE_OPTIONS)
  const [sector, setSector] = useState(ALL_PESTICIDE_OPTIONS)
  const dirty =
    keyword.trim() !== '' || pestGroup !== ALL_PESTICIDE_OPTIONS || sector !== ALL_PESTICIDE_OPTIONS

  function submit(event: FormEvent) {
    event.preventDefault()
    navigate({
      pathname: LIST_PATH,
      search: buildPesticideListSearch({ q: keyword, pestGroup, sector }),
    })
  }

  function reset() {
    setKeyword('')
    setPestGroup(ALL_PESTICIDE_OPTIONS)
    setSector(ALL_PESTICIDE_OPTIONS)
  }

  return (
    <Card className={cn('gap-0 py-0', className)}>
      <form onSubmit={submit} className="space-y-3 border-b p-4">
        <SectionTitle icon={Search}>Tìm thuốc khác</SectionTitle>
        <Input
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="Tên thuốc, hoạt chất, công ty…"
          aria-label="Tìm thuốc BVTV"
        />
        <Select value={pestGroup} onValueChange={setPestGroup}>
          <SelectTrigger className="w-full" aria-label="Phân nhóm">
            <SelectValue placeholder="Phân nhóm" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_PESTICIDE_OPTIONS}>Tất cả phân nhóm</SelectItem>
            {(options.data?.pest_groups ?? []).map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.value}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sector} onValueChange={setSector}>
          <SelectTrigger className="w-full" aria-label="Lĩnh vực">
            <SelectValue placeholder="Lĩnh vực" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_PESTICIDE_OPTIONS}>Tất cả lĩnh vực</SelectItem>
            {(options.data?.sectors ?? []).map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {toSentenceCaseIfShouting(item.value)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex gap-2">
          <Button type="submit" className="flex-1">
            <Search className="size-4" />
            Lọc
          </Button>
          <Button type="button" variant="outline" onClick={reset} disabled={!dirty}>
            Xóa bộ lọc
          </Button>
        </div>
      </form>

      <nav className="p-4" aria-label="Tra cứu nhanh theo phân nhóm">
        <SectionTitle icon={Zap}>Tra cứu nhanh</SectionTitle>
        <ul className="mt-2 space-y-0.5">
          {(options.data?.pest_groups ?? []).map((item) => {
            const current = item.value === currentPestGroup
            return (
              <li key={item.value}>
                <Link
                  to={{
                    pathname: LIST_PATH,
                    search: buildPesticideListSearch({ pestGroup: item.value }),
                  }}
                  aria-current={current ? 'true' : undefined}
                  className={cn(
                    'flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-row-hover hover:text-primary',
                    current && 'bg-primary/10 font-medium text-primary',
                  )}
                >
                  <span className="truncate" title={item.value}>
                    {item.value}
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                    {item.count.toLocaleString('vi-VN')}
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </Card>
  )
}

function SectionTitle({ icon: Icon, children }: { icon: typeof Search; children: string }) {
  return (
    <h2 className="flex items-center gap-1.5 text-sm font-semibold">
      <Icon className="size-4 text-muted-foreground" aria-hidden />
      {children}
    </h2>
  )
}
