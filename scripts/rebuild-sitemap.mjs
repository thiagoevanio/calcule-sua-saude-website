import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const domain = "https://www.calculesuasaude.com.br";
const sitemapPath = path.join(root, "sitemap.xml");

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === ".git" || entry.name === "node_modules") return [];
      return walk(full);
    }
    return [full];
  });
}

function attr(tag, name) {
  const match = tag.match(new RegExp(`\\b${name}\\s*=\\s*(["'])(.*?)\\1`, "is"));
  return match ? match[2].trim() : "";
}

function pageUrl(file) {
  const relative = path.relative(root, file).replaceAll("\\", "/");
  return relative === "index.html" ? `${domain}/` : `${domain}/${relative}`;
}

function defaults(file) {
  const relative = path.relative(root, file).replaceAll("\\", "/");
  if (relative === "index.html") return { changefreq: "daily", priority: "1.00" };
  if (["artigos.html", "calculadoras.html", "quizzes.html", "receitas.html"].includes(relative)) {
    return { changefreq: "weekly", priority: "0.90" };
  }
  if (relative.startsWith("artigos/")) return { changefreq: "monthly", priority: "0.82" };
  if (relative.startsWith("calculadoras/") || relative.startsWith("receitas/")) {
    return { changefreq: "monthly", priority: "0.80" };
  }
  return { changefreq: "monthly", priority: "0.70" };
}

const existing = new Map();
if (fs.existsSync(sitemapPath)) {
  const xml = fs.readFileSync(sitemapPath, "utf8");
  for (const match of xml.matchAll(
    /<url>\s*<loc>(.*?)<\/loc>\s*<lastmod>(.*?)<\/lastmod>\s*<changefreq>(.*?)<\/changefreq>\s*<priority>(.*?)<\/priority>\s*<\/url>/g,
  )) {
    existing.set(match[1], {
      lastmod: match[2],
      changefreq: match[3],
      priority: match[4],
    });
  }
}

const rows = [];
for (const file of walk(root).filter((item) => item.endsWith(".html"))) {
  const relative = path.relative(root, file).replaceAll("\\", "/");
  if (relative === "404.html" || relative.startsWith("scripts/")) continue;

  const html = fs.readFileSync(file, "utf8").replace(/<!--[\s\S]*?-->/g, "");
  const robotsTag = [...html.matchAll(/<meta\b[^>]*>/gi)].find(
    (match) => attr(match[0], "name").toLowerCase() === "robots",
  )?.[0] || "";
  if (/\bnoindex\b/i.test(attr(robotsTag, "content"))) continue;

  const canonicalTag = [...html.matchAll(/<link\b[^>]*>/gi)].find(
    (match) => attr(match[0], "rel").toLowerCase() === "canonical",
  )?.[0] || "";
  const canonical = attr(canonicalTag, "href");
  const expected = pageUrl(file);
  if (!canonical || canonical !== expected) continue;

  const previous = existing.get(canonical);
  const fallback = defaults(file);
  rows.push({
    loc: canonical,
    lastmod: fs.statSync(file).mtime.toISOString().slice(0, 10),
    changefreq: previous?.changefreq || fallback.changefreq,
    priority: previous?.priority || fallback.priority,
  });
}

rows.sort((a, b) => a.loc.localeCompare(b.loc, "en"));

const xml = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
  ...rows.map(
    (row) =>
      `  <url><loc>${row.loc.replaceAll("&", "&amp;")}</loc><lastmod>${row.lastmod}</lastmod><changefreq>${row.changefreq}</changefreq><priority>${row.priority}</priority></url>`,
  ),
  "</urlset>",
  "",
].join("\n");

fs.writeFileSync(sitemapPath, xml, "utf8");
console.log(`Sitemap atualizado: ${rows.length} URLs indexáveis.`);
