import { Editor } from '@tiptap/core'
import { TextAlign } from '@tiptap/extension-text-align'
import { TextStyleKit } from '@tiptap/extension-text-style'
import StarterKit from '@tiptap/starter-kit'
import { describe, expect, it } from 'vitest'

import { ImageWithSize } from './image-size-extension'
import { ImportTrace } from './import-trace-extension'
import { ParagraphFormat } from './paragraph-format-extension'

describe('định dạng nội dung nhập từ Word', () => {
  it('giữ định dạng đoạn, chữ, danh sách và kích thước ảnh sau khi Tiptap serialize', () => {
    const editor = new Editor({
      extensions: [
        StarterKit,
        TextStyleKit,
        TextAlign.configure({ types: ['heading', 'paragraph'] }),
        ParagraphFormat,
        ImageWithSize.configure({ inline: false, allowBase64: true }),
        ImportTrace,
      ],
      content: `
        <figure>
          <img src="data:image/png;base64,aW1hZ2U=" alt="Logo" width="199" height="48" data-import-id="trace-01" data-source-page="2">
          <figcaption>Logo công ty</figcaption>
        </figure>
        <p style="margin-top: 0px; margin-right: 10px; margin-bottom: 8px; margin-left: 30px; line-height: 1.5; text-indent: 12px; text-align: center; background-color: #fef3c7">
          <strong><span style="font-family: &quot;Calibri&quot;; font-size: 20pt; color: #00b0f0">TIÊU ĐỀ</span></strong>
        </p>
        <ul><li><p>Mục thứ nhất</p></li><li><p>Mục thứ hai</p></li></ul>
      `,
    })

    const root = document.createElement('div')
    root.innerHTML = editor.getHTML()
    const image = root.querySelector('img')
    const caption = root.querySelector('figcaption')
    const paragraph = root.querySelector('p')
    const text = root.querySelector<HTMLElement>('span')

    expect(image?.getAttribute('width')).toBe('199')
    expect(image?.getAttribute('height')).toBe('48')
    expect(image?.getAttribute('data-import-id')).toBe('trace-01')
    expect(image?.getAttribute('data-source-page')).toBe('2')
    expect(caption?.textContent).toBe('Logo công ty')
    expect(paragraph?.style.marginTop).toBe('0px')
    expect(paragraph?.style.marginBottom).toBe('8px')
    expect(paragraph?.style.lineHeight).toBe('1.5')
    expect(paragraph?.style.marginLeft).toBe('30px')
    expect(paragraph?.style.marginRight).toBe('10px')
    expect(paragraph?.style.textIndent).toBe('12px')
    expect(paragraph?.style.textAlign).toBe('center')
    expect(paragraph?.style.backgroundColor).toBe('rgb(254, 243, 199)')
    expect(text?.style.fontFamily).toContain('Calibri')
    expect(text?.style.fontSize).toBe('20pt')
    expect(text?.style.color).toBe('rgb(0, 176, 240)')
    expect(root.querySelectorAll('ul > li')).toHaveLength(2)

    const captionInput = editor.view.dom.querySelector<HTMLTextAreaElement>('.editor-image-caption')
    expect(captionInput?.value).toBe('Logo công ty')
    expect(editor.view.dom.querySelectorAll('[data-resize-handle]')).toHaveLength(4)
    if (captionInput) {
      captionInput.value = 'Chú thích đã sửa'
      captionInput.dispatchEvent(new Event('input', { bubbles: true }))
    }
    expect(editor.getHTML()).toContain('<figcaption>Chú thích đã sửa</figcaption>')

    const editorImage = editor.view.dom.querySelector<HTMLImageElement>('.editor-image-node img')
    const resizeHandle = editor.view.dom.querySelector<HTMLElement>(
      '[data-resize-handle="bottom-right"]',
    )
    if (editorImage && resizeHandle) {
      Object.defineProperty(editorImage, 'offsetWidth', {
        configurable: true,
        get: () => Number.parseFloat(editorImage.style.width) || 199,
      })
      Object.defineProperty(editorImage, 'offsetHeight', {
        configurable: true,
        get: () => Number.parseFloat(editorImage.style.height) || 48,
      })
      resizeHandle.dispatchEvent(
        new MouseEvent('mousedown', { bubbles: true, clientX: 100, clientY: 100 }),
      )
      document.dispatchEvent(new MouseEvent('mousemove', { clientX: 150, clientY: 120 }))
      document.dispatchEvent(new MouseEvent('mouseup'))
    }
    const resized = document.createElement('div')
    resized.innerHTML = editor.getHTML()
    expect(resized.querySelector('img')?.getAttribute('width')).toBe('249')
    expect(resized.querySelector('img')?.getAttribute('height')).toBe('60')

    editor.destroy()
  })

  it('đọc ảnh HTML cũ không có figure mà không mất dữ liệu', () => {
    const editor = new Editor({
      extensions: [StarterKit, ImageWithSize.configure({ allowBase64: true })],
      content: '<img src="https://example.com/anh.png" alt="Ảnh cũ" width="320" height="180">',
    })

    const html = editor.getHTML()
    expect(html).toContain('<figure')
    expect(html).toContain('src="https://example.com/anh.png"')
    expect(html).toContain('alt="Ảnh cũ"')
    expect(html).toContain('width="320"')
    expect(html).toContain('<figcaption></figcaption>')
    editor.destroy()
  })
})
