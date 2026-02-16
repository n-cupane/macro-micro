import { Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./Dashboard";
import DietBuilder from "./components/DietBuilder";
import Login from "./components/Login";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  const token = localStorage.getItem("token");

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dieta/nuova"
        element={
          <ProtectedRoute>
            <DietBuilder />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dieta/:id"
        element={
          <ProtectedRoute>
            <DietBuilder />
          </ProtectedRoute>
        }
      />
      <Route
        path="*"
        element={<Navigate to={token ? "/dashboard" : "/login"} replace />}
      />
    </Routes>
  );
}

export default App;
