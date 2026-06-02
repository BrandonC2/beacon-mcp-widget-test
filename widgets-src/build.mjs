import { build } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../widgets");

const widgets = ["prepare_query", "query_executed", "field_values", "similar_text", "hierarchy"];

for (const name of widgets) {
  await build({
    plugins: [viteSingleFile()],
    build: {
      outDir,
      emptyOutDir: false,
      rollupOptions: {
        input: path.resolve(__dirname, `${name}.html`),
      },
    },
    logLevel: "warn",
  });
  console.log(`✓ ${name}`);
}
