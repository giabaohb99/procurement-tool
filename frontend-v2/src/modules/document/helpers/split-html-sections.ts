/**
 * Tách thân văn bản thành CÁC MỤC theo tiêu đề — để chọn phần cần trích thay vì
 * bắt người dùng bôi đen rồi dán tay.
 *
 * Một mục = thẻ tiêu đề + mọi khối đứng sau nó, cho tới khi gặp tiêu đề **cùng
 * cấp hoặc cao hơn**. Nhờ vậy chọn "Chương II" là lấy trọn cả các Điều nằm
 * trong chương đó, không phải tick từng cái.
 */

export interface HtmlSection {
  /** Khóa ổn định trong một lần mở hộp thoại — dùng làm key và giá trị tick. */
  id: string
  /** 1 · 2 · 3 theo h1/h2/h3, để thụt lề danh sách cho ra hình cây. */
  level: number
  title: string
  /** HTML của cả mục, gồm chính dòng tiêu đề. */
  html: string
}

const HEADING_TAGS = new Set(['H1', 'H2', 'H3'])

/**
 * Cắt HTML thành danh sách mục.
 *
 * Phần nội dung nằm TRƯỚC tiêu đề đầu tiên bị bỏ qua: đó thường là khối đầu văn
 * bản (quốc hiệu, số hiệu, ngày tháng) — thứ mà bản trích tự có, chép sang là
 * thành hai khối đầu chồng nhau.
 *
 * Văn bản không có tiêu đề nào thì trả mảng rỗng; nơi gọi phải nói với người
 * dùng là "văn bản này chưa chia mục, dán tay phần cần trích".
 */
export function splitHtmlSections(html: string): HtmlSection[] {
  if (!html || !html.trim()) return []

  //  `DOMParser` thay vì regex: nội dung có bảng, danh sách lồng nhau và thuộc
  //  tính style dài — regex cắt HTML là cách chắc chắn cắt nhầm giữa thẻ.
  const doc = new DOMParser().parseFromString(`<body>${html}</body>`, 'text/html')
  const khoi = Array.from(doc.body.children)

  //  Lượt 1: ghi lại vị trí mọi tiêu đề.
  const moc = khoi
    .map((the, i) => ({ the, i }))
    .filter(({ the }) => HEADING_TAGS.has(the.tagName))
    .map(({ the, i }) => ({ i, level: Number(the.tagName[1]), title: (the.textContent || '').trim() }))

  //  Lượt 2: mỗi tiêu đề là MỘT MỤC, chạy tới tiêu đề kế cùng cấp hoặc cao hơn.
  //  Nhờ hai lượt, mục cha bao trùm mục con mà mục con vẫn tick lẻ được — một
  //  lượt duy nhất thì tiêu đề con bị nuốt vào cha và biến mất khỏi danh sách.
  return moc.map((m, thu_tu) => {
    const ke = moc.slice(thu_tu + 1).find((x) => x.level <= m.level)
    const het = ke ? ke.i : khoi.length
    return {
      id: `muc-${thu_tu}`,
      level: m.level,
      title: m.title,
      html: khoi.slice(m.i, het).map((the) => the.outerHTML).join(''),
    }
  })
}


/** Gộp HTML của những mục được tick, giữ đúng thứ tự trong văn bản. */
export function joinSections(sections: HtmlSection[], ids: string[]): string {
  const chon = new Set(ids)
  return sections
    .filter((s) => chon.has(s.id))
    .map((s) => s.html)
    .join('')
}

/**
 * Tên gợi ý cho bản trích: "Trích {tiêu đề mục đầu tiên}".
 *
 * Chỉ GỢI Ý — người dùng sửa được. Tick nhiều mục thì lấy mục đầu và thêm "…",
 * vì ghép hết tên vào là một dòng dài không ai đọc.
 */
export function suggestExcerptTitle(sections: HtmlSection[], ids: string[]): string {
  const chon = sections.filter((s) => ids.includes(s.id))
  if (!chon.length) return ''
  return chon.length === 1 ? `Trích ${chon[0].title}` : `Trích ${chon[0].title} và ${chon.length - 1} mục khác`
}
