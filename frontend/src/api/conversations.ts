import { apiFetch } from "./client";

export interface Conversation {
  id: number;
  user_id: number;
  document_id: number | null;
  title: string;
  created_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationDetail
  extends Conversation {
  messages: Message[];
}


export async function getConversations(
  documentId: number | null,
): Promise<Conversation[]> {
  const params =
    documentId === null
      ? ""
      : `?document_id=${documentId}`;

  const response = await apiFetch(
    `/conversations${params}`,
  );

  return response.json();
}


export async function getConversation(
  conversationId: number,
): Promise<ConversationDetail> {
  const response = await apiFetch(
    `/conversations/${conversationId}`,
  );

  return response.json();
}


export async function createConversation(
  title: string,
  documentId: number | null,
): Promise<Conversation> {
  const response = await apiFetch(
    "/conversations",
    {
      method: "POST",
      body: JSON.stringify({
        title,
        document_id: documentId,
      }),
    },
  );

  return response.json();
}


export async function renameConversation(
  conversationId: number,
  title: string,
): Promise<Conversation> {
  const response = await apiFetch(
    `/conversations/${conversationId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        title,
      }),
    },
  );

  return response.json();
}


export async function deleteConversation(
  conversationId: number,
): Promise<void> {
  await apiFetch(
    `/conversations/${conversationId}`,
    {
      method: "DELETE",
    },
  );
}