import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getDocuments,
  uploadDocument,
  renameDocument,
  deleteDocument,
  type Document,
} from "../api/documents";  

import {
  deleteConversation,
  renameConversation,
  type Conversation,
} from "../api/conversations";

interface SidebarProps {
  selectedDocumentId: number | null;
  selectedConversationId: number | null;

  onSelectDocument: (
    documentId: number | null,
  ) => void;

  onSelectConversation: (
    conversationId: number | null,
  ) => void;

  onNewChat: () => void;

  conversations: Conversation[];

  loadingConversations: boolean;

  onConversationDeleted: (
    conversationId: number,
  ) => void;

  onConversationUpdated?: (
    conversation: Conversation,
  ) => void;
}

export default function Sidebar({
  selectedDocumentId,
  selectedConversationId,
  onSelectDocument,
  onSelectConversation,
  onNewChat,
  conversations,
  loadingConversations,
  onConversationDeleted,
  onConversationUpdated,
}: SidebarProps) {
  const [documents, setDocuments] =
    useState<Document[]>([]);

  const [documentsLoading, setDocumentsLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [uploading, setUploading] =
    useState(false);

  const [uploadError, setUploadError] =
    useState("");

  const [
  conversationSearch,
  setConversationSearch,
] = useState("");

  const [
    deletingConversationId,
    setDeletingConversationId,
  ] = useState<number | null>(null);

  const [
    renamingConversationId,
    setRenamingConversationId,
  ] = useState<number | null>(null);

  const [
    conversationRenameValue,
    setConversationRenameValue,
  ] = useState("");


  const [
    deletingDocumentId,
    setDeletingDocumentId,
  ] = useState<number | null>(null);

  const [
    renamingDocumentId,
    setRenamingDocumentId,
  ] = useState<number | null>(null);

  const [
    documentRenameValue,
    setDocumentRenameValue,
  ] = useState("");

  const [
    openConversationMenuId,
    setOpenConversationMenuId,
  ] = useState<number | null>(null);

  const [
    openDocumentMenuId,
    setOpenDocumentMenuId,
  ] = useState<number | null>(null);

  const sidebarRef =
    useRef<HTMLElement | null>(null);

  /*
   * Load documents.
   */
  useEffect(() => {
    async function loadDocuments() {
      try {
        setDocumentsLoading(true);
        setError("");

        const data =
          await getDocuments();

        setDocuments(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load documents.",
        );
      } finally {
        setDocumentsLoading(false);
      }
    }

    loadDocuments();
  }, []);

  /*
   * Close menus when clicking outside
   * the sidebar menu area.
   */
  useEffect(() => {
    function handleClickOutside(
      event: MouseEvent,
    ) {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(
          event.target as Node,
        )
      ) {
        setOpenConversationMenuId(null);
        setOpenDocumentMenuId(null);
      }
    }

    document.addEventListener(
      "mousedown",
      handleClickOutside,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside,
      );
    };
  }, []);

  /*
   * Upload document.
   */
  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    try {
      setUploading(true);
      setUploadError("");
      setError("");

      const uploadedDocument =
        await uploadDocument(file);

      setDocuments((previous) => [
        uploadedDocument,
        ...previous,
      ]);

      onSelectDocument(
        uploadedDocument.id,
      );

      onSelectConversation(null);

      event.target.value = "";
    } catch (err) {
      setUploadError(
        err instanceof Error
          ? err.message
          : "Failed to upload document.",
      );
    } finally {
      setUploading(false);
    }
  }

  /*
   * Delete conversation.
   */
  async function handleDeleteConversation(
    event: React.MouseEvent,
    conversationId: number,
  ) {
    event.stopPropagation();

    const confirmed =
      window.confirm(
        "Delete this conversation?",
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingConversationId(
        conversationId,
      );

      await deleteConversation(
        conversationId,
      );

      setOpenConversationMenuId(null);

      onConversationDeleted(
        conversationId,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete conversation.",
      );
    } finally {
      setDeletingConversationId(null);
    }
  }

  /*
   * Start conversation rename.
   */
  function startRenameConversation(
    conversation: Conversation,
  ) {
    setOpenConversationMenuId(null);

    setRenamingConversationId(
      conversation.id,
    );

    setConversationRenameValue(
      conversation.title,
    );
  }

  /*
   * Cancel conversation rename.
   */
  function cancelRenameConversation() {
    setRenamingConversationId(null);
    setConversationRenameValue("");
  }

  /*
   * Save conversation rename.
   */
  async function handleRenameConversation(
    conversation: Conversation,
  ) {
    const title =
      conversationRenameValue.trim();

    if (!title) {
      return;
    }

    if (
      title === conversation.title
    ) {
      cancelRenameConversation();
      return;
    }

    try {
      const updated =
        await renameConversation(
          conversation.id,
          title,
        );

      cancelRenameConversation();

      onConversationUpdated?.(
        updated,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to rename conversation.",
      );
    }
  }

  /*
   * Delete document.
   */
  async function handleDeleteDocument(
    event: React.MouseEvent,
    documentId: number,
  ) {
    event.stopPropagation();

    const confirmed =
      window.confirm(
        "Delete this document? This cannot be undone.",
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingDocumentId(
        documentId,
      );

      await deleteDocument(
        documentId,
      );

      setDocuments((previous) =>
        previous.filter(
          (document) =>
            document.id !== documentId,
        ),
      );

      setOpenDocumentMenuId(null);

      if (
        selectedDocumentId ===
        documentId
      ) {
        onSelectDocument(null);
        onSelectConversation(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete document.",
      );
    } finally {
      setDeletingDocumentId(null);
    }
  }

  /*
   * Start document rename.
   */
  function startRenameDocument(
    document: Document,
  ) {
    setOpenDocumentMenuId(null);

    setRenamingDocumentId(
      document.id,
    );

    setDocumentRenameValue(
      document.filename,
    );
  }

  /*
   * Cancel document rename.
   */
  function cancelRenameDocument() {
    setRenamingDocumentId(null);
    setDocumentRenameValue("");
  }

  /*
   * Save document rename.
   */
  async function handleRenameDocument(
    document: Document,
  ) {
    const filename =
      documentRenameValue.trim();

    if (!filename) {
      return;
    }

    if (
      filename === document.filename
    ) {
      cancelRenameDocument();
      return;
    }

    try {
      const updated =
        await renameDocument(
          document.id,
          filename,
        );

      setDocuments((previous) =>
        previous.map((item) =>
          item.id === updated.id
            ? updated
            : item,
        ),
      );

      cancelRenameDocument();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to rename document.",
      );
    }
  }

  return (
    <aside
      ref={sidebarRef}
      className="sidebar"
    >
      {/* ================================================= */}
      {/* Conversations */}
      {/* ================================================= */}

      <section className="sidebar-section">
        <div className="sidebar-section-header">
          <h3>
            Conversations
          </h3>

          <button
            type="button"
            className="new-chat-button"
            onClick={onNewChat}
          >
            + New Chat
          </button>
        </div>
        <input
  type="text"
  className="conversation-search"
  placeholder="Search conversations..."
  value={conversationSearch}
  onChange={(event) =>
    setConversationSearch(
      event.target.value,
    )
  }
/>

        <div className="conversation-list">
          {loadingConversations && (
            <p className="sidebar-status">
              Loading conversations...
            </p>
          )}

          {!loadingConversations &&
            conversations.length === 0 && (
              <p className="sidebar-status">
                No conversations yet.
              </p>
            )}

          {!loadingConversations &&
  conversations
    .filter((conversation) =>
      conversation.title
        .toLowerCase()
        .includes(
          conversationSearch
            .trim()
            .toLowerCase(),
        ),
    )
    .map(
      (conversation) => (
                <div
                  key={conversation.id}
                  className={`conversation-row ${
                    selectedConversationId ===
                    conversation.id
                      ? "selected"
                      : ""
                  }`}
                >
                  {renamingConversationId ===
                  conversation.id ? (
                    <input
                      autoFocus
                      type="text"
                      className="sidebar-rename-input"
                      value={
                        conversationRenameValue
                      }
                      onChange={(event) =>
                        setConversationRenameValue(
                          event.target.value,
                        )
                      }
                      onKeyDown={(event) => {
                        if (
                          event.key ===
                          "Enter"
                        ) {
                          void handleRenameConversation(
                            conversation,
                          );
                        }

                        if (
                          event.key ===
                          "Escape"
                        ) {
                          cancelRenameConversation();
                        }
                      }}
                      onBlur={() => {
                        void handleRenameConversation(
                          conversation,
                        );
                      }}
                    />
                  ) : (
                    <>
                      <button
                        type="button"
                        className="conversation-item"
                        onClick={() =>
                          onSelectConversation(
                            conversation.id,
                          )
                        }
                      >
                        <span className="conversation-title">
                          {conversation.title}
                        </span>
                      </button>

                      <div className="sidebar-menu-wrapper">
                        <button
                          type="button"
                          className="sidebar-menu-button"
                          aria-label="Conversation options"
                          title="Conversation options"
                          onClick={(
                            event,
                          ) => {
                            event.stopPropagation();

                            setOpenConversationMenuId(
                              (previous) =>
                                previous ===
                                conversation.id
                                  ? null
                                  : conversation.id,
                            );

                            setOpenDocumentMenuId(
                              null,
                            );
                          }}
                        >
                          ⋮
                        </button>

                        {openConversationMenuId ===
                          conversation.id && (
                          <div className="sidebar-menu">
                            <button
                              type="button"
                              onClick={() =>
                                startRenameConversation(
                                  conversation,
                                )
                              }
                            >
                              Rename
                            </button>

                            <button
                              type="button"
                              className="danger"
                              disabled={
                                deletingConversationId ===
                                conversation.id
                              }
                              onClick={(
                                event,
                              ) =>
                                void handleDeleteConversation(
                                  event,
                                  conversation.id,
                                )
                              }
                            >
                              {deletingConversationId ===
                              conversation.id
                                ? "Deleting..."
                                : "Delete"}
                            </button>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ),
            )}
        </div>
      </section>

      {/* ================================================= */}
      {/* Documents */}
      {/* ================================================= */}

      <section className="sidebar-section documents-section">
        <div className="sidebar-section-header">
          <h3>
            Documents
          </h3>

          <label
            className={`upload-button ${
              uploading
                ? "uploading"
                : ""
            }`}
          >
            {uploading
              ? "Uploading..."
              : "+ Upload"}

            <input
              type="file"
              accept=".pdf,.docx,.md,.markdown"
              onChange={
                handleUpload
              }
              disabled={uploading}
              hidden
            />
          </label>
        </div>

        {uploadError && (
          <p className="upload-error">
            {uploadError}
          </p>
        )}

        <div className="document-list">
          {/* All Documents */}

          <button
            type="button"
            className={`document-item ${
              selectedDocumentId === null
                ? "selected"
                : ""
            }`}
            onClick={() => {
              onSelectDocument(null);
              onSelectConversation(null);
            }}
          >
            <span>
              🔍 All Documents
            </span>
          </button>

          {documentsLoading && (
            <p className="sidebar-status">
              Loading documents...
            </p>
          )}

          {error && (
            <p className="sidebar-error">
              {error}
            </p>
          )}

          {!documentsLoading &&
            !error &&
            documents.length === 0 && (
              <p className="sidebar-status">
                No documents uploaded.
              </p>
            )}

          {!documentsLoading &&
            !error &&
            documents.map(
              (document) => (
                <div
                  key={document.id}
                  className={`document-row ${
                    selectedDocumentId ===
                    document.id
                      ? "selected"
                      : ""
                  }`}
                >
                  {renamingDocumentId ===
                  document.id ? (
                    <input
                      autoFocus
                      type="text"
                      className="sidebar-rename-input"
                      value={
                        documentRenameValue
                      }
                      onChange={(event) =>
                        setDocumentRenameValue(
                          event.target.value,
                        )
                      }
                      onKeyDown={(event) => {
                        if (
                          event.key ===
                          "Enter"
                        ) {
                          void handleRenameDocument(
                            document,
                          );
                        }

                        if (
                          event.key ===
                          "Escape"
                        ) {
                          cancelRenameDocument();
                        }
                      }}
                      onBlur={() => {
                        void handleRenameDocument(
                          document,
                        );
                      }}
                    />
                  ) : (
                    <>
                      <button
                        type="button"
                        className="document-item"
                        onClick={() => {
                          onSelectDocument(
                            document.id,
                          );

                          onSelectConversation(
                            null,
                          );
                        }}
                      >
                        <span className="document-name">
                          📄{" "}
                          {document.filename}
                        </span>
                      </button>

                      <div className="sidebar-menu-wrapper">
                        <button
                          type="button"
                          className="sidebar-menu-button"
                          aria-label="Document options"
                          title="Document options"
                          onClick={(
                            event,
                          ) => {
                            event.stopPropagation();

                            setOpenDocumentMenuId(
                              (previous) =>
                                previous ===
                                document.id
                                  ? null
                                  : document.id,
                            );

                            setOpenConversationMenuId(
                              null,
                            );
                          }}
                        >
                          ⋮
                        </button>

                        {openDocumentMenuId ===
                          document.id && (
                          <div className="sidebar-menu">
                            <button
                              type="button"
                              onClick={() =>
                                startRenameDocument(
                                  document,
                                )
                              }
                            >
                              Rename
                            </button>

                            <button
                              type="button"
                              className="danger"
                              disabled={
                                deletingDocumentId ===
                                document.id
                              }
                              onClick={(
                                event,
                              ) =>
                                void handleDeleteDocument(
                                  event,
                                  document.id,
                                )
                              }
                            >
                              {deletingDocumentId ===
                              document.id
                                ? "Deleting..."
                                : "Delete"}
                            </button>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ),
            )}
        </div>
      </section>
    </aside>
  );
}