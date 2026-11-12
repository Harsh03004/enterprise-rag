import "./App.css";

import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Admin from "./pages/Admin";
import Evaluations from "./pages/Evaluations";
import AdminSettings from "./pages/AdminSettings";
import AdminContent from "./pages/AdminContent";

import ProtectedRoute from "./components/ProtectedRoute";
import AdminRoute from "./components/AdminRoute";
import Layout from "./components/Layout";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
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

      <Route
        path="/admin"
        element={
          <AdminRoute>
            <Admin />
          </AdminRoute>
        }
      />

      <Route path="/admin/content" element={<AdminRoute><AdminContent /></AdminRoute>} />
      <Route path="/admin/evaluations" element={<AdminRoute><Evaluations /></AdminRoute>} />
      <Route path="/admin/settings" element={<AdminRoute><AdminSettings /></AdminRoute>} />

      {/* ============================== */}
      {/* Fallback */}
      {/* ============================== */}

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />
    </Routes>
  );
}

export default App;
