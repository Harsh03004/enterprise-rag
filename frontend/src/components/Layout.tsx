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

interface LayoutProps {
  children: (
    selectedDocumentId: number | null,
    selectedDocument: Document | null,
    selectedConversationId: number | null,
    chatResetKey: number,
    onConversationCreated: (
      conversation: Conversation,
    ) => void,
    onConversationUpdated: (
      conversation: Conversation,
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
    selectedConversationId,
    setSelectedConversationId,
  ] = useState<number | null>(null);

  const [
    documents,
    setDocuments,
  ] = useState<Document[]>([]);

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
   * Load documents once.
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
  }, []);

  /*
   * Find the complete selected document.
   */
  const selectedDocument =
    documents.find(
      (document) =>
        document.id ===
        selectedDocumentId,
    ) ?? null;

  /*
   * Load conversations whenever
   * the selected document changes.
   */
  useEffect(() => {
    async function loadConversations() {
      try {
        setLoadingConversations(true);

        const data =
          await getConversations(
            selectedDocumentId,
          );

        setConversations(data);

        if (
          selectedConversationId !==
          null
        ) {
          const exists = data.some(
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
      } finally {
        setLoadingConversations(false);
      }
    }

    loadConversations();
  }, [selectedDocumentId]);

  /*
   * Document selection.
   */
  function handleSelectDocument(
    documentId: number | null,
  ) {
    setSelectedDocumentId(
      documentId,
    );

    setSelectedConversationId(
      null,
    );

    setChatResetKey(
      (previous) =>
        previous + 1,
    );
  }

  /*
   * Conversation selection.
   */
  function handleSelectConversation(
    conversationId: number | null,
  ) {
    setSelectedConversationId(
      conversationId,
    );
  }

  /*
   * Start a completely new chat.
   */
  function handleNewChat() {
    setSelectedConversationId(
      null,
    );

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

    setSelectedConversationId(
      conversation.id,
    );
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
      setSelectedConversationId(
        null,
      );

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

          selectedConversationId={
            selectedConversationId
          }

          onSelectDocument={
            handleSelectDocument
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
            selectedConversationId,
            chatResetKey,
            handleConversationCreated,
            handleConversationUpdated,
          )}
        </main>

      </div>
    </div>
  );
}