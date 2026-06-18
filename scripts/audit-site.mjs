import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const domain = "https://www.calculesuasaude.com.br";

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

function rel(file) {
  return path.relative(root, file).replaceAll("\\", "/");
}

function attr(tag, name) {
  const match = tag.match(new RegExp(`\\b${name}\\s*=\\s*(["'])(.*?)\\1`, "is"));
  return match ? match[2].trim() : "";
}

function first(html, pattern) {
  const match = html.match(pattern);
  return match ? match[1].replace(/\s+/g, " ").trim() : "";
}

function metaTag(html, name) {
  return [...html.matchAll(/<meta\b[^>]*>/gi)].find(
    (match) => attr(match[0], "name").toLowerCase() === name.toLowerCase(),
  )?.[0] || "";
}

function isNoindex(html) {
  return /\bnoindex\b/i.test(attr(metaTag(html, "robots"), "content"));
}

function stripUrl(value) {
  return value.split("#")[0].split("?")[0];
}

function localTarget(sourceFile, value) {
  if (
    !value ||
    value.startsWith("#") ||
    value.startsWith("mailto:") ||
    value.startsWith("tel:") ||
    value.startsWith("data:") ||
    value.startsWith("javascript:")
  ) {
    return null;
  }

  let clean = stripUrl(value);
  try {
    clean = decodeURIComponent(clean);
  } catch {
    return { invalidEncoding: true, value };
  }

  if (/^https?:\/\//i.test(clean)) {
    if (!clean.startsWith(domain)) return null;
    clean = clean.slice(domain.length) || "/";
  } else if (/^\/\//.test(clean)) {
    return null;
  }

  if (clean === "/") return path.join(root, "index.html");
  if (clean.startsWith("/")) return path.join(root, clean.slice(1));
  return path.resolve(path.dirname(sourceFile), clean);
}

function expectedCanonical(file) {
  const fileRel = rel(file);
  return fileRel === "index.html" ? `${domain}/` : `${domain}/${fileRel}`;
}

const files = walk(root);
const htmlFiles = files.filter((file) => {
  if (!file.endsWith(".html")) return false;
  const relative = rel(file);
  return !relative.startsWith("scripts/");
});
const knownFiles = new Set(files.map((file) => path.normalize(file).toLowerCase()));
const errors = [];
const warnings = [];
const stats = {
  html: htmlFiles.length,
  localReferences: 0,
  jsonLd: 0,
  images: 0,
};
const titleOwners = new Map();
const descriptionOwners = new Map();
const canonicalOwners = new Map();
const pageData = new Map();
const languageWords = {
  pt: [" para ", " que ", " uma ", " com ", " saúde ", " não ", " você ", " dos ", " das ", " tratamento ", " sintomas "],
  es: [" para ", " que ", " una ", " con ", " salud ", " también ", " usted ", " los ", " las ", " tratamiento ", " síntomas "],
  en: [" the ", " and ", " for ", " with ", " health ", " you ", " about ", " this ", " treatment ", " symptoms ", " from ", " are "],
};

function report(bucket, code, file, detail) {
  bucket.push({ code, file: rel(file), detail });
}

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, "utf8");
  const activeHtml = html.replace(/<!--[\s\S]*?-->/g, "");
  const noindex = isNoindex(activeHtml);
  const title = first(html, /<title[^>]*>([\s\S]*?)<\/title>/i);
  const description = first(
    html,
    /<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["'][^>]*>/i,
  ) || first(
    html,
    /<meta[^>]+content=["']([^"']*)["'][^>]+name=["']description["'][^>]*>/i,
  );
  const lang = first(html, /<html[^>]+lang=["']([^"']+)["']/i);
  const canonicalTag = activeHtml.match(/<link[^>]+rel=["']canonical["'][^>]*>/i)?.[0] || "";
  const canonical = attr(canonicalTag, "href");
  const h1Count = (activeHtml.match(/<h1\b/gi) || []).length;
  stats.noindex = (stats.noindex || 0) + (noindex ? 1 : 0);
  pageData.set(path.normalize(file).toLowerCase(), { canonical, noindex });

  if (!title) report(errors, "missing-title", file, "Página sem <title>.");
  if (!description) report(errors, "missing-description", file, "Página sem meta description.");
  if (!lang) report(errors, "missing-lang", file, "Página sem idioma no elemento <html>.");
  if (!noindex && !canonical) report(errors, "missing-canonical", file, "Página indexável sem canonical.");
  if (!noindex && canonical && canonical !== expectedCanonical(file)) {
    report(warnings, "canonical-mismatch", file, `${canonical} != ${expectedCanonical(file)}`);
  }
  if (h1Count !== 1) report(errors, "h1-count", file, `Encontrados ${h1Count} elementos <h1>.`);

  if (!noindex && title) {
    if (!titleOwners.has(title)) titleOwners.set(title, []);
    titleOwners.get(title).push(file);
  }
  if (!noindex && description) {
    if (!descriptionOwners.has(description)) descriptionOwners.set(description, []);
    descriptionOwners.get(description).push(file);
  }
  if (!noindex && canonical) {
    if (!canonicalOwners.has(canonical)) canonicalOwners.set(canonical, []);
    canonicalOwners.get(canonical).push(file);
  }

  const ids = [...activeHtml.matchAll(/\bid\s*=\s*(["'])(.*?)\1/gi)].map((match) => match[2]);
  const duplicateIds = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
  if (duplicateIds.length) {
    report(errors, "duplicate-id", file, duplicateIds.join(", "));
  }

  for (const match of activeHtml.matchAll(/<(?:a|link|script|img|source)\b[^>]*>/gi)) {
    const tag = match[0];
    const value = attr(tag, tag.startsWith("<a") || tag.startsWith("<link") ? "href" : "src");
    const target = localTarget(file, value);
    if (!target) continue;
    stats.localReferences += 1;
    if (target.invalidEncoding) {
      report(errors, "invalid-url-encoding", file, value);
      continue;
    }
    if (!knownFiles.has(path.normalize(target).toLowerCase()) && !fs.existsSync(target)) {
      report(errors, "broken-local-reference", file, value);
    }
  }

  for (const match of activeHtml.matchAll(/<img\b[^>]*>/gi)) {
    stats.images += 1;
    const tag = match[0];
    if (!/\balt\s*=/i.test(tag)) report(errors, "image-missing-alt", file, attr(tag, "src"));
    if (attr(tag, "src") && (!/\bwidth\s*=/i.test(tag) || !/\bheight\s*=/i.test(tag))) {
      report(warnings, "image-missing-dimensions", file, attr(tag, "src"));
    }
  }

  for (const match of activeHtml.matchAll(/<a\b[^>]*target=["']_blank["'][^>]*>/gi)) {
    const relValue = attr(match[0], "rel");
    if (!/\bnoopener\b/i.test(relValue)) {
      report(warnings, "blank-link-without-noopener", file, attr(match[0], "href"));
    }
  }

  if (/data-ad-slot=["']YOUR_SLOT_HERE["']/i.test(activeHtml)) {
    report(errors, "placeholder-ad-slot", file, "Substitua pelo ID real do bloco ou remova o anúncio.");
  }

  for (const match of activeHtml.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    stats.jsonLd += 1;
    try {
      JSON.parse(match[1]);
    } catch (error) {
      report(errors, "invalid-json-ld", file, error.message);
    }
  }

  for (const match of activeHtml.matchAll(/<a\b[^>]*href\s*=\s*(["'])(.*?)\1[^>]*>/gi)) {
    const value = match[2];
    if (!value.includes("#") || value === "#") continue;
    const [targetValue, fragmentValue] = value.split("#");
    if (!fragmentValue || /^https?:/i.test(targetValue)) continue;
    let fragment;
    try {
      fragment = decodeURIComponent(fragmentValue);
    } catch {
      continue;
    }
    const target = targetValue ? localTarget(file, targetValue) : file;
    if (!target || target.invalidEncoding || !fs.existsSync(target)) continue;
    const targetHtml = target === file ? activeHtml : fs.readFileSync(target, "utf8").replace(/<!--[\s\S]*?-->/g, "");
    const escaped = fragment.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (!new RegExp(`\\b(?:id|name)\\s*=\\s*(["'])${escaped}\\1`, "i").test(targetHtml)) {
      report(errors, "broken-fragment", file, value);
    }
  }

  if (!noindex && /^(es|en)/i.test(lang)) {
    const visibleText = activeHtml
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .toLowerCase()
      .replace(/\s+/g, " ");
    const scores = Object.fromEntries(
      Object.entries(languageWords).map(([language, words]) => [
        language,
        words.reduce((score, word) => score + visibleText.split(word).length - 1, 0),
      ]),
    );
    const expected = lang.toLowerCase().startsWith("es") ? "es" : "en";
    const [detected, detectedScore] = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
    if (detected !== expected && detectedScore > scores[expected] * 1.35) {
      report(warnings, "language-mismatch", file, `lang=${lang}; pontuação ${JSON.stringify(scores)}`);
    }
  }
}

for (const [title, owners] of titleOwners) {
  if (owners.length > 1) {
    report(warnings, "duplicate-title", owners[0], `${owners.length} páginas: ${title}`);
  }
}
for (const [description, owners] of descriptionOwners) {
  if (owners.length > 1) {
    report(warnings, "duplicate-description", owners[0], `${owners.length} páginas: ${description}`);
  }
}
for (const [canonical, owners] of canonicalOwners) {
  if (owners.length > 1) {
    report(errors, "duplicate-canonical", owners[0], `${owners.length} páginas: ${canonical}`);
  }
}

const sitemapPath = path.join(root, "sitemap.xml");
if (fs.existsSync(sitemapPath)) {
  const sitemap = fs.readFileSync(sitemapPath, "utf8");
  const urls = [...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map((match) => match[1].trim());
  const seen = new Set();
  for (const url of urls) {
    if (seen.has(url)) report(errors, "duplicate-sitemap-url", sitemapPath, url);
    seen.add(url);
    const target = localTarget(sitemapPath, url);
    if (target && !fs.existsSync(target)) {
      report(errors, "sitemap-missing-file", sitemapPath, url);
      continue;
    }
    if (target) {
      const data = pageData.get(path.normalize(target).toLowerCase());
      if (data?.noindex) report(errors, "sitemap-noindex-url", sitemapPath, url);
      if (data?.canonical && data.canonical !== url) {
        report(errors, "sitemap-canonical-mismatch", sitemapPath, `${url} -> ${data.canonical}`);
      }
    }
  }
  stats.sitemapUrls = urls.length;
}

function printSection(name, items) {
  console.log(`\n${name}: ${items.length}`);
  const grouped = new Map();
  for (const item of items) {
    if (!grouped.has(item.code)) grouped.set(item.code, []);
    grouped.get(item.code).push(item);
  }
  for (const [code, group] of [...grouped].sort(([a], [b]) => a.localeCompare(b))) {
    console.log(`  ${code}: ${group.length}`);
    for (const item of group.slice(0, 12)) {
      console.log(`    - ${item.file}: ${item.detail}`);
    }
    if (group.length > 12) console.log(`    ... e mais ${group.length - 12}`);
  }
}

console.log("AUDITORIA DO SITE");
console.log(JSON.stringify(stats, null, 2));
printSection("ERROS", errors);
printSection("AVISOS", warnings);
process.exitCode = errors.length ? 1 : 0;
