import { defineConfig } from "vite";

// Vite transpiles .tsx via esbuild, so no React plugin is required for the build.
// `allowedHosts: true` lets `vite preview` serve behind Railway's generated domain;
// fine for a public demo, tighten to the explicit host for a production app.
export default defineConfig({
  preview: {
    allowedHosts: true,
  },
});
