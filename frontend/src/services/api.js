import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "https://fmcsa-trip-planner.onrender.com/api";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

export const planTrip = (payload) => api.post("/plan-trip", payload).then(r => r.data);
export const listTrips = () => api.get("/trips").then(r => r.data);