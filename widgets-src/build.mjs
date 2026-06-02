import { readFileSync, writeFileSync, mkdirSync, rmSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, "../widgets");
const tmpDir = path.resolve(__dirname, ".build-tmp");

const widgets = ["prepare_query", "query_executed", "field_values", "similar_text", "hierarchy"];

mkdirSync(tmpDir, { recursive: true });

for (const name of widgets) {
  const result = await Bun.build({
    entrypoints: [path.resolve(__dirname, `${name}.js`)],
    outdir: tmpDir,
    bundle: true,
    minify: true,
    target: "browser",
  });

  if (!result.success) {
    console.error(`✗ ${name}`, result.logs);
    process.exit(1);
  }

  const js = readFileSync(path.resolve(tmpDir, `${name}.js`), "utf8")
    .replaceAll("</script>", "<\\/script>");

  // Use a replacer function so $ in the bundle JS isn't treated as a back-reference
  const html = readFileSync(path.resolve(__dirname, `${name}.html`), "utf8").replace(
    `<script type="module" src="./${name}.js"></script>`,
    () => `<script type="module">${js}</script>`
  );

  writeFileSync(path.resolve(outDir, `${name}.html`), html);
  console.log(`✓ ${name}`);
}

rmSync(tmpDir, { recursive: true });
