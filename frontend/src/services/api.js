import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  timeout: 20000
});

export async function planTrip(payload) {
  const { data } = await api.post("/plan-trip", payload);
  return data;
}

export async function listTrips() {
  const { data } = await api.get("/trips");
  return data;
}
