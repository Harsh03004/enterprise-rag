import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import Header from "./Header";
import Sidebar from "./Sidebar";

import {
  getConversations,
  type Conversation,
} from "../api/conversations";

import {
  getDocuments,
  type Document,
} from "../api/documents";

import {
  getCollections,
  type Collection,
} from "../api/collections";


interface LayoutProps {
  children: (
    selectedDocumentId: number | null,
    selectedDocument: Document | null,
    selectedCollectionId: number | null,
    selectedCollection: Collection | null,
    selectedConversationId: number | null,
    chatResetKey: number,
    onConversationCreated: (
      conversation: Conversation,
    ) => void,
    onConversationUpdated: (
      conversation: Conversation,
    ) => void,
    onDocumentStatusChange: (
      document: Document,
    ) => void,
  ) => ReactNode;
}


export default function Layout({
  children,
}: LayoutProps) {
  const [
    selectedDocumentId,
    setSelectedDocumentId,
  ] = useState<number | null>(null);

  const [
    selectedCollectionId,
    setSelectedCollectionId,
  ] = useState<number | null>(null);

  const [
    selectedConversationId,
    setSelectedConversationId,
  ] = useState<number | null>(null);

  const [
    documents,
    setDocuments,
  ] = useState<Document[]>([]);

  const [
    collections,
    setCollections,
  ] = useState<Collection[]>([]);

  const [
    conversations,
    setConversations,
  ] = useState<Conversation[]>([]);

  const [
    loadingConversations,
    setLoadingConversations,
  ] = useState(true);

  const [
    chatResetKey,
    setChatResetKey,
  ] = useState(0);


  /*
   * Load documents.
   */

  useEffect(() => {
    async function loadDocuments() {
      try {
        const data =
          await getDocuments();

        setDocuments(data);
      } catch (error) {
        console.error(
          "Failed to load documents:",
          error,
        );
      }
    }

    loadDocuments();

    const interval =
      setInterval(
        loadDocuments,
        3000,
      );

    return () => {
      clearInterval(interval);
    };
  }, []);


  /*
   * Load collections.
   */

  useEffect(() => {
    async function loadCollections() {
      try {
        const data =
          await getCollections();

        setCollections(data);
      } catch (error) {
        console.error(
          "Failed to load collections:",
          error,
        );
      }
    }

    loadCollections();
  }, []);


  /*
   * Resolve selected document.
   */

  const selectedDocument =
    documents.find(
      (document) =>
        document.id ===
        selectedDocumentId,
    ) ?? null;


  /*
   * Resolve selected collection.
   */

  const selectedCollection =
    collections.find(
      (collection) =>
        collection.id ===
        selectedCollectionId,
    ) ?? null;


  /*
   * Load conversations according
   * to the current scope.
   *
   * Priority:
   *
   * Document
   * Collection
   * All Documents
   */

  useEffect(() => {
    async function loadConversations() {
      try {
        setLoadingConversations(true);

        const data =
  await getConversations(
    selectedDocumentId,
    selectedCollectionId,
  );
        setConversations(data);

        if (
          selectedConversationId !==
          null
        ) {
          const exists =
            data.some(
              (conversation) =>
                conversation.id ===
                selectedConversationId,
            );

          if (!exists) {
            setSelectedConversationId(
              null,
            );
          }
        }
      } catch (error) {
        console.error(
          "Failed to load conversations:",
          error,
        );

        setConversations([]);
        setSelectedConversationId(null);
      } finally {
        setLoadingConversations(false);
      }
    }

    loadConversations();
  }, [
    selectedDocumentId,
    selectedCollectionId,
  ]);


  /*
   * Select a document.
   */

  function handleSelectDocument(
    documentId: number | null,
  ) {
    setSelectedDocumentId(
      documentId,
    );

    /*
     * Selecting a document leaves
     * project scope.
     */
   

    setSelectedConversationId(null);

    setChatResetKey(
      (previous) =>
        previous + 1,
    );
  }


  /*
   * Select a collection/project.
   */

  function handleSelectCollection(
    collectionId: number | null,
  ) {
    setSelectedCollectionId(
      collectionId,
    );

    /*
     * Project chat is not tied to
     * an individual document.
     */
    setSelectedDocumentId(null);

    setSelectedConversationId(null);

    setChatResetKey(
      (previous) =>
        previous + 1,
    );
  }


  /*
   * Select conversation.
   */

  function handleSelectConversation(
    conversationId: number | null,
  ) {
    setSelectedConversationId(
      conversationId,
    );
  }


  /*
   * Start new chat.
   */

  function handleNewChat() {
    setSelectedConversationId(null);

    setChatResetKey(
      (previous) =>
        previous + 1,
    );
  }


  /*
   * Conversation created.
   */

  function handleConversationCreated(
  conversation: Conversation,
) {
  setConversations(
    (previous) => [
      conversation,
      ...previous.filter(
        (item) =>
          item.id !==
          conversation.id,
      ),
    ],
  );

  /*
   * Only select the newly created conversation
   * if it belongs to the scope that is currently
   * visible in the UI.
   */
  const belongsToCurrentScope =
    selectedCollectionId !== null
      ? conversation.collection_id ===
        selectedCollectionId
      : selectedDocumentId !== null
        ? conversation.document_id ===
          selectedDocumentId
        : conversation.collection_id === null &&
          conversation.document_id === null;

  if (belongsToCurrentScope) {
    setSelectedConversationId(
      conversation.id,
    );
  }
}


  /*
   * Conversation updated.
   */

  function handleConversationUpdated(
  conversation: Conversation,
) {
  setConversations(
    (previous) => [
      conversation,
      ...previous.filter(
        (item) =>
          item.id !==
          conversation.id,
      ),
    ],
  );

  /*
   * Never keep an incompatible conversation
   * selected after a scope change.
   */
  const belongsToCurrentScope =
    selectedCollectionId !== null
      ? conversation.collection_id ===
        selectedCollectionId
      : selectedDocumentId !== null
        ? conversation.document_id ===
          selectedDocumentId
        : conversation.collection_id === null &&
          conversation.document_id === null;

  if (
    !belongsToCurrentScope &&
    selectedConversationId ===
      conversation.id
  ) {
    setSelectedConversationId(null);

    setChatResetKey(
      (previous) =>
        previous + 1,
    );
  }
}


  /*
   * Conversation deleted.
   */

  function handleConversationDeleted(
    conversationId: number,
  ) {
    setConversations(
      (previous) =>
        previous.filter(
          (conversation) =>
            conversation.id !==
            conversationId,
        ),
    );

    if (
      selectedConversationId ===
      conversationId
    ) {
      setSelectedConversationId(null);

      setChatResetKey(
        (previous) =>
          previous + 1,
      );
    }
  }


  /*
   * Document processing status.
   */

  function handleDocumentStatusChange(
    document: Document,
  ) {
    setDocuments(
      (previous) =>
        previous.map(
          (item) =>
            item.id === document.id
              ? document
              : item,
        ),
    );
  }


  /*
   * Collection created.
   */

  function handleCollectionCreated(
    collection: Collection,
  ) {
    setCollections(
      (previous) => [
        collection,
        ...previous.filter(
          (item) =>
            item.id !==
            collection.id,
        ),
      ],
    );

    handleSelectCollection(
      collection.id,
    );
  }


  /*
   * Collection updated.
   */

  function handleCollectionUpdated(
    collection: Collection,
  ) {
    setCollections(
      (previous) =>
        previous.map(
          (item) =>
            item.id === collection.id
              ? collection
              : item,
        ),
    );
  }


  /*
   * Collection deleted.
   */

  function handleCollectionDeleted(
    collectionId: number,
  ) {
    setCollections(
      (previous) =>
        previous.filter(
          (collection) =>
            collection.id !==
            collectionId,
        ),
    );

    if (
      selectedCollectionId ===
      collectionId
    ) {
      setSelectedCollectionId(null);
      setSelectedConversationId(null);

      setChatResetKey(
        (previous) =>
          previous + 1,
      );
    }
  }


  return (
    <div className="app">
      <Header />

      <div className="app-body">
        <Sidebar
          selectedDocumentId={
            selectedDocumentId
          }

          selectedCollectionId={
            selectedCollectionId
          }

          selectedConversationId={
            selectedConversationId
          }

          onSelectDocument={
            handleSelectDocument
          }

          onSelectCollection={
            handleSelectCollection
          }

          onSelectConversation={
            handleSelectConversation
          }

          onNewChat={
            handleNewChat
          }

          conversations={
            conversations
          }

          loadingConversations={
            loadingConversations
          }

          collections={
            collections
          }

          onCollectionCreated={
            handleCollectionCreated
          }

          onCollectionUpdated={
            handleCollectionUpdated
          }

          onCollectionDeleted={
            handleCollectionDeleted
          }

          onConversationDeleted={
            handleConversationDeleted
          }

          onConversationUpdated={
            handleConversationUpdated
          }
        />

        <main className="main-content">
          {children(
            selectedDocumentId,
            selectedDocument,
            selectedCollectionId,
            selectedCollection,
            selectedConversationId,
            chatResetKey,
            handleConversationCreated,
            handleConversationUpdated,
            handleDocumentStatusChange,
          )}
        </main>
      </div>
    </div>
  );
}