import { apiFetch } from "./client";


export interface Document {
  id: number;
  filename: string;
  content_type: string;
  status: string;
  source_url: string | null;
  processing_error: string | null;
  collection_id: number | null;
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
  collectionId: number | null = null,
): Promise<Document> {
  const formData = new FormData();

  formData.append(
    "file",
    file,
  );

  if (collectionId !== null) {
    formData.append(
      "collection_id",
      String(collectionId),
    );
  }

  const response = await apiFetch(
    "/documents/upload",
    {
      method: "POST",
      body: formData,
    },
  );

  return response.json();
}


export async function addWebsite(
  url: string,
  collectionId: number | null = null,
): Promise<Document> {
  const query =
    collectionId === null
      ? ""
      : `?collection_id=${collectionId}`;

  const response = await apiFetch(
    `/documents/url${query}`,
    {
      method: "POST",
      body: JSON.stringify({
        url,
      }),
    },
  );

  return response.json();
}


export async function retryDocumentProcessing(
  documentId: number,
): Promise<Document> {
  const response = await apiFetch(
    `/documents/${documentId}/retry`,
    {
      method: "POST",
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


export async function assignDocumentToCollection(
  documentId: number,
  collectionId: number,
): Promise<Document> {
  const response = await apiFetch(
    `/documents/${documentId}/collection`,
    {
      method: "PATCH",
      body: JSON.stringify({
        collection_id: collectionId,
      }),
    },
  );

  return response.json();
}


export async function removeDocumentFromCollection(
  documentId: number,
): Promise<Document> {
  const response = await apiFetch(
    `/documents/${documentId}/collection`,
    {
      method: "PATCH",
      body: JSON.stringify({
        collection_id: null,
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