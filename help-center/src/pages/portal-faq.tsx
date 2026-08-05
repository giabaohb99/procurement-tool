import { useEffect, useState } from 'react'
import { MessageCircleQuestion, Search } from 'lucide-react'

import HelpBreadcrumb from '@/components/help-breadcrumb'
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from '@/components/ui/accordion'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { fetchFaqs, type Faq } from '@/lib/faq-api'

// /cau-hoi-thuong-gap — trang người dùng: danh sách câu hỏi dạng gập/mở, lọc tại chỗ.

/** Bỏ dấu + chữ thường để lọc theo kiểu gõ không dấu. */
function fold(text: string): string {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[đĐ]/g, 'd').toLowerCase()
}

export default function PortalFaq() {
  const [faqs, setFaqs] = useState<Faq[] | null>(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    let cancelled = false
    fetchFaqs(true)
      .then((data) => { if (!cancelled) setFaqs(data) })
      .catch(() => { if (!cancelled) setFaqs([]) })
    window.scrollTo({ top: 0 })
    return () => { cancelled = true }
  }, [])

  const kw = fold(filter.trim())
  const shown = (faqs || []).filter(
    (f) => !kw || fold(f.question).includes(kw) || fold(f.answer).includes(kw),
  )

  return (
    <div className="mx-auto max-w-3xl px-6 pb-16 pt-8 md:px-8">
      <div className="mb-5">
        <HelpBreadcrumb crumbs={[{ id: 0, title: 'Câu hỏi thường gặp' }]} />
      </div>

      <h1 className="mb-2.5 border-b pb-4 text-[1.8rem] font-bold leading-tight text-navy">
        Câu hỏi thường gặp
      </h1>

      {faqs === null ? (
        <div className="space-y-3 pt-2">
          {Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-14 w-full" />)}
        </div>
      ) : faqs.length === 0 ? (
        <div className="mt-6 rounded-md border border-dashed px-6 py-12 text-center">
          <MessageCircleQuestion className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
          <strong className="block text-navy">Chưa có câu hỏi nào</strong>
          <span className="text-sm text-muted-foreground">
            Quản trị viên chưa đăng câu hỏi thường gặp. Vui lòng quay lại sau.
          </span>
        </div>
      ) : (
        <>
          <div className="relative mb-2 mt-4 max-w-sm">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Lọc câu hỏi..."
              className="h-9 pl-9"
            />
          </div>

          {shown.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              Không có câu hỏi nào khớp từ khóa.
            </p>
          ) : (
            <Accordion type="single" collapsible className="w-full">
              {shown.map((faq) => (
                <AccordionItem key={faq.id} value={String(faq.id)}>
                  <AccordionTrigger className="text-left text-[0.9375rem] font-semibold text-navy hover:no-underline">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent>
                    {faq.answer ? (
                      <div className="hc-content" dangerouslySetInnerHTML={{ __html: faq.answer }} />
                    ) : (
                      <span className="text-muted-foreground">Chưa có câu trả lời.</span>
                    )}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </>
      )}
    </div>
  )
}
