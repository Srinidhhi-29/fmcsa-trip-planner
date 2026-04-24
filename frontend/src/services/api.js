import axios from "axios";

const API_BASE = "https://fmcsa-trip-planner.onrender.com/api";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});