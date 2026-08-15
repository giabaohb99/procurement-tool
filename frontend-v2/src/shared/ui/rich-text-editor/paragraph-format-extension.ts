import { Extension } from '@tiptap/core'

/** Hai loại khối có thể đặt giãn dòng / thụt lề — bảng và danh sách thì không. */
const TYPES = ['paragraph', 'heading']

/** Một nấc thụt lề ≈ 1,27cm, đúng nấc Tab mặc định của Word. */
const INDENT_STEP = 48
const MAX_INDENT = 480

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    paragraphFormat: {
      /** Giãn dòng, vd `'1.5'`; `null` = trả về mặc định của trang. */
      setLineHeight: (value: string | null) => ReturnType
      indent: () => ReturnType
      outdent: () => ReturnType
    }
  }
}

/** Đọc nấc thụt lề của đoạn đang đứng, dù đó là đoạn văn hay tiêu đề. */
function currentIndent(attributes: Record<string, unknown>[]): number {
  for (const attrs of attributes) {
    const value = Number(attrs.indent)
    if (Number.isFinite(value) && value > 0) return value
  }
  return 0
}

/**
 * GIÃN DÒNG và THỤT LỀ cho đoạn văn / tiêu đề.
 *
 * Tiptap không có sẵn hai thứ này, mà văn bản hành chính thì gần như bắt buộc:
 * công văn thường quy định giãn dòng 1,5 và đoạn nào cũng lùi đầu dòng. Cài
 * bằng "global attribute" chứ không tạo node mới để mọi đoạn văn cũ vẫn dùng
 * được, chỉ thêm `style` khi người dùng thực sự đặt.
 */
export const ParagraphFormat = Extension.create({
  name: 'paragraphFormat',

  addGlobalAttributes() {
    return [
      {
        types: TYPES,
        attributes: {
          lineHeight: {
            default: null,
            parseHTML: (element) => element.style.lineHeight || null,
            renderHTML: (attributes) =>
              attributes.lineHeight ? { style: `line-height: ${attributes.lineHeight}` } : {},
          },
          spaceBefore: {
            default: null,
            parseHTML: (element) => element.style.marginTop || null,
            renderHTML: (attributes) =>
              attributes.spaceBefore ? { style: `margin-top: ${attributes.spaceBefore}` } : {},
          },
          rightIndent: {
            default: 0,
            parseHTML: (element) => Number.parseInt(element.style.marginRight, 10) || 0,
            renderHTML: (attributes) =>
              attributes.rightIndent ? { style: `margin-right: ${attributes.rightIndent}px` } : {},
          },
          spaceAfter: {
            default: null,
            parseHTML: (element) => element.style.marginBottom || null,
            renderHTML: (attributes) =>
              attributes.spaceAfter ? { style: `margin-bottom: ${attributes.spaceAfter}` } : {},
          },
          indent: {
            default: 0,
            parseHTML: (element) => Number.parseInt(element.style.marginLeft, 10) || 0,
            renderHTML: (attributes) =>
              attributes.indent ? { style: `margin-left: ${attributes.indent}px` } : {},
          },
          textIndent: {
            default: 0,
            parseHTML: (element) => Number.parseInt(element.style.textIndent, 10) || 0,
            renderHTML: (attributes) =>
              attributes.textIndent ? { style: `text-indent: ${attributes.textIndent}px` } : {},
          },
          backgroundColor: {
            default: null,
            parseHTML: (element) => element.style.backgroundColor || null,
            renderHTML: (attributes) =>
              attributes.backgroundColor
                ? { style: `background-color: ${attributes.backgroundColor}` }
                : {},
          },
        },
      },
    ]
  },

  addCommands() {
    // Mọi lệnh đều áp cho CẢ hai loại khối: chỗ con trỏ đang đứng chỉ là một
    // trong hai, gọi nhầm loại kia thì lệnh không làm gì chứ không lỗi.
    return {
      setLineHeight:
        (value) =>
        ({ commands }) =>
          TYPES.every((type) => commands.updateAttributes(type, { lineHeight: value })),

      indent:
        () =>
        ({ editor, commands }) => {
          const next = Math.min(
            currentIndent([editor.getAttributes('paragraph'), editor.getAttributes('heading')]) +
              INDENT_STEP,
            MAX_INDENT,
          )
          return TYPES.every((type) => commands.updateAttributes(type, { indent: next }))
        },

      outdent:
        () =>
        ({ editor, commands }) => {
          const next = Math.max(
            currentIndent([editor.getAttributes('paragraph'), editor.getAttributes('heading')]) -
              INDENT_STEP,
            0,
          )
          return TYPES.every((type) => commands.updateAttributes(type, { indent: next }))
        },
    }
  },
})
