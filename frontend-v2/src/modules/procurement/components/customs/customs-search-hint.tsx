import type { CustomsSearchExplain } from '../../api/customs-kind-api'

/**
 * Dòng giải thích dưới ô tìm tên hàng — bao-CR-495.
 *
 * Ô trống: nhắc cú pháp (cách nhau = có cả hai từ, dấu trừ = loại trừ). Có chữ: bày từng từ và
 * các cách viết nó sẽ khớp, để người dùng thấy vì sao «3,6%» ra cả dòng «36 G/L».
 */
interface CustomsSearchHintProps {
  query: string
  explain?: CustomsSearchExplain
}

function joinMatches(matches: string[]): string {
  const shown = matches.slice(0, 4).join(' · ')
  return matches.length > 4 ? `${shown} · +${matches.length - 4}` : shown
}

export function CustomsSearchHint({ query, explain }: CustomsSearchHintProps) {
  if (!query.trim() || !explain) {
    return (
      <p className="text-xs text-muted-foreground">
        Mẹo: gõ nhiều từ để tìm dòng có ĐỦ các từ đó; thêm dấu trừ trước từ cần loại (vd{' '}
        <span className="font-mono">abamectin 3.6 -TC</span>); nồng độ 3,6% tự khớp 3.6EC và 36 G/L.
      </p>
    )
  }
  return (
    <p className="text-xs text-muted-foreground">
      {explain.include.map((part) => (
        <span key={`in-${part.term}`} className="mr-3">
          Có «{part.term}»: {joinMatches(part.matches)}
        </span>
      ))}
      {explain.exclude.map((part) => (
        <span key={`ex-${part.term}`} className="mr-3 text-destructive">
          Không có «{part.term}»: {joinMatches(part.matches)}
        </span>
      ))}
    </p>
  )
}
