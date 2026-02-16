import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { eliminaDieta } from "./api";

function Dashboard() {
  const navigate = useNavigate();
  const [diete, setDiete] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dietToDelete, setDietToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const fetchDiete = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await api.get("/diete");
        setDiete(response.data);
      } catch (_err) {
        setError("Impossibile caricare le diete.");
      } finally {
        setLoading(false);
      }
    };

    fetchDiete();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const handleCreateDiet = () => {
    navigate("/dieta/nuova");
  };

  const handleOpenDiet = (dietId) => {
    navigate(`/dieta/${dietId}`);
  };

  const handleDeleteClick = (dieta) => {
    setDietToDelete(dieta);
  };

  const handleConfirmDelete = async () => {
    if (!dietToDelete) {
      return;
    }
    try {
      setIsDeleting(true);
      await eliminaDieta(dietToDelete.id);
      setDiete((prev) => prev.filter((dieta) => dieta.id !== dietToDelete.id));
      setDietToDelete(null);
    } catch (_err) {
      setError("Errore durante l'eliminazione della dieta.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <main style={styles.page}>
      <section style={styles.container}>
        <header style={styles.header}>
          <h1 style={styles.title}>Le tue diete</h1>
          <div style={styles.actions}>
            <button type="button" onClick={handleCreateDiet} style={styles.primaryButton}>
              Crea Nuova Dieta
            </button>
            <button type="button" onClick={handleLogout} style={styles.secondaryButton}>
              Logout
            </button>
          </div>
        </header>

        {loading && <p>Caricamento...</p>}
        {error && <p style={styles.error}>{error}</p>}

        {!loading && !error && diete.length === 0 && (
          <p style={styles.empty}>Nessuna dieta trovata. Crea la prima dieta.</p>
        )}

        {!loading && !error && diete.length > 0 && (
          <div style={styles.grid}>
            {diete.map((dieta) => (
              <article key={dieta.id} style={styles.card}>
                <h2 style={styles.cardTitle}>{dieta.nome_dieta}</h2>
                <p style={styles.cardMeta}>Creata: {dieta.data_creazione}</p>
                <div style={styles.cardActions}>
                  <button
                    type="button"
                    onClick={() => handleOpenDiet(dieta.id)}
                    style={styles.cardButton}
                  >
                    Apri/Modifica
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteClick(dieta)}
                    style={styles.deleteButton}
                  >
                    Elimina
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      {dietToDelete && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Conferma eliminazione</h3>
            <p style={styles.modalText}>
              Vuoi eliminare definitivamente la dieta
              {" "}
              <strong>{dietToDelete.nome_dieta}</strong>?
            </p>
            <div style={styles.modalActions}>
              <button
                type="button"
                style={styles.modalCancelButton}
                onClick={() => setDietToDelete(null)}
                disabled={isDeleting}
              >
                Annulla
              </button>
              <button
                type="button"
                style={styles.modalDeleteButton}
                onClick={handleConfirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? "Eliminazione..." : "Elimina"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

const styles = {
  page: {
    width: "100%",
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "flex-start",
    padding: "2rem 1rem 1rem",
    boxSizing: "border-box",
  },
  container: {
    width: "min(1400px, 100%)",
    background: "#ffffff",
    borderRadius: "16px",
    border: "1px solid #dbe2ea",
    padding: "1.25rem",
    boxShadow: "0 20px 45px rgba(15, 23, 42, 0.08)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "1rem",
    gap: "1rem",
    flexWrap: "wrap",
  },
  title: {
    margin: 0,
    color: "#0f172a",
  },
  actions: {
    display: "flex",
    gap: "0.5rem",
  },
  primaryButton: {
    border: "none",
    borderRadius: "10px",
    padding: "0.65rem 0.95rem",
    fontWeight: 700,
    background: "#0f766e",
    color: "#fff",
    cursor: "pointer",
  },
  secondaryButton: {
    border: "1px solid #cbd5e1",
    borderRadius: "10px",
    padding: "0.65rem 0.95rem",
    fontWeight: 700,
    background: "#fff",
    color: "#0f172a",
    cursor: "pointer",
  },
  error: {
    color: "#b91c1c",
  },
  empty: {
    color: "#475569",
  },
  grid: {
    display: "grid",
    gap: "1rem",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
  },
  card: {
    border: "1px solid #d7dee8",
    borderRadius: "12px",
    padding: "0.9rem",
    background: "#f8fafc",
    display: "grid",
    gap: "0.5rem",
  },
  cardTitle: {
    margin: 0,
    fontSize: "1.05rem",
    color: "#0f172a",
  },
  cardMeta: {
    margin: 0,
    color: "#475569",
    fontSize: "0.9rem",
  },
  cardButton: {
    border: "none",
    borderRadius: "9px",
    padding: "0.55rem 0.85rem",
    background: "#14532d",
    color: "#fff",
    cursor: "pointer",
  },
  cardActions: {
    display: "flex",
    gap: "0.5rem",
    flexWrap: "wrap",
  },
  deleteButton: {
    border: "none",
    borderRadius: "9px",
    padding: "0.55rem 0.85rem",
    background: "#b91c1c",
    color: "#fff",
    cursor: "pointer",
  },
  modalOverlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(2, 6, 23, 0.45)",
    display: "grid",
    placeItems: "center",
    padding: "1rem",
  },
  modal: {
    width: "min(460px, 100%)",
    background: "#ffffff",
    borderRadius: "14px",
    border: "1px solid #dbe2ea",
    padding: "1rem",
    boxShadow: "0 20px 45px rgba(15, 23, 42, 0.22)",
  },
  modalTitle: {
    margin: "0 0 0.5rem 0",
    color: "#0f172a",
  },
  modalText: {
    margin: 0,
    color: "#334155",
  },
  modalActions: {
    marginTop: "1rem",
    display: "flex",
    justifyContent: "flex-end",
    gap: "0.5rem",
  },
  modalCancelButton: {
    border: "1px solid #cbd5e1",
    borderRadius: "9px",
    padding: "0.5rem 0.85rem",
    background: "#ffffff",
    color: "#0f172a",
    cursor: "pointer",
    fontWeight: 700,
  },
  modalDeleteButton: {
    border: "none",
    borderRadius: "9px",
    padding: "0.5rem 0.85rem",
    background: "#b91c1c",
    color: "#ffffff",
    cursor: "pointer",
    fontWeight: 700,
  },
};

export default Dashboard;
