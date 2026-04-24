import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "https://fmcsa-trip-planner.onrender.com/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

export async function planTrip(payload) {
  const { data } = await api.post("/plan-trip", payload);
  return data;
}

export async function listTrips() {
  const { data } = await api.get("/trips");
  return data;
}
