import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/honeypot": "http://localhost:8000",
      "/sessions": "http://localhost:8000",
      "/patterns": "http://localhost:8000",
      "/callbacks": "http://localhost:8000",
      "/system": "http://localhost:8000",
    },
  },
});
