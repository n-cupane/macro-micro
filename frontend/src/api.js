import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const loginUser = (email, password) => {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  return api.post("/token", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
};

export const salvaDietaCompleta = (payload) => {
  return api.post("/diete/completa", payload);
};

export const aggiornaDietaCompleta = (id, payload) => {
  return api.put(`/diete/${id}/completa`, payload);
};

export const eliminaDieta = (id) => {
  return api.delete(`/diete/${id}`);
};

export const calcolaMicroGiornalieri = (alimenti) => {
  return api.post("/nutrizione/giornaliera/micro", { alimenti });
};

export default api;
