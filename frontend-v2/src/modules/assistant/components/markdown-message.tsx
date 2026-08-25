import ReactMarkdown, { type Components } from 'react-markdown'
// react-markdown + remark-gfm: bot trả về Markdown (đậm, danh sách, bảng, khối code) nên phải render,
// đừng in thô. KHÔNG bật rehype-raw → HTML thô trong nội dung không được chèn (an toàn, khỏi lo XSS).
import remarkGfm from 'remark-gfm'

import { cn } from '@/shared/utils/cn'

/** Ánh xạ từng phần tử Markdown sang lớp Tailwind — thay cho plugin `prose` (dự án không cài typography). */
const components: Components = {
  p: ({ children }) => <p className="leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline underline-offset-2 hover:opacity-80"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  h1: ({ children }) => <h1 className="mt-1 text-base font-semibold">{children}</h1>,
  h2: ({ children }) => <h2 className="mt-1 text-sm font-semibold">{children}</h2>,
  h3: ({ children }) => <h3 className="mt-1 text-sm font-medium">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-border pl-3 text-muted-foreground italic">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-2 border-border" />,
  // Inline code; khối code (trong <pre>) được reset lại nền/đệm bên dưới.
  code: ({ children }) => (
    <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs [&>code]:bg-transparent [&>code]:p-0">
      {children}
    </pre>
  ),
  // Bọc bảng trong div cuộn ngang để bảng rộng không phá khung chat.
  table: ({ children }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border bg-muted px-2 py-1 text-left font-medium">{children}</th>
  ),
  td: ({ children }) => <td className="border border-border px-2 py-1 align-top">{children}</td>,
}

interface MarkdownMessageProps {
  content: string
  className?: string
}

/** Hiển thị nội dung Markdown của Trợ lý (chỉ dùng cho tin của bot, không dùng cho tin người dùng). */
export function MarkdownMessage({ content, className }: MarkdownMessageProps) {
  return (
    <div className={cn('space-y-2 break-words', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
