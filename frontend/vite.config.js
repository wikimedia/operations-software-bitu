import { defineConfig } from "vite";
import { resolve } from "path";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  base: "/static/",
  plugins: [vue()],
  build: {
    manifest: "manifest.json",
    outDir: resolve("./src/bitu/static/bundler"),
    rollupOptions: {
      input: {
        ssh: resolve("./frontend/src/ssh.js"),
        perms: resolve("./frontend/src/perm.js")
      },
    },
  },
});
