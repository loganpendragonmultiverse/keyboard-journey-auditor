import { mkdir, copyFile } from "node:fs/promises";
await mkdir("dist/docs", { recursive: true });
await mkdir("dist/examples", { recursive: true });
for (const name of ["index.html", "recorder.js", "app.js", "style.css", "README.md", "LICENSE",
  "DEVELOPMENT.md", "TESTING.md", "SECURITY.md", "CHANGELOG.md", "CONTRIBUTING.md",
  "SUPPORT.md", "CODE_OF_CONDUCT.md", "docs/integration.md", "docs/native-acceptance.md", "examples/exit-rehearsal.html", "examples/exit-rehearsal.js", "examples/exit-rehearsal.css"]) {
  await copyFile(name, "dist/" + name);
}
console.log("Built local static application and linked documentation in dist/");
