// BABYLON / STEMIT progress widget for Scriptable (iOS).
//
// Reads babylon-status.json that `ix_crate phone-status` (or BABYLON itself)
// writes to your iCloud Drive. Nothing leaves your Apple ID: no server, no
// listener on the Mac. Setup: docs/crate.md → "BABYLON on iPhone".
//
// Looks in Scriptable's iCloud folder (ix/babylon-status.json), then a
// Scriptable file bookmark named "ix" (Settings → File Bookmarks → iCloud Drive/ix).

const VERSION = "v4";
const STATUS_NAME = "babylon-status.json";
const CACHE_NAME = "babylon-status-cache.json";
const STALE_MIN = 10;
const REFRESH_MIN = 5;

const BG = new Color("#111318");
const FG = new Color("#f2f2f2");
const DIM = new Color("#9aa0a6");
const OK = new Color("#34c759");
const WARN = new Color("#ff9f0a");
const BAD = new Color("#ff453a");

function newer(a, b) {
  if (!a) return b;
  if (!b) return a;
  return Date.parse(a.updated_at) >= Date.parse(b.updated_at) ? a : b;
}

// Widgets sometimes cannot pull from iCloud; keep the last good copy on the phone.
async function readStatus() {
  const local = FileManager.local();
  const cachePath = local.joinPath(local.cacheDirectory(), CACHE_NAME);
  let cached = null;
  try {
    if (local.fileExists(cachePath)) cached = JSON.parse(local.readString(cachePath));
  } catch (e) {
    cached = null;
  }
  const fresh = await readICloud();
  const best = newer(fresh, cached);
  if (best && best === fresh) {
    try {
      local.writeString(cachePath, JSON.stringify(fresh));
    } catch (e) {
      // cache is best-effort
    }
  }
  return best;
}

async function readICloud() {
  const fm = FileManager.iCloud();
  const paths = [fm.joinPath(fm.joinPath(fm.documentsDirectory(), "ix"), STATUS_NAME)];
  if (fm.bookmarkExists("ix")) {
    paths.push(fm.joinPath(fm.bookmarkedPath("ix"), STATUS_NAME));
  }
  for (const path of paths) {
    try {
      // Not-yet-downloaded iCloud files are placeholders that fileExists()
      // misses, so always ask iCloud first.
      await fm.downloadFileFromiCloud(path);
      if (fm.fileExists(path)) return JSON.parse(fm.readString(path));
    } catch (e) {
      // try the next location
    }
  }
  return null;
}

function minutesAgo(iso) {
  const t = Date.parse(iso);
  return Number.isNaN(t) ? null : Math.max(0, (Date.now() - t) / 60000);
}

function fmtMin(min) {
  if (min == null) return "";
  if (min < 1) return "<1 min";
  if (min < 90) return `${Math.round(min)} min`;
  return `${(min / 60).toFixed(1)} h`;
}

function view(s) {
  if (!s) {
    return {
      state: "no data",
      color: DIM,
      title: "BABYLON",
      phase: "No status file yet",
      passes: "Start BABYLON on the Mac",
      summary: `Looking in Scriptable/ix and bookmark "ix" (${VERSION})`,
      updated: VERSION,
      pct: 0,
    };
  }
  const ago = minutesAgo(s.updated_at);
  let state = s.state;
  let color = state === "done" ? OK : state === "running" ? OK : state === "failed" ? BAD : WARN;
  if (state === "running" && ago != null && ago > STALE_MIN) {
    state = "iCloud behind";
    color = WARN;
  }
  const p = s.passes || {};
  const ph = s.phase || {};
  let pct = 0;
  if (p.total) pct = p.done / p.total;
  else if (ph.total) pct = Math.max(ph.index - 1, 0) / ph.total;
  if (s.state === "done") pct = 1;

  const phase = ph.total ? `${ph.index}/${ph.total} ${ph.name}` : ph.name || "";
  const passes = p.total ? `${p.done}/${p.total} passes${p.failed ? ` · ${p.failed} fail` : ""}` : s.step || "";
  const track = s.track ? `${s.track}${s.track_pct != null ? `  ${s.track_pct}%` : ""}` : "";
  const eta = s.state === "running" && s.eta_min != null ? `ETA ${fmtMin(s.eta_min)}` : "";
  const updated = ago != null ? `Mac update ${fmtMin(ago)} ago · ${VERSION}` : VERSION;
  return {
    state,
    color,
    title: s.title || "BABYLON",
    phase,
    passes,
    track,
    eta,
    updated,
    summary: s.summary || "",
    pct,
  };
}

function bar(pct, width, height, color) {
  const ctx = new DrawContext();
  ctx.size = new Size(width, height);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  const track = new Path();
  track.addRoundedRect(new Rect(0, 0, width, height), height / 2, height / 2);
  ctx.addPath(track);
  ctx.setFillColor(new Color("#2c2f36"));
  ctx.fillPath();
  const w = Math.max(height, width * Math.min(Math.max(pct, 0), 1));
  const fill = new Path();
  fill.addRoundedRect(new Rect(0, 0, w, height), height / 2, height / 2);
  ctx.addPath(fill);
  ctx.setFillColor(color);
  ctx.fillPath();
  return ctx.getImage();
}

function text(stack, value, size, color, { bold = false, lines = 1 } = {}) {
  if (!value) return null;
  const t = stack.addText(value);
  t.font = bold ? Font.boldSystemFont(size) : Font.systemFont(size);
  t.textColor = color;
  t.lineLimit = lines;
  t.minimumScaleFactor = 0.7;
  return t;
}

function homeWidget(v, family) {
  const w = new ListWidget();
  w.backgroundColor = BG;
  w.setPadding(12, 14, 12, 14);
  const head = w.addStack();
  head.centerAlignContent();
  text(head, v.title, 13, FG, { bold: true });
  head.addSpacer();
  text(head, v.state, 11, v.color, { bold: true });
  w.addSpacer(6);
  text(w, v.phase, 12, FG);
  text(w, v.passes, 12, DIM);
  w.addSpacer(6);
  const barWidth = family === "small" ? 130 : 290;
  w.addImage(bar(v.pct, barWidth, 6, v.color));
  w.addSpacer(6);
  text(w, v.track || v.summary, 11, FG, { lines: family === "small" ? 2 : 1 });
  w.addSpacer();
  const foot = w.addStack();
  text(foot, v.eta, 10, DIM);
  foot.addSpacer();
  text(foot, v.updated, 10, DIM);
  return w;
}

function lockWidget(v, family) {
  const w = new ListWidget();
  if (family === "accessoryInline") {
    text(w, `${v.title} ${Math.round(v.pct * 100)}% ${v.eta || v.state}`, 12, FG);
    return w;
  }
  if (family === "accessoryCircular") {
    text(w, `${Math.round(v.pct * 100)}%`, 14, FG, { bold: true });
    text(w, v.state, 9, FG);
    return w;
  }
  text(w, `${v.title} · ${v.state}`, 13, FG, { bold: true });
  text(w, v.passes || v.phase, 12, FG);
  text(w, v.eta ? `${v.eta} · ${VERSION}` : v.updated, 11, FG);
  return w;
}

const status = await readStatus();
const v = view(status);
const family = config.widgetFamily || "medium";
const widget = family.startsWith("accessory") ? lockWidget(v, family) : homeWidget(v, family);
widget.refreshAfterDate = new Date(Date.now() + REFRESH_MIN * 60000);

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  await widget.presentMedium();
}
Script.complete();
