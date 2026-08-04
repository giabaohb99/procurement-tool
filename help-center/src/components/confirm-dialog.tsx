import { useEffect, useState } from 'react'

import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

// Hộp thoại xác nhận / nhập một dòng dùng chung (singleton, promise-based) —
// thay confirm()/prompt() của trình duyệt. Gắn <ConfirmHost /> một lần ở main.tsx.

type Req = {
  id: number
  title: string
  message: string
  confirmText: string
  cancelText: string
  danger: boolean
  withInput: boolean
  placeholder: string
  defaultValue: string
  required: boolean
  resolve: (v: boolean | string) => void
}

let current: Req | null = null
let seq = 1
const listeners = new Set<(x: Req | null) => void>()
const emit = () => listeners.forEach((l) => l(current))

/** Xác nhận Yes/No → Promise<boolean>. */
export function askConfirm(opts: {
  title?: string; message: string; confirmText?: string; cancelText?: string; danger?: boolean
}): Promise<boolean> {
  return new Promise((resolve) => {
    current = {
      id: seq++, title: opts.title || 'Xác nhận', message: opts.message,
      confirmText: opts.confirmText || 'Đồng ý', cancelText: opts.cancelText || 'Hủy',
      danger: opts.danger ?? true, withInput: false, placeholder: '',
      defaultValue: '', required: false, resolve: (v) => resolve(v === true),
    }
    emit()
  })
}

/** Nhập 1 dòng → Promise<string|null> (null = bấm Hủy). */
export function askPrompt(opts: {
  title?: string; message: string; placeholder?: string
  defaultValue?: string; confirmText?: string; required?: boolean
}): Promise<string | null> {
  return new Promise((resolve) => {
    current = {
      id: seq++, title: opts.title || 'Nhập thông tin', message: opts.message,
      confirmText: opts.confirmText || 'Xác nhận', cancelText: 'Hủy',
      danger: false, withInput: true, placeholder: opts.placeholder || '',
      defaultValue: opts.defaultValue || '', required: opts.required ?? false,
      resolve: (v) => resolve(v === false ? null : (v as string)),
    }
    emit()
  })
}

export function ConfirmHost() {
  const [req, setReq] = useState<Req | null>(null)
  const [value, setValue] = useState('')

  useEffect(() => { listeners.add(setReq); return () => { listeners.delete(setReq) } }, [])
  useEffect(() => { if (req) setValue(req.defaultValue) }, [req?.id])

  const close = (result: boolean | string) => {
    const resolve = req!.resolve
    current = null
    emit()
    resolve(result)
  }

  if (!req) return null

  if (req.withInput) {
    return (
      <Dialog open onOpenChange={(open) => { if (!open) close(false) }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{req.title}</DialogTitle>
            <DialogDescription>{req.message}</DialogDescription>
          </DialogHeader>
          <Input
            autoFocus
            value={value}
            placeholder={req.placeholder}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (!req.required || value.trim())) close(value)
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => close(false)}>{req.cancelText}</Button>
            <Button disabled={req.required && !value.trim()} onClick={() => close(value)}>
              {req.confirmText}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <AlertDialog open onOpenChange={(open) => { if (!open) close(false) }}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{req.title}</AlertDialogTitle>
          <AlertDialogDescription className="whitespace-pre-line">{req.message}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => close(false)}>{req.cancelText}</AlertDialogCancel>
          <AlertDialogAction
            className={req.danger ? 'bg-destructive text-white hover:bg-destructive/90' : ''}
            onClick={() => close(true)}
          >
            {req.confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
