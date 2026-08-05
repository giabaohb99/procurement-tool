import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Loader2, Search } from 'lucide-react'

import { api } from '@/api/client'
import { Input } from '@/components/ui/input'
import { useArticlePath } from '@/lib/help-slug'
import { cn } from '@/lib/utils'

// Ô tìm kiếm tài liệu — debounce 300ms. Backend tìm theo CẢ tiêu đề lẫn nội dung
// và trả về đoạn trích quanh từ khóa (match_at/match_len) để tô đậm chỗ khớp.

export interface HelpSearchHit {
  id: number
  title: string
  parent_id: number | null
  in_title: boolean
  snippet: string
  match_at: number
  match_len: number
}

interface HelpSearchBoxProps {
  size?: 'sm' | 'lg'
  basePath?: string
  placeholder?: string
  className?: string
}

/** Bôi đậm đúng đoạn khớp trong trích đoạn (offset do backend tính, kể cả khi gõ không dấu). */
function Snippet({ hit }: { hit: HelpSearchHit }) {
  if (!hit.snippet) return null
  if (hit.match_at < 0) {
    return <span className="line-clamp-2 text-muted-foreground">{hit.snippet}</span>
  }
  const before = hit.snippet.slice(0, hit.match_at)
  const match = hit.snippet.slice(hit.match_at, hit.match_at + hit.match_len)
  const after = hit.snippet.slice(hit.match_at + hit.match_len)
  return (
    <span className="line-clamp-2 text-muted-foreground">
      {before}
      <mark className="rounded-sm bg-primary/10 px-0.5 font-semibold text-primary">{match}</mark>
      {after}
    </span>
  )
}

export default function HelpSearchBox({
  size = 'sm',
  basePath = '',
  placeholder = 'Tìm kiếm tài liệu...',
  className,
}: HelpSearchBoxProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<HelpSearchHit[]>([])
  const [searching, setSearching] = useState(false)
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  // basePath rỗng = khu người dùng -> đường dẫn dạng slug; có basePath (/admin) -> vẫn theo id
  const pathOf = useArticlePath()

  useEffect(() => {
    const kw = query.trim()
    if (!kw) {
      setResults([])
      setOpen(false)
      return
    }
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await api.get('/api/v1/help-center/search', { params: { q: kw } })
        setResults(res.data.data)
        setOpen(true)
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  // Đóng dropdown khi bấm ra ngoài
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const isLarge = size === 'lg'

  return (
    <div ref={boxRef} className={cn('relative', className)}>
      <Search
        className={cn(
          'pointer-events-none absolute top-1/2 -translate-y-1/2 text-muted-foreground',
          isLarge ? 'left-6 size-5' : 'left-3 size-4',
        )}
      />
      <Input
        value={query}
        placeholder={placeholder}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => { if (query.trim()) setOpen(true) }}
        className={cn(
          'bg-background',
          isLarge
            // Ô tìm kiếm lớn ở trang chủ: cao, bo tròn, bóng mềm, không viền cứng
            ? 'h-16 rounded-2xl border-transparent pl-14 pr-6 text-[1.125rem] shadow-[0_4px_24px_rgba(0,0,0,0.06)] md:text-[1.125rem]'
            : 'h-9 pl-9 pr-4',
        )}
      />
      {searching && (
        <Loader2 className={cn(
          'absolute top-1/2 -translate-y-1/2 animate-spin text-muted-foreground',
          isLarge ? 'right-4 size-[1.125rem]' : 'right-3 size-4',
        )} />
      )}

      {open && (
        <div className="absolute left-0 right-0 z-50 mt-1.5 max-h-[24rem] overflow-y-auto rounded-md border bg-popover p-1 text-left shadow-lg">
          {results.length > 0 ? (
            results.map((hit) => (
              <Link
                key={hit.id}
                to={basePath ? `${basePath}/${hit.id}` : pathOf(hit.id)}
                onClick={() => { setOpen(false); setQuery('') }}
                className="flex gap-3 rounded-sm px-3 py-2.5 transition-colors hover:bg-secondary"
              >
                <FileText className="mt-0.5 size-4 shrink-0 text-primary" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-navy">{hit.title}</span>
                  <span className="mt-0.5 block text-xs leading-relaxed">
                    <Snippet hit={hit} />
                  </span>
                </span>
              </Link>
            ))
          ) : (
            <div className="px-3 py-6 text-center text-sm text-muted-foreground">
              {searching ? 'Đang tìm...' : 'Không tìm thấy tài liệu'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
