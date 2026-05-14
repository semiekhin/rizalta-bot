import { useEffect } from 'react'

// Modal: flex column with sticky header + scrollable body + sticky footer.
// Mobile: bottom-padding (pb-16) reserves space for the bottom navigation bar
// (~64px), so the footer with action buttons isn't covered by it.
// handle: when true, renders a thin drag-handle bar at the top (mobile only).
export default function Modal({ title, onClose, children, footer, handle = false }) {
  useEffect(() => {
    const onEsc = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onEsc)
    return () => window.removeEventListener('keydown', onEsc)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 pb-16 sm:pb-4"
      onClick={onClose}
    >
      <div
        className="bg-rz-green border border-rz-green-light rounded-2xl sm:rounded-xl w-full sm:max-w-lg max-h-[calc(100vh-80px)] sm:max-h-[92vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {handle && (
          <div className="sm:hidden pt-2">
            <div className="w-9 h-1 bg-rz-cream-muted/40 rounded-full mx-auto mb-3" />
          </div>
        )}
        <div className="bg-rz-green border-b border-rz-green-light rounded-t-2xl sm:rounded-t-xl px-4 py-3 flex items-center justify-between">
          <h2 className="text-rz-gold font-semibold">{title}</h2>
          <button onClick={onClose} className="text-rz-cream-dark text-xl leading-none">×</button>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4">{children}</div>
        {footer && (
          <div className="border-t border-rz-green-light px-4 py-3 flex gap-2 items-center bg-rz-green rounded-b-2xl sm:rounded-b-xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
