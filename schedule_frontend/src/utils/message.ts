import { ElMessage, ElMessageBox } from 'element-plus'

export function notifySuccess(message: string): void {
  ElMessage.success(message)
}

export function notifyError(message: string): void {
  ElMessage.error(message)
}

export function notifyInfo(message: string): void {
  ElMessage.info(message)
}

export async function confirmAction(message: string, title = '确认操作'): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    return true
  } catch {
    return false
  }
}
