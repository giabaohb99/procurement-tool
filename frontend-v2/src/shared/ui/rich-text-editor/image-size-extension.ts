import { mergeAttributes, ResizableNodeView, type Editor } from '@tiptap/core'
import { Image } from '@tiptap/extension-image'
import type { Node as ProseMirrorNode } from '@tiptap/pm/model'
import { Plugin } from '@tiptap/pm/state'
import { toast } from 'sonner'

import { clipboardHasSpreadsheetTable } from './spreadsheet-clipboard'

const MAX_PASTED_IMAGE_SIZE = 1024 * 1024
const MAX_EDITOR_IMAGE_WIDTH = 642

function imageElement(element: HTMLElement): HTMLElement | null {
  return element.tagName === 'IMG' ? element : element.querySelector('img')
}

function imageAttribute(name: string) {
  return (element: HTMLElement) => imageElement(element)?.getAttribute(name) || null
}

function imageDimension(name: 'width' | 'height') {
  return (element: HTMLElement) => {
    const value = Number.parseInt(imageElement(element)?.getAttribute(name) ?? '', 10)
    return Number.isFinite(value) && value > 0 ? value : null
  }
}

function readImage(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

/** Dùng chung cho Ctrl+V và lệnh Dán trong menu chuột phải. */
export async function insertImageBlobs(editor: Editor, images: Blob[]) {
  for (const image of images) {
    const name = image instanceof File ? image.name : ''
    if (image.size > MAX_PASTED_IMAGE_SIZE) {
      toast.error(`Ảnh “${name || 'đã dán'}” vượt quá 1MB`)
      continue
    }
    try {
      const src = await readImage(image)
      editor
        .chain()
        .focus()
        .setImage({ src, alt: name || undefined })
        .run()
    } catch {
      toast.error('Không đọc được ảnh từ khay nhớ tạm')
    }
  }
}

/**
 * Ảnh trong editor có ba trách nhiệm:
 *
 * - giữ width/height khi import Word/PDF hoặc khi lưu rồi mở lại;
 * - cho kéo bốn góc để resize, luôn khóa tỷ lệ để ảnh không bị méo;
 * - lưu caption trong chính node ảnh và render thành figure/figcaption chuẩn.
 *
 * Vẫn đọc được HTML cũ chỉ có `<img>`, nên tài liệu đã lưu trước tính năng này
 * không phải migrate.
 */
export const ImageWithSize = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      src: {
        default: null,
        parseHTML: imageAttribute('src'),
      },
      alt: {
        default: null,
        parseHTML: imageAttribute('alt'),
      },
      title: {
        default: null,
        parseHTML: imageAttribute('title'),
      },
      width: {
        default: null,
        parseHTML: imageDimension('width'),
      },
      height: {
        default: null,
        parseHTML: imageDimension('height'),
      },
      caption: {
        default: '',
        parseHTML: (element) =>
          element.tagName === 'FIGURE'
            ? (element.querySelector('figcaption')?.textContent?.trim() ?? '')
            : '',
        renderHTML: () => ({}),
      },
    }
  },

  parseHTML() {
    const imageSelector = this.options.allowBase64 ? 'img[src]' : 'img[src]:not([src^="data:"])'
    return [
      {
        tag: 'figure',
        getAttrs: (element) => (element.querySelector(imageSelector) ? {} : false),
      },
      { tag: imageSelector },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const { caption: _caption, ...imageAttributes } = HTMLAttributes
    return [
      'figure',
      { 'data-editor-image': '' },
      ['img', mergeAttributes(this.options.HTMLAttributes, imageAttributes)],
      ['figcaption', {}, String(node.attrs.caption || '')],
    ]
  },

  addNodeView() {
    return ({ node, getPos, editor }) => {
      const image = document.createElement('img')
      image.draggable = false
      const caption = document.createElement('textarea')
      caption.rows = 1
      caption.placeholder = 'Thêm chú thích ảnh…'
      caption.className = 'editor-image-caption'
      caption.setAttribute('aria-label', 'Chú thích ảnh')
      caption.contentEditable = 'false'

      const syncCaptionHeight = () => {
        caption.style.height = 'auto'
        caption.style.height = `${caption.scrollHeight}px`
      }

      const syncImage = (currentNode: ProseMirrorNode) => {
        const { src, alt, title, width, height } = currentNode.attrs
        if (src) image.setAttribute('src', String(src))
        else image.removeAttribute('src')
        if (alt) image.setAttribute('alt', String(alt))
        else image.removeAttribute('alt')
        if (title) image.setAttribute('title', String(title))
        else image.removeAttribute('title')
        image.style.width = width ? `${width}px` : ''
        image.style.height = height ? `${height}px` : ''
        caption.value = String(currentNode.attrs.caption || '')
        caption.readOnly = !editor.isEditable
        caption.hidden = !editor.isEditable && !caption.value
        requestAnimationFrame(syncCaptionHeight)
      }

      syncImage(node)

      const updateNodeAttributes = (attributes: Record<string, unknown>) => {
        const position = getPos()
        if (position === undefined) return
        const currentNode = editor.state.doc.nodeAt(position)
        if (!currentNode || currentNode.type.name !== 'image') return
        const transaction = editor.state.tr.setNodeMarkup(position, undefined, {
          ...currentNode.attrs,
          ...attributes,
        })
        editor.view.dispatch(transaction)
      }

      const resizable = new ResizableNodeView({
        element: image,
        editor,
        node,
        getPos,
        onResize: (width, height) => {
          image.style.width = `${width}px`
          image.style.height = `${height}px`
        },
        onCommit: (width, height) => {
          updateNodeAttributes({ width: Math.round(width), height: Math.round(height) })
        },
        onUpdate: (updatedNode) => {
          if (updatedNode.type.name !== 'image') return false
          syncImage(updatedNode)
          return true
        },
        options: {
          directions: editor.isEditable
            ? ['top-left', 'top-right', 'bottom-left', 'bottom-right']
            : [],
          min: { width: 48, height: 24 },
          max: { width: MAX_EDITOR_IMAGE_WIDTH },
          preserveAspectRatio: true,
          className: {
            container: 'editor-image-node',
            wrapper: 'editor-image-resize-wrapper',
            handle: 'editor-image-resize-handle',
            resizing: 'is-resizing',
          },
        },
      })
      resizable.container.appendChild(caption)

      const handleCaptionInput = () => {
        syncCaptionHeight()
        updateNodeAttributes({ caption: caption.value })
      }
      caption.addEventListener('input', handleCaptionInput)

      return {
        dom: resizable.dom,
        update: resizable.update.bind(resizable),
        selectNode: () => resizable.container.classList.add('is-selected'),
        deselectNode: () => resizable.container.classList.remove('is-selected'),
        stopEvent: (event) => event.target === caption,
        ignoreMutation: (mutation) => mutation.target === caption,
        destroy: () => {
          caption.removeEventListener('input', handleCaptionInput)
          resizable.destroy()
        },
      }
    }
  },

  addProseMirrorPlugins() {
    const editor = this.editor
    return [
      new Plugin({
        props: {
          handlePaste: (_view, event) => {
            // Excel chép một vùng ô thường đính kèm cả ẢNH XEM TRƯỚC. Bảng HTML
            // hoặc TSV phải thắng file ảnh, nếu không vùng Excel bị dán thành
            // hình và không còn sửa từng ô được.
            if (clipboardHasSpreadsheetTable(event.clipboardData)) return false

            const images = Array.from(event.clipboardData?.files ?? []).filter((file) =>
              file.type.startsWith('image/'),
            )
            if (!images.length) return false
            event.preventDefault()

            void insertImageBlobs(editor, images)
            return true
          },
        },
      }),
    ]
  },
})
