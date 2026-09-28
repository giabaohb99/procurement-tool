import { describe, expect, it } from 'vitest'

import {
  describeAttachmentsForPrint,
  isPrintableImage,
  splitPrintableAttachments,
} from './leave-print-attachments'

const file = (filename: string, content_type = '') => ({ filename, content_type })

describe('isPrintableImage', () => {
  it('accepts raster images the view endpoint can serve', () => {
    expect(isPrintableImage(file('a.jpg', 'image/jpeg'))).toBe(true)
    expect(isPrintableImage(file('a.png', 'image/png'))).toBe(true)
    expect(isPrintableImage(file('a.webp', 'IMAGE/WEBP'))).toBe(true)
    expect(isPrintableImage(file('a.png', 'image/png; charset=binary'))).toBe(true)
  })

  it('rejects svg even though it is an image, because /view answers 415 for it', () => {
    //  Xếp SVG vào nhóm ảnh thì trang in chờ một ảnh không bao giờ về.
    expect(isPrintableImage(file('logo.svg', 'image/svg+xml'))).toBe(false)
    expect(isPrintableImage(file('photo.heic', 'image/heic'))).toBe(false)
  })

  it('trusts content type over a misleading file extension', () => {
    expect(isPrintableImage(file('giay-kham.jpg', 'application/pdf'))).toBe(false)
    expect(isPrintableImage(file('scan.pdf', 'image/png'))).toBe(true)
  })

  it('falls back to the extension only when content type is empty', () => {
    expect(isPrintableImage(file('ANH.JPEG'))).toBe(true)
    expect(isPrintableImage(file('giay.pdf'))).toBe(false)
    expect(isPrintableImage(file(''))).toBe(false)
    expect(isPrintableImage(file('jpg'))).toBe(false)
  })
})

describe('describeAttachmentsForPrint', () => {
  it('is empty when there is nothing attached, so the sheet prints no dangling label', () => {
    expect(describeAttachmentsForPrint([], [])).toBe('')
  })

  it('names non-image files and only counts images', () => {
    expect(
      describeAttachmentsForPrint(
        [file('IMG_1.jpg'), file('IMG_2.jpg')],
        [file('giay-ra-vien.pdf'), file('ke-hoach.docx')],
      ),
    ).toBe('giay-ra-vien.pdf, ke-hoach.docx; 2 ảnh in kèm ở các trang sau')
  })

  it('handles a single group on either side', () => {
    expect(describeAttachmentsForPrint([file('a.png')], [])).toBe('1 ảnh in kèm ở các trang sau')
    expect(describeAttachmentsForPrint([], [file('a.pdf')])).toBe('a.pdf')
  })
})

describe('splitPrintableAttachments', () => {
  it('keeps upload order inside each group', () => {
    const list = [
      file('1.jpg', 'image/jpeg'),
      file('2.pdf', 'application/pdf'),
      file('3.png', 'image/png'),
      file('4.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    ]
    const { images, others } = splitPrintableAttachments(list)
    expect(images.map((f) => f.filename)).toEqual(['1.jpg', '3.png'])
    expect(others.map((f) => f.filename)).toEqual(['2.pdf', '4.docx'])
  })

  it('returns two empty groups for null, undefined and empty input', () => {
    for (const input of [null, undefined, []]) {
      expect(splitPrintableAttachments(input)).toEqual({ images: [], others: [] })
    }
  })
})
