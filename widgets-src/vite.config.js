import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "../widgets",
    emptyOutDir: false,
    rollupOptions: {
      input: {
        prepare_query: "./prepare_query.html",
        query_executed: "./query_executed.html",
        field_values: "./field_values.html",
        similar_text: "./similar_text.html",
        hierarchy: "./hierarchy.html",
      },
      output: {
        entryFileNames: "[name].html",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
