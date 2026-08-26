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
                selectedConversationId,
                chatResetKey,
                onConversationCreated,
                onConversationUpdated,
              ) => (
                <Chat
                  selectedDocumentId={
                    selectedDocumentId
                  }
                  selectedDocument={
                    selectedDocument
                  }
                  selectedConversationId={
                    selectedConversationId
                  }
                  chatResetKey={
                    chatResetKey
                  }
                  onConversationCreated={
                    onConversationCreated
                  }
                  onConversationUpdated={
                    onConversationUpdated
                  }
                />
              )}
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