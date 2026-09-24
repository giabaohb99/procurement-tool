/** Loại token của một mẩu JSON — quyết định màu chữ, không quyết định gì khác. */
export type JsonTokenKind = 'key' | 'string' | 'number' | 'keyword' | 'plain'

export interface JsonToken {
  text: string
  kind: JsonTokenKind
}

/**
 * Khóa (`"status":`) · chuỗi · số · `true|false|null`. Bốn nhóm bắt theo đúng
 * thứ tự đó vì khóa CŨNG là một chuỗi — để nhánh chuỗi lên trước thì mọi khóa
 * đều ra màu chuỗi và mất hẳn tầng phân biệt.
 *
 * Chuỗi khớp `"(?:\\.|[^"\\])*"` chứ không phải `"[^"]*"`: thân yêu cầu hay có
 * đường dẫn và chữ Việt đã escape (`"Đã cập nhật \"tiến độ\""`), mẫu ngây thơ
 * cắt ngay tại dấu nháy đã escape rồi lệch màu suốt phần còn lại của dòng.
 */
const TOKEN_PATTERN =
  /("(?:\\.|[^"\\])*")(\s*:)|("(?:\\.|[^"\\])*")|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(true|false|null)\b/g

/**
 * Cắt một chuỗi JSON ĐÃ in đẹp thành các mẩu để tô màu.
 *
 * Hàm THUẦN, trả mảng — tầng React chỉ việc bọc mỗi mẩu trong một `<span>`. Cố ý
 * KHÔNG sinh HTML: dựng chuỗi HTML rồi nhét bằng `dangerouslySetInnerHTML` là mở
 * cửa cho nội dung nhật ký (vốn do người dùng gõ vào) chạy như mã — mà đây đúng
 * là màn chứa dữ liệu bẩn nhất hệ thống.
 *
 * Không phải trình phân tích JSON: nó soi mẫu chứ không hiểu cấu trúc. Đủ dùng
 * cho việc tô màu, và văn bản KHÔNG phải JSON (traceback) đi qua đây vẫn ra chữ
 * nguyên vẹn — chỉ là hầu hết rơi vào `plain`.
 */
export function tokenizeJson(text: string): JsonToken[] {
  if (!text) return []

  const tokens: JsonToken[] = []
  let last = 0

  //  `exec` trong vòng lặp với cờ `g`: mỗi lượt tự đẩy `lastIndex`, nên phải
  //  dùng CÙNG một biểu thức và không được gọi `test` xen vào giữa.
  TOKEN_PATTERN.lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = TOKEN_PATTERN.exec(text)) !== null) {
    const [whole, keyName, colon, str, num, keyword] = match

    if (match.index > last) {
      tokens.push({ text: text.slice(last, match.index), kind: 'plain' })
    }

    if (keyName) {
      tokens.push({ text: keyName, kind: 'key' })
      //  Dấu hai chấm (kèm khoảng trắng trước nó) là dấu câu, không phải khóa —
      //  gộp vào token khóa thì nó ăn luôn màu khóa và nhìn ra một cụm lạ.
      tokens.push({ text: colon, kind: 'plain' })
    } else if (str) {
      tokens.push({ text: str, kind: 'string' })
    } else if (num) {
      tokens.push({ text: num, kind: 'number' })
    } else if (keyword) {
      tokens.push({ text: keyword, kind: 'keyword' })
    }

    last = match.index + whole.length
  }

  if (last < text.length) tokens.push({ text: text.slice(last), kind: 'plain' })

  return tokens
}
