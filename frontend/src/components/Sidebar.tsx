import { useEffect, useRef, useState } from "react";

import {
  getDocuments,
  uploadDocument,
  addWebsite,
  renameDocument,
  deleteDocument,
  assignDocumentToCollection,
  removeDocumentFromCollection,
  retryDocumentProcessing,
  type Document,
} from "../api/documents";

import {
  deleteConversation,
  renameConversation,
  type Conversation,
} from "../api/conversations";

import {
  createCollection,
  renameCollection,
  deleteCollection,
  type Collection,
} from "../api/collections";

interface SidebarProps {
  selectedDocumentId: number | null;

  selectedCollectionId: number | null;

  selectedConversationId: number | null;

  onSelectDocument: (documentId: number | null) => void;

  onSelectCollection: (collectionId: number | null) => void;

  onSelectConversation: (conversationId: number | null) => void;

  onNewChat: () => void;

  conversations: Conversation[];

  loadingConversations: boolean;

  collections: Collection[];

  onCollectionCreated: (collection: Collection) => void;

  onCollectionUpdated: (collection: Collection) => void;

  onCollectionDeleted: (collectionId: number) => void;

  onConversationDeleted: (conversationId: number) => void;

  onConversationUpdated?: (conversation: Conversation) => void;
}

export default function Sidebar({
  selectedDocumentId,
  selectedCollectionId,
  selectedConversationId,
  onSelectDocument,
  onSelectCollection,
  onSelectConversation,
  onNewChat,
  conversations,
  loadingConversations,
  collections,
  onCollectionCreated,
  onCollectionUpdated,
  onCollectionDeleted,
  onConversationDeleted,
  onConversationUpdated,
}: SidebarProps) {
  const [documents, setDocuments] = useState<Document[]>([]);

  const [documentsLoading, setDocumentsLoading] = useState(true);

  const [error, setError] = useState("");

  const [uploading, setUploading] = useState(false);

  const [addingWebsite, setAddingWebsite] = useState(false);

  const [addingWebsiteLoading, setAddingWebsiteLoading] = useState(false);

  const [websiteUrl, setWebsiteUrl] = useState("");

  const [websiteError, setWebsiteError] = useState("");

  const [uploadError, setUploadError] = useState("");

  const [conversationSearch, setConversationSearch] = useState("");

  const [deletingConversationId, setDeletingConversationId] = useState<
    number | null
  >(null);

  const [renamingConversationId, setRenamingConversationId] = useState<
    number | null
  >(null);

  const [conversationRenameValue, setConversationRenameValue] = useState("");

  const [deletingDocumentId, setDeletingDocumentId] = useState<number | null>(
    null,
  );

  const [renamingDocumentId, setRenamingDocumentId] = useState<number | null>(
    null,
  );

  const [retryingDocumentId, setRetryingDocumentId] = useState<number | null>(
    null,
  );

  const [documentRenameValue, setDocumentRenameValue] = useState("");

  const [openConversationMenuId, setOpenConversationMenuId] = useState<
    number | null
  >(null);

  const [openDocumentMenuId, setOpenDocumentMenuId] = useState<number | null>(
    null,
  );

  const [movingDocumentId, setMovingDocumentId] = useState<number | null>(null);

  const [creatingCollection, setCreatingCollection] = useState(false);

  const [collectionName, setCollectionName] = useState("");

  const [collectionError, setCollectionError] = useState("");

  const [renamingCollectionId, setRenamingCollectionId] = useState<
    number | null
  >(null);

  const [collectionRenameValue, setCollectionRenameValue] = useState("");

  const [deletingCollectionId, setDeletingCollectionId] = useState<
    number | null
  >(null);

  const [openCollectionMenuId, setOpenCollectionMenuId] = useState<
    number | null
  >(null);

  const sidebarRef = useRef<HTMLElement | null>(null);

  /*
   * Load documents.
   */

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const latestDocuments = await getDocuments();

        setDocuments(latestDocuments);

        setDocumentsLoading(false);
      } catch (error) {
        console.error("Failed to load documents:", error);

        setDocumentsLoading(false);
      }
    };

    loadDocuments();

    const interval = setInterval(loadDocuments, 3000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  /*
   * Close menus outside sidebar.
   */

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        sidebarRef.current &&
        !sidebarRef.current.contains(event.target as Node)
      ) {
        setOpenConversationMenuId(null);
        setOpenDocumentMenuId(null);
        setOpenCollectionMenuId(null);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  /*
   * Upload document.
   */

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    try {
      setUploading(true);
      setUploadError("");
      setError("");

      const uploadedDocument =
  await uploadDocument(
    file,
    selectedCollectionId,
  );

      setDocuments((previous) => [uploadedDocument, ...previous]);

      onSelectDocument(uploadedDocument.id);

      onSelectConversation(null);

      event.target.value = "";
    } catch (err) {
      setUploadError(
        err instanceof Error ? err.message : "Failed to upload document.",
      );
    } finally {
      setUploading(false);
    }
  }

  /*
   * Add website.
   */

  async function handleAddWebsite(event: React.FormEvent) {
    event.preventDefault();

    const url = websiteUrl.trim();

    if (!url) {
      setWebsiteError("Please enter a website URL.");

      return;
    }

    try {
      setAddingWebsiteLoading(true);
      setWebsiteError("");
      setError("");

      const website =
  await addWebsite(
    url,
    selectedCollectionId,
  );

      setDocuments((previous) => [website, ...previous]);

      setWebsiteUrl("");
      setWebsiteError("");
      setAddingWebsite(false);

      onSelectDocument(website.id);

      onSelectConversation(null);
    } catch (err) {
      setWebsiteError(
        err instanceof Error ? err.message : "Failed to add website.",
      );
    } finally {
      setAddingWebsiteLoading(false);
    }
  }

  /*
   * Create collection.
   */

  async function handleCreateCollection(event: React.FormEvent) {
    event.preventDefault();

    const name = collectionName.trim();

    if (!name) {
      setCollectionError("Project name cannot be empty.");

      return;
    }

    try {
      setCollectionError("");

      const collection = await createCollection(name);

      setCollectionName("");
      setCreatingCollection(false);

      onCollectionCreated(collection);
    } catch (err) {
      setCollectionError(
        err instanceof Error ? err.message : "Failed to create project.",
      );
    }
  }

  /*
   * Start collection rename.
   */

  function startRenameCollection(collection: Collection) {
    setOpenCollectionMenuId(null);

    setRenamingCollectionId(collection.id);

    setCollectionRenameValue(collection.name);
  }

  function cancelRenameCollection() {
    setRenamingCollectionId(null);
    setCollectionRenameValue("");
  }

  /*
   * Save collection rename.
   */

  async function handleRenameCollection(collection: Collection) {
    const name = collectionRenameValue.trim();

    if (!name) {
      return;
    }

    if (name === collection.name) {
      cancelRenameCollection();
      return;
    }

    try {
      const updated = await renameCollection(collection.id, name);

      cancelRenameCollection();

      onCollectionUpdated(updated);
    } catch (err) {
      setCollectionError(
        err instanceof Error ? err.message : "Failed to rename project.",
      );
    }
  }

  /*
   * Delete collection.
   */

  async function handleDeleteCollection(
    event: React.MouseEvent,
    collectionId: number,
  ) {
    event.stopPropagation();

    const confirmed = window.confirm(
      "Delete this project? Documents will not be deleted.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingCollectionId(collectionId);

      await deleteCollection(collectionId);

      setOpenCollectionMenuId(null);

      onCollectionDeleted(collectionId);
    } catch (err) {
      setCollectionError(
        err instanceof Error ? err.message : "Failed to delete project.",
      );
    } finally {
      setDeletingCollectionId(null);
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

    const confirmed = window.confirm("Delete this conversation?");

    if (!confirmed) {
      return;
    }

    try {
      setDeletingConversationId(conversationId);

      await deleteConversation(conversationId);

      setOpenConversationMenuId(null);

      onConversationDeleted(conversationId);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete conversation.",
      );
    } finally {
      setDeletingConversationId(null);
    }
  }

  /*
   * Conversation rename.
   */

  function startRenameConversation(conversation: Conversation) {
    setOpenConversationMenuId(null);

    setRenamingConversationId(conversation.id);

    setConversationRenameValue(conversation.title);
  }

  function cancelRenameConversation() {
    setRenamingConversationId(null);
    setConversationRenameValue("");
  }

  async function handleRenameConversation(conversation: Conversation) {
    const title = conversationRenameValue.trim();

    if (!title) {
      return;
    }

    if (title === conversation.title) {
      cancelRenameConversation();
      return;
    }

    try {
      const updated = await renameConversation(conversation.id, title);

      cancelRenameConversation();

      onConversationUpdated?.(updated);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to rename conversation.",
      );
    }
  }

  async function handleRetryDocument(
    event: React.MouseEvent,
    documentId: number,
  ) {
    event.stopPropagation();

    try {
      setRetryingDocumentId(documentId);
      setError("");

      const updated = await retryDocumentProcessing(documentId);

      setDocuments((previous) =>
        previous.map((document) =>
          document.id === updated.id ? updated : document,
        ),
      );

      setOpenDocumentMenuId(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to retry document.",
      );
    } finally {
      setRetryingDocumentId(null);
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

    const confirmed = window.confirm(
      "Delete this document? This cannot be undone.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingDocumentId(documentId);

      await deleteDocument(documentId);

      setDocuments((previous) =>
        previous.filter((document) => document.id !== documentId),
      );

      setOpenDocumentMenuId(null);

      if (selectedDocumentId === documentId) {
        onSelectDocument(null);
        onSelectConversation(null);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete document.",
      );
    } finally {
      setDeletingDocumentId(null);
    }
  }

  /*
   * Document rename.
   */

  function startRenameDocument(document: Document) {
    setOpenDocumentMenuId(null);

    setRenamingDocumentId(document.id);

    setDocumentRenameValue(document.filename);
  }

  function cancelRenameDocument() {
    setRenamingDocumentId(null);
    setDocumentRenameValue("");
  }

  async function handleRenameDocument(document: Document) {
    const filename = documentRenameValue.trim();

    if (!filename) {
      return;
    }

    if (filename === document.filename) {
      cancelRenameDocument();
      return;
    }

    try {
      const updated = await renameDocument(document.id, filename);

      setDocuments((previous) =>
        previous.map((item) => (item.id === updated.id ? updated : item)),
      );

      cancelRenameDocument();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to rename document.",
      );
    }
  }

  /*
   * Documents belonging to the
   * selected project.
   *
   * We will use this later for
   * source assignment.
   */
  async function handleMoveDocument(documentId: number, collectionId: number) {
    try {
      setMovingDocumentId(documentId);
      setError("");

      const updated = await assignDocumentToCollection(
        documentId,
        collectionId,
      );

      setDocuments((previous) =>
        previous.map((document) =>
          document.id === updated.id ? updated : document,
        ),
      );

      setOpenDocumentMenuId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to move document.");
    } finally {
      setMovingDocumentId(null);
    }
  }

  async function handleRemoveDocumentFromCollection(documentId: number) {
    try {
      setMovingDocumentId(documentId);
      setError("");

      const updated = await removeDocumentFromCollection(documentId);

      setDocuments((previous) =>
        previous.map((document) =>
          document.id === updated.id ? updated : document,
        ),
      );

      setOpenDocumentMenuId(null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to remove document from project.",
      );
    } finally {
      setMovingDocumentId(null);
    }
  }

  const visibleDocuments =
    selectedCollectionId === null
      ? documents
      : documents.filter(
          (document) => document.collection_id === selectedCollectionId,
        );

  const displayedConversations = conversations.filter((conversation) =>
    conversation.title
      .toLowerCase()
      .includes(conversationSearch.trim().toLowerCase()),
  );

  return (
    <aside ref={sidebarRef} className="sidebar">
      {/* ================================================= */}
      {/* Projects */}
      {/* ================================================= */}

      <section className="sidebar-section">
        <div className="sidebar-section-header">
          <h3>Projects</h3>

          <button
            type="button"
            className="new-chat-button"
            onClick={() => {
              setCreatingCollection((previous) => !previous);

              setCollectionError("");
            }}
          >
            + New Project
          </button>
        </div>

        {creatingCollection && (
          <form className="website-form" onSubmit={handleCreateCollection}>
            <input
              type="text"
              placeholder="Project name"
              value={collectionName}
              onChange={(event) => setCollectionName(event.target.value)}
              autoFocus
            />

            <div className="website-form-actions">
              <button
                type="button"
                onClick={() => {
                  setCreatingCollection(false);

                  setCollectionName("");
                  setCollectionError("");
                }}
              >
                Cancel
              </button>

              <button type="submit" disabled={!collectionName.trim()}>
                Create Project
              </button>
            </div>

            {collectionError && (
              <p className="upload-error">{collectionError}</p>
            )}
          </form>
        )}

        <div className="document-list">
          <button
            type="button"
            className={`document-item ${
              selectedCollectionId === null && selectedDocumentId === null
                ? "selected"
                : ""
            }`}
            onClick={() => {
              onSelectCollection(null);
              onSelectConversation(null);
            }}
          >
            <span>🔍 All Documents</span>
          </button>

          {collections.length === 0 && (
            <p className="sidebar-status">No projects yet.</p>
          )}

          {collections.map((collection) => (
            <div
              key={collection.id}
              className={`document-row ${
                selectedCollectionId === collection.id ? "selected" : ""
              }`}
            >
              {renamingCollectionId === collection.id ? (
                <input
                  autoFocus
                  type="text"
                  className="sidebar-rename-input"
                  value={collectionRenameValue}
                  onChange={(event) =>
                    setCollectionRenameValue(event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      void handleRenameCollection(collection);
                    }

                    if (event.key === "Escape") {
                      cancelRenameCollection();
                    }
                  }}
                  onBlur={() => {
                    void handleRenameCollection(collection);
                  }}
                />
              ) : (
                <>
                  <button
                    type="button"
                    className="document-item"
                    onClick={() => {
                      onSelectCollection(collection.id);

                      onSelectConversation(null);
                    }}
                  >
                    <span className="document-name">📁 {collection.name}</span>
                  </button>

                  <div className="sidebar-menu-wrapper">
                    <button
                      type="button"
                      className="sidebar-menu-button"
                      aria-label="Project options"
                      title="Project options"
                      onClick={(event) => {
                        event.stopPropagation();

                        setOpenCollectionMenuId((previous) =>
                          previous === collection.id ? null : collection.id,
                        );

                        setOpenConversationMenuId(null);

                        setOpenDocumentMenuId(null);
                      }}
                    >
                      ⋮
                    </button>

                    {openCollectionMenuId === collection.id && (
                      <div className="sidebar-menu">
                        <button
                          type="button"
                          onClick={() => startRenameCollection(collection)}
                        >
                          Rename
                        </button>

                        <button
                          type="button"
                          className="danger"
                          disabled={deletingCollectionId === collection.id}
                          onClick={(event) =>
                            void handleDeleteCollection(event, collection.id)
                          }
                        >
                          {deletingCollectionId === collection.id
                            ? "Deleting..."
                            : "Delete"}
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ================================================= */}
      {/* Conversations */}
      {/* ================================================= */}

      <section className="sidebar-section">
        <div className="sidebar-section-header">
          <h3>{selectedCollectionId !== null ? "Project Chats" : "Chats"}</h3>

          <button type="button" className="new-chat-button" onClick={onNewChat}>
            + New Chat
          </button>
        </div>

        <input
          type="text"
          className="conversation-search"
          placeholder="Search conversations..."
          value={conversationSearch}
          onChange={(event) => setConversationSearch(event.target.value)}
        />

        <div className="conversation-list">
          {loadingConversations && (
            <p className="sidebar-status">Loading conversations...</p>
          )}

          {!loadingConversations && displayedConversations.length === 0 && (
            <p className="sidebar-status">No conversations yet.</p>
          )}

          {!loadingConversations &&
            displayedConversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`conversation-row ${
                  selectedConversationId === conversation.id ? "selected" : ""
                }`}
              >
                {renamingConversationId === conversation.id ? (
                  <input
                    autoFocus
                    type="text"
                    className="sidebar-rename-input"
                    value={conversationRenameValue}
                    onChange={(event) =>
                      setConversationRenameValue(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        void handleRenameConversation(conversation);
                      }

                      if (event.key === "Escape") {
                        cancelRenameConversation();
                      }
                    }}
                    onBlur={() => {
                      void handleRenameConversation(conversation);
                    }}
                  />
                ) : (
                  <>
                    <button
                      type="button"
                      className="conversation-item"
                      onClick={() => onSelectConversation(conversation.id)}
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
                        onClick={(event) => {
                          event.stopPropagation();

                          setOpenConversationMenuId((previous) =>
                            previous === conversation.id
                              ? null
                              : conversation.id,
                          );

                          setOpenDocumentMenuId(null);

                          setOpenCollectionMenuId(null);
                        }}
                      >
                        ⋮
                      </button>

                      {openConversationMenuId === conversation.id && (
                        <div className="sidebar-menu">
                          <button
                            type="button"
                            onClick={() =>
                              startRenameConversation(conversation)
                            }
                          >
                            Rename
                          </button>

                          <button
                            type="button"
                            className="danger"
                            disabled={
                              deletingConversationId === conversation.id
                            }
                            onClick={(event) =>
                              void handleDeleteConversation(
                                event,
                                conversation.id,
                              )
                            }
                          >
                            {deletingConversationId === conversation.id
                              ? "Deleting..."
                              : "Delete"}
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
        </div>
      </section>

      {/* ================================================= */}
      {/* Documents */}
      {/* ================================================= */}

      <section className="sidebar-section documents-section">
        <div className="sidebar-section-header">
          <h3>
            {selectedCollectionId !== null ? "Project Sources" : "Documents"}
          </h3>

          <label className={`upload-button ${uploading ? "uploading" : ""}`}>
            {uploading ? "Uploading..." : "+ Upload"}

            <input
              type="file"
              accept=".pdf,.docx,.md,.markdown"
              onChange={handleUpload}
              disabled={uploading}
              hidden
            />
          </label>

          <button
            type="button"
            className="website-button"
            onClick={() => setAddingWebsite((previous) => !previous)}
          >
            + Add Website
          </button>
        </div>

        {addingWebsite && (
          <form className="website-form" onSubmit={handleAddWebsite}>
            <input
              type="url"
              placeholder="https://example.com"
              value={websiteUrl}
              onChange={(event) => setWebsiteUrl(event.target.value)}
              disabled={addingWebsiteLoading}
              autoFocus
            />

            <div className="website-form-actions">
              <button
                type="button"
                onClick={() => {
                  setAddingWebsite(false);
                  setWebsiteUrl("");
                  setWebsiteError("");
                }}
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={addingWebsiteLoading || !websiteUrl.trim()}
              >
                {addingWebsiteLoading ? "Adding..." : "Add Website"}
              </button>
            </div>

            {websiteError && <p className="upload-error">{websiteError}</p>}
          </form>
        )}

        {uploadError && <p className="upload-error">{uploadError}</p>}

        <div className="document-list">
          {documentsLoading && (
            <p className="sidebar-status">Loading documents...</p>
          )}

          {error && <p className="sidebar-error">{error}</p>}

          {!documentsLoading && !error && visibleDocuments.length === 0 && (
            <p className="sidebar-status">
              {selectedCollectionId !== null
                ? "No sources in this project yet."
                : "No documents uploaded."}
            </p>
          )}

          {!documentsLoading &&
            !error &&
            visibleDocuments.map((document) => (
              <div
                key={document.id}
                className={`document-row ${
                  selectedDocumentId === document.id ? "selected" : ""
                }`}
              >
                {renamingDocumentId === document.id ? (
                  <input
                    autoFocus
                    type="text"
                    className="sidebar-rename-input"
                    value={documentRenameValue}
                    onChange={(event) =>
                      setDocumentRenameValue(event.target.value)
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        void handleRenameDocument(document);
                      }

                      if (event.key === "Escape") {
                        cancelRenameDocument();
                      }
                    }}
                    onBlur={() => {
                      void handleRenameDocument(document);
                    }}
                  />
                ) : (
                  <>
                    <button
                      type="button"
                      className="document-item"
                      onClick={() => {
                        onSelectDocument(document.id);

                        onSelectConversation(null);
                      }}
                    >
                      <span className="document-name">
                        📄 {document.filename}
                      </span>

                      <span
                        className={`document-status document-status-${document.status}`}
                        title={
                          document.status === "failed" &&
                          document.processing_error
                            ? document.processing_error
                            : undefined
                        }
                      >
                        {document.status === "processing" && "Processing"}

                        {document.status === "processed" && "Processed"}

                        {document.status === "failed" && "Failed"}

                        {!["processing", "processed", "failed"].includes(
                          document.status,
                        ) && document.status}
                      </span>
                      {document.status === "failed" &&
                        document.processing_error && (
                          <span className="document-processing-error">
                            {document.processing_error}
                          </span>
                        )}
                    </button>

                    <div className="sidebar-menu-wrapper">
                      <button
                        type="button"
                        className="sidebar-menu-button"
                        aria-label="Document options"
                        title="Document options"
                        onClick={(event) => {
                          event.stopPropagation();

                          setOpenDocumentMenuId((previous) =>
                            previous === document.id ? null : document.id,
                          );

                          setOpenConversationMenuId(null);

                          setOpenCollectionMenuId(null);
                        }}
                      >
                        ⋮
                      </button>

                      {openDocumentMenuId === document.id && (
                        <div className="sidebar-menu">
                          <button
                            type="button"
                            onClick={() => startRenameDocument(document)}
                          >
                            Rename
                          </button>
                          {document.status === "failed" && (
                            <button
                              type="button"
                              disabled={retryingDocumentId === document.id}
                              onClick={(event) =>
                                void handleRetryDocument(event, document.id)
                              }
                            >
                              {retryingDocumentId === document.id
                                ? "Retrying..."
                                : "Retry Processing"}
                            </button>
                          )}

                          {collections.length > 0 && (
                            <>
                              {document.collection_id === null ? (
                                <>
                                  <div
                                    style={{
                                      padding: "6px 10px",
                                      fontSize: "12px",
                                      opacity: 0.7,
                                    }}
                                  >
                                    Move to Project
                                  </div>

                                  {collections.map((collection) => (
                                    <button
                                      key={collection.id}
                                      type="button"
                                      disabled={
                                        movingDocumentId === document.id
                                      }
                                      onClick={() =>
                                        void handleMoveDocument(
                                          document.id,
                                          collection.id,
                                        )
                                      }
                                    >
                                      📁 {collection.name}
                                    </button>
                                  ))}
                                </>
                              ) : (
                                <button
                                  type="button"
                                  disabled={movingDocumentId === document.id}
                                  onClick={() =>
                                    void handleRemoveDocumentFromCollection(
                                      document.id,
                                    )
                                  }
                                >
                                  Remove from Project
                                </button>
                              )}
                            </>
                          )}

                          <button
                            type="button"
                            className="danger"
                            disabled={deletingDocumentId === document.id}
                            onClick={(event) =>
                              void handleDeleteDocument(event, document.id)
                            }
                          >
                            {deletingDocumentId === document.id
                              ? "Deleting..."
                              : "Delete"}
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
        </div>
      </section>
    </aside>
  );
}
