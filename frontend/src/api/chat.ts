import type { Conversation } from "./conversations";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const TOKEN_KEY = "enterprise_rag_token";

export interface ChatSource {
  id: number;
  document_id: number;
  filename: string;
  chunk_index: number;
  distance: number;
}

export interface ChatStreamEvent {
  type:
  | "token"
  | "sources"
  | "conversation"
  | "complete"
  | "error";

  content?: string;

  sources?: ChatSource[];

  conversation?: Conversation;
}

interface StreamChatOptions {
  question: string;
  documentId: number | null;
  conversationId?: number | null;

  signal?: AbortSignal;

  onToken: (token: string) => void;

  onSources: (
    sources: ChatSource[],
  ) => void;

  onConversation: (
    conversation: Conversation,
  ) => void;

  onComplete?: () => void;
}

export async function streamChat({
  question,
  documentId,
  conversationId = null,
  signal,
  onToken,
  onSources,
  onConversation,
  onComplete,
}: StreamChatOptions): Promise<void> {
  const token =
    localStorage.getItem(TOKEN_KEY);

  if (!token) {
    throw new Error(
      "You are not authenticated.",
    );
  }

  const response = await fetch(
    `${API_URL}/chat/stream`,
    {
      method: "POST",

      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },

      body: JSON.stringify({
        question,
        document_id: documentId,
        conversation_id: conversationId,
      }),

      signal,
    },
  );

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}`;

    try {
      const data =
        await response.json();

      if (
        typeof data.detail ===
        "string"
      ) {
        message = data.detail;
      }
    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  if (!response.body) {
    throw new Error(
      "The server did not return a streaming response.",
    );
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let buffer = "";

  while (true) {
    const {
      value,
      done,
    } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(
      value,
      {
        stream: true,
      },
    );

    const events =
      buffer.split("\n\n");

    buffer =
      events.pop() ?? "";

    for (const event of events) {
      const line = event
        .split("\n")
        .find((line) =>
          line.startsWith(
            "data: ",
          ),
        );

      if (!line) {
        continue;
      }

      const json =
        line.slice(6);

      try {
        const parsed =
          JSON.parse(
            json,
          ) as ChatStreamEvent;

        /*
         * Streaming token.
         */
        if (
          parsed.type ===
          "token"
        ) {
          onToken(
            parsed.content ?? "",
          );
        }

        /*
         * Sources sent after
         * the answer.
         */
        if (
          parsed.type ===
          "sources"
        ) {
          onSources(
            parsed.sources ?? [],
          );
        }

        /*
         * Conversation created
         * or updated.
         */
        if (
          parsed.type ===
          "conversation"
        ) {
          if (
            parsed.conversation
          ) {
            onConversation(
              parsed.conversation,
            );
          }
        }
        /*
 * Backend has finished generating
 * and has saved the assistant message.
 */
        if (
          parsed.type ===
          "complete"
        ) {
          onComplete?.();
        }

        /*
         * Backend error.
         */
        if (
          parsed.type ===
          "error"
        ) {
          throw new Error(
            parsed.content ??
            "An error occurred while generating the answer.",
          );
        }
      } catch (error) {
        if (
          error instanceof
          SyntaxError
        ) {
          console.warn(
            "Could not parse SSE event:",
            json,
          );
        } else {
          throw error;
        }
      }
    }
  }
}