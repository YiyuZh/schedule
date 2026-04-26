export const PAGE_REFRESH_EVENT = 'schedule:refresh-current-page'
export const PAGE_EXPORT_EVENT = 'schedule:export-current-page'

type EventHandler = () => void | Promise<void>

function addWindowListener(eventName: string, handler: EventHandler): () => void {
  const listener = () => {
    void handler()
  }

  window.addEventListener(eventName, listener)
  return () => window.removeEventListener(eventName, listener)
}

export function emitPageRefresh(): void {
  window.dispatchEvent(new CustomEvent(PAGE_REFRESH_EVENT))
}

export function emitPageExport(): void {
  window.dispatchEvent(new CustomEvent(PAGE_EXPORT_EVENT))
}

export function listenPageRefresh(handler: EventHandler): () => void {
  return addWindowListener(PAGE_REFRESH_EVENT, handler)
}

export function listenPageExport(handler: EventHandler): () => void {
  return addWindowListener(PAGE_EXPORT_EVENT, handler)
}
