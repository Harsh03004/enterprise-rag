import React, { useEffect, useRef, useState } from 'react'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { streamChat, type ChatSource } from '../api/chat'

import {
  getConversation,
  type Conversation,
  type Message
} from '../api/conversations'

import { retryDocumentProcessing, type Document } from '../api/documents'

interface ChatProps {
  selectedDocumentId: number | null

  selectedDocument: Document | null

  collectionId: number | null;

  selectedConversationId: number | null

  chatResetKey: number

  onConversationCreated: (conversation: Conversation) => void

  onConversationUpdated: (conversation: Conversation) => void

  onDocumentStatusChange?: (document: Document) => void
}

/*
 * --------------------------------------------------
 * Markdown components
 * --------------------------------------------------
 */

const markdownComponents = {
  table: ({ children }: { children?: React.ReactNode }) => (
    <div className='table-wrapper'>
      <table>{children}</table>
    </div>
  )
}

/*
 * --------------------------------------------------
 * Chat
 * --------------------------------------------------
 */

export default function Chat({
  selectedDocumentId,
  selectedDocument,
  collectionId,
  selectedConversationId,
  chatResetKey,
  onConversationCreated,
  onConversationUpdated,
  onDocumentStatusChange,
}: ChatProps) {
  const [question, setQuestion] = useState('')

  const [retryingProcessing, setRetryingProcessing] = useState(false)

  const [messages, setMessages] = useState<Message[]>([])

  const [answer, setAnswer] = useState('')

  const [sources, setSources] = useState<ChatSource[]>([])

  const [loading, setLoading] = useState(false)

  const [loadingConversation, setLoadingConversation] = useState(false)

  const [error, setError] = useState('')

  const [activeSourceId, setActiveSourceId] = useState<number | null>(null)

  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const sourceRefs = useRef<Record<number, HTMLDivElement | null>>({})

  /*
   * Identifies the currently visible chat.
   *
   * Changing chats does NOT invalidate the
   * backend stream anymore.
   */
  const visibleChatGenerationRef = useRef(0)

  /*
   * Identifies the current request.
   *
   * This is only changed when:
   *
   * - a new request starts
   * - the user explicitly presses Stop
   */
  const requestGenerationRef = useRef(0)

  const abortControllerRef = useRef<AbortController | null>(null)

  /*
   * Stores the conversation ID created
   * by the backend for a new chat.
   */
  const activeConversationIdRef = useRef<number | null>(null)

  /*
   * --------------------------------------------------
   * Load selected conversation
   * --------------------------------------------------
   */

  useEffect(() => {
    visibleChatGenerationRef.current += 1

    const visibleGeneration = visibleChatGenerationRef.current

    async function loadConversation () {
      /*
       * New empty chat.
       *
       * This does NOT show thinking.
       */
      if (selectedConversationId === null) {
        setMessages([])
        setAnswer('')
        setSources([])
        setError('')
        setLoading(false)
        setLoadingConversation(false)
        setActiveSourceId(null)

        activeConversationIdRef.current = null

        return
      }

      /*
       * We are opening an existing
       * conversation.
       */
      setMessages([])
      setAnswer('')
      setSources([])
      setError('')
      setLoading(false)
      setLoadingConversation(true)
      setActiveSourceId(null)

      try {
        const conversation = await getConversation(selectedConversationId)

        /*
         * Ignore the result if the user
         * switched again while loading.
         */
        if (visibleChatGenerationRef.current !== visibleGeneration) {
          return
        }

        setMessages(conversation.messages)

        activeConversationIdRef.current = conversation.id
      } catch (err) {
        if (visibleChatGenerationRef.current !== visibleGeneration) {
          return
        }

        setError(
          err instanceof Error ? err.message : 'Failed to load conversation.'
        )
      } finally {
        if (visibleChatGenerationRef.current === visibleGeneration) {
          setLoadingConversation(false)
        }
      }
    }

    void loadConversation()
  }, [selectedConversationId, chatResetKey])

  /*
   * --------------------------------------------------
   * New chat / document switch
   * --------------------------------------------------
   */

  useEffect(() => {
    visibleChatGenerationRef.current += 1

    /*
     * Reset only the visible UI.
     *
     * DO NOT touch requestGenerationRef here.
     * A running backend request must continue.
     *
     * Loading is controlled by the request itself.
     */
    setMessages([])
    setAnswer('')
    setSources([])
    setQuestion('')
    setError('')
    setActiveSourceId(null)

    activeConversationIdRef.current = null

    requestAnimationFrame(() => {
      resizeTextarea()
    })
  }, [chatResetKey])

  /*
   * --------------------------------------------------
   * Scroll
   * --------------------------------------------------
   */

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    })
  }, [messages, answer, loading])

  /*
   * --------------------------------------------------
   * Textarea
   * --------------------------------------------------
   */

  function resizeTextarea () {
    const textarea = textareaRef.current

    if (!textarea) {
      return
    }

    textarea.style.height = 'auto'

    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`
  }

  function handleQuestionChange (value: string) {
    setQuestion(value)

    requestAnimationFrame(() => {
      resizeTextarea()
    })
  }

  /*
   * --------------------------------------------------
   * Source citation navigation
   * --------------------------------------------------
   */

  function scrollToSource (sourceId: number) {
    const sourceElement = sourceRefs.current[sourceId]

    if (!sourceElement) {
      return
    }

    setActiveSourceId(sourceId)

    sourceElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })

    window.setTimeout(() => {
      setActiveSourceId(current => (current === sourceId ? null : current))
    }, 1800)
  }

  /*
   * Convert backend citations:
   *
   * [Source 1]
   *
   * into Markdown links:
   *
   * [1](#source-1)
   *
   * ReactMarkdown then passes these links
   * through the custom <a> renderer below.
   */
  function prepareMarkdown (content: string): string {
    return content.replace(
      /\[Source\s+(\d+)\]/gi,
      (match, sourceNumber: string) => {
        const number = Number(sourceNumber)

        const sourceExists = sources.some(source => source.id === number)

        if (!sourceExists) {
          return match
        }

        return `[${number}](#source-${number})`
      }
    )
  }

  /*
   * Render Markdown links.
   *
   * Citation links become buttons.
   * Normal links remain normal links.
   */
  const citationMarkdownComponents = {
    ...markdownComponents,

    a: ({ href, children }: { href?: string; children?: React.ReactNode }) => {
      const match = href?.match(/^#source-(\d+)$/)

      if (!match) {
        return (
          <a href={href} target='_blank' rel='noreferrer'>
            {children}
          </a>
        )
      }

      const sourceNumber = Number(match[1])

      return (
        <button
          type='button'
          className={`citation-button ${
            activeSourceId === sourceNumber ? 'citation-button-active' : ''
          }`}
          onClick={() => scrollToSource(sourceNumber)}
          title={`View Source ${sourceNumber}`}
        >
          [{sourceNumber}]
        </button>
      )
    }
  }

  /*
   * --------------------------------------------------
   * Stop
   * --------------------------------------------------
   */
  /*
   * --------------------------------------------------
   * Knowledge source processing retry
   * --------------------------------------------------
   */

  async function handleRetryProcessing () {
    if (!selectedDocument || retryingProcessing) {
      return
    }

    setRetryingProcessing(true)
    setError('')

    try {
      const updatedDocument = await retryDocumentProcessing(selectedDocument.id)

      /*
       * Update the selected document immediately
       * in the Chat UI.
       *
       * The Sidebar will also pick up the new
       * status through its existing polling.
       */
      onDocumentStatusChange?.(updatedDocument)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to retry document processing.'
      )
    } finally {
      setRetryingProcessing(false)
    }
  }

  function handleStop () {
    /*
     * THIS is where we invalidate the
     * current request.
     *
     * Switching chats does not do this.
     */
    requestGenerationRef.current += 1

    abortControllerRef.current?.abort()

    abortControllerRef.current = null

    setLoading(false)
  }

  /*
   * --------------------------------------------------
   * Submit
   * --------------------------------------------------
   */

  async function handleSubmit () {
    const trimmedQuestion = question.trim()

    if (!trimmedQuestion || loading || loadingConversation) {
      return
    }

    /*
     * This request belongs to whichever
     * conversation is currently selected.
     *
     * null means this is a NEW chat.
     */
    const requestConversationId = selectedConversationId

    /*
     * Create a brand-new request ID.
     */
    requestGenerationRef.current += 1

    const requestGeneration = requestGenerationRef.current

    /*
     * Capture which chat was visible when
     * the request started.
     */
    const requestVisibleGeneration = visibleChatGenerationRef.current

    /*
     * Clear input.
     */
    setQuestion('')

    requestAnimationFrame(() => {
      resizeTextarea()
    })

    setAnswer('')
    setSources([])
    setError('')
    setActiveSourceId(null)

    /*
     * Thinking appears ONLY HERE,
     * after the user actually sends a message.
     */
    setLoading(true)

    /*
     * Add the user's message immediately.
     */
    const temporaryUserMessage: Message = {
      id: Date.now(),
      conversation_id: requestConversationId ?? 0,
      role: 'user',
      content: trimmedQuestion,
      created_at: new Date().toISOString()
    }

    setMessages(previous => [...previous, temporaryUserMessage])

    /*
     * Local streamed answer.
     */
    let streamedAnswer = ''

    const abortController = new AbortController()

    abortControllerRef.current = abortController

    try {
      const effectiveDocumentId =
  selectedDocument?.id ?? selectedDocumentId;

const effectiveCollectionId =
  selectedDocument?.collection_id ?? collectionId;

await streamChat({
  question: trimmedQuestion,
  documentId: effectiveDocumentId,
  conversationId: requestConversationId,
  collectionId: effectiveCollectionId,
  signal: abortController.signal,

        /*
         * ----------------------------------------------
         * Conversation created / updated
         * ----------------------------------------------
         */

        onConversation: conversation => {
          /*
           * This request is no longer current.
           */
          if (requestGenerationRef.current !== requestGeneration) {
            return
          }

          /*
           * Backend created the real
           * conversation for a new chat.
           */
          activeConversationIdRef.current = conversation.id

          /*
           * Sidebar should know about it.
           */
          if (requestConversationId === null) {
            onConversationCreated(conversation)
          } else {
            onConversationUpdated(conversation)
          }
        },

        /*
         * ----------------------------------------------
         * Tokens
         * ----------------------------------------------
         */

        onToken: token => {
          /*
           * The request was explicitly
           * stopped/replaced.
           */
          if (requestGenerationRef.current !== requestGeneration) {
            return
          }

          /*
           * User switched to another chat.
           *
           * The backend continues, but we
           * don't render its tokens into
           * another conversation.
           */
          if (visibleChatGenerationRef.current !== requestVisibleGeneration) {
            return
          }

          streamedAnswer += token

          setAnswer(previous => previous + token)
        },

        /*
         * ----------------------------------------------
         * Sources
         * ----------------------------------------------
         */

        onSources: newSources => {
          if (requestGenerationRef.current !== requestGeneration) {
            return
          }

          if (visibleChatGenerationRef.current !== requestVisibleGeneration) {
            return
          }

          setSources(newSources)
        },

        /*
         * ----------------------------------------------
         * Backend complete
         * ----------------------------------------------
         */

        onComplete: () => {
          if (requestGenerationRef.current !== requestGeneration) {
            return
          }

          /*
           * If the user switched away,
           * don't change that other chat's UI.
           *
           * The response is already saved
           * by the backend.
           */
          if (visibleChatGenerationRef.current !== requestVisibleGeneration) {
            return
          }

          /*
           * Convert the streamed answer into
           * a normal message immediately.
           */
          if (streamedAnswer.trim()) {
            const conversationId =
              activeConversationIdRef.current ?? requestConversationId ?? 0

            const temporaryAssistantMessage: Message = {
              id: Date.now() + 1,

              conversation_id: conversationId,

              role: 'assistant',

              content: streamedAnswer,

              created_at: new Date().toISOString()
            }

            setMessages(previous => [...previous, temporaryAssistantMessage])

            setAnswer('')
          }

          setLoading(false)
        }
      })
    } catch (err) {
      /*
       * User pressed Stop.
       */
      if (err instanceof DOMException && err.name === 'AbortError') {
        return
      }

      /*
       * Old request.
       */
      if (requestGenerationRef.current !== requestGeneration) {
        return
      }

      /*
       * If the user switched chats,
       * don't put an error into the
       * newly selected conversation.
       */
      if (visibleChatGenerationRef.current !== requestVisibleGeneration) {
        return
      }

      setError(
        err instanceof Error ? err.message : 'Failed to generate response.'
      )
    } finally {
      if (requestGenerationRef.current === requestGeneration) {
        /*
         * Only stop the loading indicator
         * if this request is still current.
         */
        if (visibleChatGenerationRef.current === requestVisibleGeneration) {
          setLoading(false)
        }
      }

      if (abortControllerRef.current === abortController) {
        abortControllerRef.current = null
      }
    }
  }

  /*
   * --------------------------------------------------
   * Keyboard
   * --------------------------------------------------
   */

  function handleKeyDown (event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()

      void handleSubmit()
    }
  }

  /*
   * --------------------------------------------------
   * Derived values
   * --------------------------------------------------
   */

  const isDocumentSelected = selectedDocument !== null

  const documentName = selectedDocument?.filename ?? 'All Documents'

  const hasMessages = messages.length > 0 || answer.length > 0

  const documentStatus = selectedDocument?.status ?? null

  const isDocumentProcessing =
    isDocumentSelected &&
    (documentStatus === 'processing' || documentStatus === 'uploaded')

  const isDocumentFailed = isDocumentSelected && documentStatus === 'failed'

  /*
   * --------------------------------------------------
   * UI
   * --------------------------------------------------
   */

  return (
    <div className='chat-page'>
      {/* ======================================== */}
      {/* Header */}
      {/* ======================================== */}

      <header className='chat-header'>
        <div className='chat-header-info'>
          <h1>Document Chat</h1>

          <p>
            {isDocumentSelected
              ? `Searching ${documentName}`
              : 'Searching all documents'}
          </p>
        </div>

        <div className='selected-document'>
          {isDocumentSelected ? (
            <>
              <span>📄</span>

              <span>{documentName}</span>
            </>
          ) : (
            <>
              <span>🔍</span>

              <span>All Documents</span>
            </>
          )}
        </div>
      </header>

      {/* ======================================== */}
      {/* Chat content */}
      {/* ======================================== */}

      <div className='chat-content'>
        {!loadingConversation && isDocumentProcessing && (
          <div className='chat-status-state'>
            <div className='chat-status-icon'>⟳</div>

            <h2>Processing this knowledge source</h2>

            <p>{documentName} is being extracted, chunked, and indexed.</p>

            <p>You can start chatting once processing is complete.</p>
          </div>
        )}

        {!loadingConversation && isDocumentFailed && (
          <div className='chat-status-state chat-status-state-failed'>
            <div className='chat-status-icon'>!</div>

            <h2>Failed to process this knowledge source</h2>

            <p>
              We couldn't process
              {documentName}.
            </p>

            <div className='chat-processing-error'>
              <div className='chat-processing-error-label'>Reason</div>

              <div className='chat-processing-error-message'>
                {selectedDocument?.processing_error ||
                  'An unknown processing error occurred.'}
              </div>
            </div>

            <button
              type='button'
              className='chat-retry-button'
              onClick={() => void handleRetryProcessing()}
              disabled={retryingProcessing}
            >
              {retryingProcessing ? 'Retrying...' : 'Retry Processing'}
            </button>
          </div>
        )}

        {!loadingConversation &&
          !isDocumentProcessing &&
          !isDocumentFailed &&
          !hasMessages &&
          !error && (
            <div className='chat-empty-state'>
              <div className='chat-empty-icon'>✦</div>

              <h2>Ask your documents anything</h2>

              <p>
                {isDocumentSelected
                  ? `Ask questions about ${documentName}.`
                  : "Ask a question and I'll search your uploaded documents for the answer."}
              </p>

              <div className='example-prompts'>
                <button
                  type='button'
                  onClick={() =>
                    handleQuestionChange(
                      isDocumentSelected
                        ? `Summarize ${documentName}`
                        : 'Summarize my documents'
                    )
                  }
                >
                  Summarize the document
                </button>

                <button
                  type='button'
                  onClick={() =>
                    handleQuestionChange('What are the key points?')
                  }
                >
                  What are the key points?
                </button>

                <button
                  type='button'
                  onClick={() =>
                    handleQuestionChange(
                      'Explain this document in simple terms.'
                    )
                  }
                >
                  Explain it simply
                </button>
              </div>
            </div>
          )}

        {loadingConversation && (
          <div className='chat-loading'>Loading conversation...</div>
        )}

        {/* ====================================== */}
        {/* Messages */}
        {/* ====================================== */}

        <div className='messages-container'>
          {messages.map(message => (
            <div
              key={message.id}
              className={`chat-message ${
                message.role === 'user'
                  ? 'chat-message-user'
                  : 'chat-message-assistant'
              }`}
            >
              <div className='message-avatar'>
                {message.role === 'user' ? 'You' : 'AI'}
              </div>

              <div className='message-body'>
                <div className='message-role'>
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </div>

                <div className='message-content'>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={
                      message.role === 'assistant'
                        ? citationMarkdownComponents
                        : markdownComponents
                    }
                  >
                    {message.role === 'assistant'
                      ? prepareMarkdown(message.content)
                      : message.content}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          ))}

          {/* ================================== */}
          {/* Currently streaming */}
          {/* ================================== */}

          {answer && (
            <div className='chat-message chat-message-assistant'>
              <div className='message-avatar'>AI</div>

              <div className='message-body'>
                <div className='message-role'>Assistant</div>

                <div className='message-content'>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={citationMarkdownComponents}
                  >
                    {prepareMarkdown(answer)}
                  </ReactMarkdown>

                  {loading && <span className='streaming-cursor'>▌</span>}
                </div>
              </div>
            </div>
          )}

          {/* ================================== */}
          {/* Thinking */}
          {/* ================================== */}

          {loading && !answer && (
            <div className='chat-message chat-message-assistant'>
              <div className='message-avatar'>AI</div>

              <div className='message-body'>
                <div className='message-role'>Assistant</div>

                <div className='thinking-indicator'>
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          {/* ================================== */}
          {/* Error */}
          {/* ================================== */}

          {error && <div className='chat-error'>{error}</div>}

          {/* ================================== */}
          {/* Sources */}
          {/* ================================== */}

          {sources.length > 0 && (
            <div className='sources-panel'>
              <div className='sources-header'>Sources</div>

              <div className='sources-list'>
                {sources.map(source => (
                  <div
                    key={source.id}
                    ref={element => {
                      sourceRefs.current[source.id] = element
                    }}
                    className={`source-card ${
                      activeSourceId === source.id ? 'source-card-active' : ''
                    }`}
                  >
                    <div className='source-filename'>
                      <span>[{source.id}]</span> 📄 {source.filename}
                    </div>

                    <div className='source-meta'>
                      <span>Chunk {source.chunk_index + 1}</span>

                      <span>Distance {source.distance.toFixed(4)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* ======================================== */}
      {/* Input */}
      {/* ======================================== */}

      <div className='chat-input-area'>
        <div className='chat-input-wrapper'>
          <textarea
            ref={textareaRef}
            value={question}
            onChange={event => handleQuestionChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isDocumentSelected
                ? `Ask about ${documentName}...`
                : 'Ask your documents...'
            }
            disabled={
              loading ||
              loadingConversation ||
              isDocumentProcessing ||
              isDocumentFailed
            }
            rows={1}
          />

          <button
            type='button'
            className='send-button'
            onClick={() => {
              if (loading) {
                handleStop()
                return
              }

              void handleSubmit()
            }}
            disabled={
              loadingConversation ||
              isDocumentProcessing ||
              isDocumentFailed ||
              (!loading && !question.trim())
            }
            title={loading ? 'Stop generating' : 'Send message'}
          >
            {loading ? '■' : '↑'}
          </button>
        </div>

        <div className='chat-input-hint'>
          Enter to send · Shift + Enter for new line
        </div>
      </div>
    </div>
  )
}
