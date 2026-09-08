import { apiFetch } from "./client";

export interface Collection {
  id: number;
  name: string;
  created_at: string;
}

export async function getCollections(): Promise<Collection[]> {
  const response = await apiFetch("/collections");

  return response.json();
}

export async function createCollection(
  name: string,
): Promise<Collection> {
  const response = await apiFetch(
    "/collections",
    {
      method: "POST",
      body: JSON.stringify({
        name,
      }),
    },
  );

  return response.json();
}

export async function renameCollection(
  collectionId: number,
  name: string,
): Promise<Collection> {
  const response = await apiFetch(
    `/collections/${collectionId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        name,
      }),
    },
  );

  return response.json();
}

export async function deleteCollection(
  collectionId: number,
): Promise<void> {
  await apiFetch(
    `/collections/${collectionId}`,
    {
      method: "DELETE",
    },
  );
}
