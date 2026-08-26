const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const TOKEN_KEY =
  "enterprise_rag_token";


export async function apiFetch(
  path: string,
  options: RequestInit = {},
) {
  const token =
    localStorage.getItem(TOKEN_KEY);

  const headers =
    new Headers(options.headers);

  /*
   * JSON requests need Content-Type.
   *
   * FormData requests must NOT have
   * Content-Type manually set because
   * the browser adds the multipart boundary.
   */
  if (!(options.body instanceof FormData)) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
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

  return response;
}