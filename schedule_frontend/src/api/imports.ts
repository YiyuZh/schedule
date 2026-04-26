import { del, get, post } from '@/api/client'
import type {
  CourseImportPayload,
  CourseImportResult,
  CourseImportValidateResult,
  ImportBatch,
} from '@/types/course'

export async function fetchImportBatches(): Promise<ImportBatch[]> {
  const data = await get<{ items: ImportBatch[] }>('/api/import-batches')
  return data.items
}

export function fetchImportBatch(batchId: number): Promise<ImportBatch> {
  return get<ImportBatch>(`/api/import-batches/${batchId}`)
}

export function validateCourseImport(payload: CourseImportPayload): Promise<CourseImportValidateResult> {
  return post<CourseImportValidateResult>('/api/import/courses/validate', { body: payload })
}

export function importCourses(payload: CourseImportPayload): Promise<CourseImportResult> {
  return post<CourseImportResult>('/api/import/courses/json', { body: payload })
}

export function deleteImportBatchCourses(batchId: number): Promise<{ batch_id: number; deleted_count: number }> {
  return del<{ batch_id: number; deleted_count: number }>(`/api/import-batches/${batchId}/courses`)
}
