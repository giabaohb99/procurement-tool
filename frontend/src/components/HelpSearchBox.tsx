import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'

// Ô tìm kiếm tài liệu HDSD — debounce 300ms, kết quả đổ xuống dropdown.

export default function HelpSearchBox() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<{ id: number; title: string }[]>([])
  const [searching, setSearching] = useState(false)
  const [open, setOpen] = useState(false)

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

  return (
    <div style={{ position: 'relative' }}>
      <div className="hc-search">
        <i className="ti ti-search" style={{ color: 'var(--muted)', fontSize: 14, marginRight: 8 }} />
        <input
          type="text"
          placeholder="Tìm kiếm tài liệu..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (query.trim()) setOpen(true) }}
          // Trễ 200ms để cú click vào kết quả kịp chạy trước khi dropdown đóng
          onBlur={() => setTimeout(() => setOpen(false), 200)}
        />
      </div>

      {open && (
        <div className="hc-search-results">
          {searching ? (
            <div className="hc-search-empty">Đang tìm...</div>
          ) : results.length > 0 ? (
            results.map((item) => (
              <Link
                key={item.id}
                to={`/hdsd/${item.id}`}
                onClick={() => { setOpen(false); setQuery('') }}
              >
                {item.title}
              </Link>
            ))
          ) : (
            <div className="hc-search-empty">Không tìm thấy tài liệu</div>
          )}
        </div>
      )}
    </div>
  )
}
