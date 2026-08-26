import { apiFetch } from "./client";


export interface Document {
  id: number;
  filename: string;
  content_type: string;
  status: string;
  created_at: string;
}


export async function getDocuments(): Promise<Document[]> {
  const response = await apiFetch(
    "/documents",
  );

  return response.json();
}


export async function uploadDocument(
  file: File,
): Promise<Document> {
  const formData = new FormData();

  formData.append(
    "file",
    file,
  );

  const response = await apiFetch(
    "/documents/upload",
    {
      method: "POST",
      body: formData,
    },
  );

  return response.json();
}


export async function renameDocument(
  documentId: number,
  filename: string,
): Promise<Document> {
  const response = await apiFetch(
    `/documents/${documentId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        filename,
      }),
    },
  );

  return response.json();
}


export async function deleteDocument(
  documentId: number,
): Promise<void> {
  await apiFetch(
    `/documents/${documentId}`,
    {
      method: "DELETE",
    },
  );
}