import "./App.css";

import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";

import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

function App() {
  return (
    <Routes>
      {/* ============================== */}
      {/* Authentication */}
      {/* ============================== */}

      <Route
        path="/login"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      {/* ============================== */}
      {/* Protected Chat */}
      {/* ============================== */}

      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Layout>
              {(
                selectedDocumentId,
                selectedDocument,
                selectedCollectionId,
                selectedCollection,
                selectedConversationId,
                chatResetKey,
                onConversationCreated,
                onConversationUpdated,
                onDocumentStatusChange,
              ) => {
                void selectedCollection;

                return (
                  <Chat
                    selectedDocumentId={selectedDocumentId}
                    selectedDocument={selectedDocument}
                    collectionId={selectedCollectionId}
                    selectedConversationId={selectedConversationId}
                    chatResetKey={chatResetKey}
                    onConversationCreated={onConversationCreated}
                    onConversationUpdated={onConversationUpdated}
                    onDocumentStatusChange={onDocumentStatusChange}
                  />
                );
              }}
            </Layout>
          </ProtectedRoute>
        }
      />

      {/* ============================== */}
      {/* Fallback */}
      {/* ============================== */}

      <Route
        path="*"
        element={
          <Navigate
            to="/chat"
            replace
          />
        }
      />
    </Routes>
  );
}

export default App;