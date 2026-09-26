const DAY_MS = 24 * 60 * 60 * 1000;
const STATS_CACHE_TTL_MS = 5 * 60 * 1000;
const VISITOR_HASH_PATTERN = /^[0-9a-f]{64}$/;
const COUNTRY_PATTERN = /^[A-Z]{2}$/;
const DURABLE_OBJECT_NAME = "global";

// The /analytics summary has the same shape and counting rules as Analog Design Bench's
// dashboard (site/analytics/worker.ts and routes.ts in that repository).
const RETAINED_DAYS = 400;
const SUMMARY_CACHE_KEY = -1;
const SITE_HOSTNAME = "razavi-bench.tokenzhang.com";

const CAMPAIGN_SOURCES = {
  google: "search:google",
  bing: "search:bing",
  baidu: "search:baidu",
  duckduckgo: "search:duckduckgo",
  yahoo: "search:yahoo",
  yandex: "search:yandex",
  wechat: "social:wechat",
  weixin: "social:wechat",
  wechat_moments: "social:wechat",
  "wechat-moments": "social:wechat",
  weixin_moments: "social:wechat",
  moments: "social:wechat",
  linkedin: "social:linkedin",
  twitter: "social:x",
  x: "social:x",
  facebook: "social:facebook",
  instagram: "social:instagram",
  reddit: "social:reddit",
  github: "social:github",
  zhihu: "social:zhihu",
  bilibili: "social:bilibili",
  xiaohongshu: "social:xiaohongshu",
  rednote: "social:xiaohongshu",
  email: "campaign:email",
  newsletter: "campaign:email",
  qr: "campaign:qr",
  qrcode: "campaign:qr",
  rss: "campaign:rss",
};

// Android apps report their package name as the referrer host.
const REFERRER_CATEGORIES = [
  ["search:bing", ["bing.com"]],
  ["search:baidu", ["baidu.com"]],
  ["search:duckduckgo", ["duckduckgo.com"]],
  ["search:yahoo", ["yahoo.com"]],
  ["search:yandex", ["yandex.com", "yandex.ru"]],
  ["search:ecosia", ["ecosia.org"]],
  ["search:naver", ["naver.com"]],
  ["search:sogou", ["sogou.com"]],
  ["search:360", ["so.com"]],
  ["social:wechat", ["weixin.qq.com", "weixin110.qq.com", "servicewechat.com", "wechat.com", "com.tencent.mm"]],
  ["social:linkedin", ["linkedin.com", "lnkd.in", "com.linkedin.android"]],
  ["social:x", ["x.com", "twitter.com", "t.co", "com.twitter.android"]],
  ["social:facebook", ["facebook.com", "fb.com"]],
  ["social:instagram", ["instagram.com"]],
  ["social:reddit", ["reddit.com", "redd.it"]],
  ["social:github", ["github.com"]],
  ["social:zhihu", ["zhihu.com"]],
  ["social:bilibili", ["bilibili.com"]],
  ["social:xiaohongshu", ["xiaohongshu.com", "xhslink.com"]],
];

export class VisitStatsDurableObject {
  constructor(ctx) {
    this.ctx = ctx;
    this.sql = ctx.storage.sql;

    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS visitors (
        visitor_hash TEXT PRIMARY KEY,
        last_seen_day INTEGER NOT NULL
      ) WITHOUT ROWID
    `);
    this.sql.exec(`
      CREATE INDEX IF NOT EXISTS idx_visitors_last_seen_day
      ON visitors(last_seen_day)
    `);
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS daily_views (
        day INTEGER PRIMARY KEY,
        views INTEGER NOT NULL
      )
    `);
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS stats_cache (
        days INTEGER PRIMARY KEY,
        computed_at INTEGER NOT NULL,
        pv INTEGER NOT NULL,
        uv INTEGER NOT NULL
      )
    `);
    // --- analytics dimension tables (added in the analytics expansion) ---
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS daily_uv (
        day INTEGER PRIMARY KEY,
        uv INTEGER NOT NULL
      )
    `);
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS hits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day INTEGER NOT NULL,
        visitor_hash TEXT,
        country TEXT,
        source TEXT,
        path TEXT
      )
    `);
    this.sql.exec(`
      CREATE INDEX IF NOT EXISTS idx_hits_day ON hits(day)
    `);
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS visitor_days (
        visitor_hash TEXT NOT NULL,
        day INTEGER NOT NULL,
        PRIMARY KEY (visitor_hash, day)
      ) WITHOUT ROWID
    `);
    // dimension totals cache (same expiry as stats_cache, keyed day=0)
    this.sql.exec(`
      CREATE TABLE IF NOT EXISTS analytics_cache (
        days INTEGER PRIMARY KEY,
        computed_at INTEGER NOT NULL,
        payload TEXT NOT NULL
      )
    `);
    // Whole-degree request location for the origins map, added after launch.
    for (const column of ["lat", "lng"]) {
      try {
        this.sql.exec(`ALTER TABLE hits ADD COLUMN ${column} INTEGER`);
      } catch (error) {
        if (!/duplicate column/i.test(String(error?.message))) throw error;
      }
    }
  }

  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/hit") {
      const body = await request.json().catch(() => null);
      const visitorHash = typeof body?.visitorHash === "string" ? body.visitorHash : "";
      if (!VISITOR_HASH_PATTERN.test(visitorHash)) {
        return Response.json({ error: "Invalid visitor hash" }, { status: 400 });
      }
      const country =
        typeof body?.country === "string" && COUNTRY_PATTERN.test(body.country)
          ? body.country
          : "";
      const source = typeof body?.source === "string" ? body.source.slice(0, 200) : "";
      const path = typeof body?.path === "string" ? body.path.slice(0, 500) : "";
      const lat = wholeDegrees(body?.lat, 90);
      const lng = wholeDegrees(body?.lng, 180);

      const now = Date.now();
      this.recordHit(visitorHash, country, source, path, lat, lng, now);
      return Response.json({ ...this.readStats(now), scope: "all" });
    }

    if (request.method === "GET" && url.pathname === "/stats") {
      const days = clampDays(url.searchParams.get("days"));
      return Response.json({ ...this.readStats(Date.now()), ...this.readDimensions(days) });
    }

    if (request.method === "GET" && url.pathname === "/analytics") {
      return Response.json(this.readAnalyticsSummary(Date.now()));
    }

    return Response.json({ error: "Not found" }, { status: 404 });
  }

  recordHit(visitorHash, country, source, path, lat, lng, now) {
    const today = utcDay(now);

    this.ctx.storage.transactionSync(() => {
      this.sql.exec(
        `
          INSERT INTO daily_views(day, views)
          VALUES (?, 1)
          ON CONFLICT(day) DO UPDATE SET views = views + 1
        `,
        today,
      );
      this.sql.exec(
        `
          INSERT INTO visitors(visitor_hash, last_seen_day)
          VALUES (?, ?)
          ON CONFLICT(visitor_hash) DO UPDATE SET last_seen_day = excluded.last_seen_day
          WHERE visitors.last_seen_day < excluded.last_seen_day
        `,
        visitorHash,
        today,
      );
      this.sql.exec(
        `
          INSERT OR IGNORE INTO visitor_days(visitor_hash, day)
          VALUES (?, ?)
        `,
        visitorHash,
        today,
      );
      this.sql.exec(
        `
          INSERT INTO hits(day, visitor_hash, country, source, path, lat, lng)
          VALUES (?, ?, ?, ?, ?, ?, ?)
        `,
        today,
        visitorHash,
        country || null,
        source || null,
        path || null,
        lat,
        lng,
      );
      this.sql.exec("DELETE FROM stats_cache");
      this.sql.exec("DELETE FROM analytics_cache");
    });
  }

  readStats(now) {
    const cached = this.sql
      .exec("SELECT computed_at, pv, uv FROM stats_cache WHERE days = 0")
      .toArray()[0];
    if (cached && now - Number(cached.computed_at) < STATS_CACHE_TTL_MS) {
      return { pv: Number(cached.pv), uv: Number(cached.uv) };
    }

    const { pv, uv } = this.computeStats();
    this.sql.exec(
      `
        INSERT INTO stats_cache(days, computed_at, pv, uv)
        VALUES (0, ?, ?, ?)
        ON CONFLICT(days) DO UPDATE SET
          computed_at = excluded.computed_at,
          pv = excluded.pv,
          uv = excluded.uv
      `,
      now,
      pv,
      uv,
    );
    return { pv, uv };
  }

  computeStats() {
    const pv = Number(
      this.sql
        .exec("SELECT COALESCE(SUM(views), 0) AS value FROM daily_views")
        .one().value,
    );
    const uv = Number(
      this.sql
        .exec("SELECT COUNT(*) AS value FROM visitors")
        .one().value,
    );
    return { pv, uv };
  }

  readAnalyticsSummary(now) {
    const cached = this.sql
      .exec("SELECT computed_at, payload FROM analytics_cache WHERE days = ?", SUMMARY_CACHE_KEY)
      .toArray()[0];
    if (cached && now - Number(cached.computed_at) < STATS_CACHE_TTL_MS) {
      return JSON.parse(cached.payload);
    }

    const today = utcDay(now);
    const firstDay = today - (RETAINED_DAYS - 1);
    const viewsByDay = new Map(
      this.sql
        .exec("SELECT day, views FROM daily_views WHERE day >= ?", firstDay)
        .toArray()
        .map((row) => [Number(row.day), Number(row.views)]),
    );
    const visitorsByDay = new Map(
      this.sql
        .exec("SELECT day, COUNT(*) AS visitors FROM visitor_days WHERE day >= ? GROUP BY day", firstDay)
        .toArray()
        .map((row) => [Number(row.day), Number(row.visitors)]),
    );
    const days = Array.from({ length: RETAINED_DAYS }, (_, index) => {
      const day = firstDay + index;
      return { date: utcDate(day), pv: viewsByDay.get(day) ?? 0, uv: visitorsByDay.get(day) ?? 0 };
    });

    // Every hit adds a page view to its country, source and page. Each visitor adds one
    // unique visitor, to the keys of their first hit. Hits of one visitor on one UTC day
    // keep the source of that day's first hit, in place of the 30-minute session cookie.
    const countries = new Map();
    const sources = new Map();
    const pages = new Map();
    const points = new Map();
    const counted = new Set();
    const sessions = new Map();
    let firstHitDay = null;
    for (const hit of this.sql.exec(
      "SELECT day, visitor_hash, country, source, path, lat, lng FROM hits ORDER BY id",
    )) {
      const path = trackedPath(hit.path);
      if (!path) continue;
      const day = Number(hit.day);
      if (firstHitDay === null) firstHitDay = day;
      const session = sessions.get(hit.visitor_hash);
      const source = session?.day === day ? session.source : acquisitionSource(hit.source);
      sessions.set(hit.visitor_hash, { day, source });
      const isNewVisitor = !counted.has(hit.visitor_hash);
      counted.add(hit.visitor_hash);
      const country = COUNTRY_PATTERN.test(hit.country ?? "") ? hit.country : "XX";
      tally(countries, country, isNewVisitor);
      tally(sources, source, isNewVisitor);
      tally(pages, path, isNewVisitor);
      // Only hits recorded with a location are mapped; older hits kept just the country.
      if (hit.lat != null && hit.lng != null) {
        const key = `${hit.lat},${hit.lng}`;
        points.set(key, (points.get(key) ?? 0) + 1);
      }
    }

    const pageViews = [...pages.values()].reduce((sum, row) => sum + row.pv, 0);
    const breakdownTotal = { pv: pageViews, uv: counted.size };
    const summary = {
      generatedAt: new Date(now).toISOString(),
      totals: this.computeStats(),
      today: days[days.length - 1],
      days,
      countries: breakdownRows(countries, "code"),
      points: [...points]
        .map(([key, count]) => {
          const [lat, lng] = key.split(",").map(Number);
          return { lat, lng, count };
        })
        .sort((a, b) => b.count - a.count)
        .slice(0, 2000),
      paths: breakdownRows(pages, "path"),
      sources: breakdownRows(sources, "source"),
      breakdownStartedAt: new Date((firstHitDay ?? today) * DAY_MS).toISOString(),
      breakdownTotals: { countries: breakdownTotal, sources: breakdownTotal, pages: breakdownTotal },
    };
    this.sql.exec(
      `
        INSERT INTO analytics_cache(days, computed_at, payload)
        VALUES (?, ?, ?)
        ON CONFLICT(days) DO UPDATE SET
          computed_at = excluded.computed_at,
          payload = excluded.payload
      `,
      SUMMARY_CACHE_KEY,
      now,
      JSON.stringify(summary),
    );
    return summary;
  }

  readDimensions(days) {
    const now = Date.now();
    const cached = this.sql
      .exec("SELECT computed_at, payload FROM analytics_cache WHERE days = ?", days)
      .toArray()[0];
    if (cached && now - Number(cached.computed_at) < STATS_CACHE_TTL_MS) {
      return JSON.parse(cached.payload);
    }

    const fromDay = utcDay(now) - (days - 1);
    const scope = days > 0 ? ` WHERE day >= ${fromDay}` : "";

    // daily PV/UV series (last `days` days, ascending)
    const dayTotals = {};
    this.sql
      .exec(`SELECT day, views FROM daily_views${scope} ORDER BY day ASC`)
      .toArray()
      .forEach((row) => {
        dayTotals[row.day] = { pv: Number(row.views), uv: 0 };
      });
    this.sql
      .exec(
        `SELECT day, COUNT(*) AS uv FROM visitor_days${scope} GROUP BY day ORDER BY day ASC`,
      )
      .toArray()
      .forEach((row) => {
        if (!dayTotals[row.day]) dayTotals[row.day] = { pv: 0, uv: 0 };
        dayTotals[row.day].uv = Number(row.uv);
      });
    const daily = Object.keys(dayTotals)
      .map(Number)
      .sort((a, b) => a - b)
      .map((day) => ({ day, pv: dayTotals[day].pv, uv: dayTotals[day].uv }));

    // today's stats
    const today = utcDay(now);
    const td = dayTotals[today] || { pv: 0, uv: 0 };

    // country aggregation
    const countryMap = {};
    this.sql
      .exec(
        `SELECT COALESCE(country, '') AS c, COUNT(*) AS views FROM hits${scope} GROUP BY c ORDER BY views DESC`,
      )
      .toArray()
      .forEach((row) => {
        if (row.c) countryMap[row.c] = (countryMap[row.c] || 0) + Number(row.views);
      });
    const origins = Object.keys(countryMap)
      .map((c) => ({ country: c, views: countryMap[c] }))
      .sort((a, b) => b.views - a.views);

    // per-region UV (distinct visitor_hash per country within scope) + PV
    const regionMap = {};
    this.sql
      .exec(
        `SELECT COALESCE(country, '') AS c, COUNT(DISTINCT visitor_hash) AS uv, COUNT(*) AS pv
         FROM hits${scope} GROUP BY c ORDER BY pv DESC`,
      )
      .toArray()
      .forEach((row) => {
        if (!row.c) return;
        regionMap[row.c] = {
          region: row.c,
          uv: Number(row.uv),
          pv: Number(row.pv),
        };
      });
    const regions = Object.values(regionMap).sort((a, b) => b.pv - a.pv);

    // source aggregation (blank -> direct)
    const sourceMap = {};
    this.sql
      .exec(
        `SELECT COALESCE(NULLIF(source, ''), 'direct') AS s, COUNT(DISTINCT visitor_hash) AS uv, COUNT(*) AS pv
         FROM hits${scope} GROUP BY s ORDER BY pv DESC`,
      )
      .toArray()
      .forEach((row) => {
        sourceMap[row.s] = { source: row.s, uv: Number(row.uv), pv: Number(row.pv) };
      });
    const sources = Object.values(sourceMap).sort((a, b) => b.pv - a.pv);

    // path aggregation (empty -> "/")
    const pageMap = {};
    this.sql
      .exec(
        `SELECT COALESCE(NULLIF(path, ''), '/') AS p, COUNT(DISTINCT visitor_hash) AS uv, COUNT(*) AS pv
         FROM hits${scope} GROUP BY p ORDER BY pv DESC`,
      )
      .toArray()
      .forEach((row) => {
        pageMap[row.p] = { path: row.p, uv: Number(row.uv), pv: Number(row.pv) };
      });
    const pages = Object.values(pageMap).sort((a, b) => b.pv - a.pv);

    const payload = { pvToday: td.pv, uvToday: td.uv, daily, origins, regions, sources, pages };
    this.sql.exec(
      `
        INSERT INTO analytics_cache(days, computed_at, payload)
        VALUES (?, ?, ?)
        ON CONFLICT(days) DO UPDATE SET
          computed_at = excluded.computed_at,
          payload = excluded.payload
      `,
      days,
      now,
      JSON.stringify(payload),
    );
    return payload;
  }
}

export async function recordPageView(namespace, visitorId, details) {
  const visitorHash = await hashVisitorId(visitorId);
  const stub = namespace.get(namespace.idFromName(DURABLE_OBJECT_NAME));
  const response = await stub.fetch("https://visit-stats.internal/hit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      visitorHash,
      country: details?.country ?? "",
      source: details?.source ?? "",
      path: details?.path ?? "",
      lat: details?.lat ?? null,
      lng: details?.lng ?? null,
    }),
  });
  if (!response.ok) throw new Error(`Visit tracking failed (${response.status})`);
  return response.json();
}

export async function queryVisitStats(namespace, days) {
  const stub = namespace.get(namespace.idFromName(DURABLE_OBJECT_NAME));
  const url = days > 0 ? `https://visit-stats.internal/stats?days=${days}` : "https://visit-stats.internal/stats";
  const response = await stub.fetch(url);
  if (!response.ok) throw new Error(`Visit stats failed (${response.status})`);
  return response.json();
}

export async function queryAnalyticsSummary(namespace) {
  const stub = namespace.get(namespace.idFromName(DURABLE_OBJECT_NAME));
  const response = await stub.fetch("https://visit-stats.internal/analytics");
  if (!response.ok) throw new Error(`Analytics summary failed (${response.status})`);
  return response.json();
}

function utcDay(timestamp) {
  return Math.floor(timestamp / DAY_MS);
}

function utcDate(day) {
  return new Date(day * DAY_MS).toISOString().slice(0, 10);
}

// A latitude or longitude (Cloudflare sends strings) rounded to a whole degree, or null.
function wholeDegrees(value, limit) {
  const degrees = typeof value === "number" ? value : Number.parseFloat(value);
  return Number.isFinite(degrees) && Math.abs(degrees) <= limit ? Math.round(degrees) : null;
}

// Pages the dashboard lists: API calls and the dashboard itself are left out.
function trackedPath(raw) {
  let path = (typeof raw === "string" && raw ? raw : "/").split("?")[0].split("#")[0];
  if (!path.startsWith("/")) return null;
  if (path.length > 120) path = path.slice(0, 120);
  if (path.startsWith("/api/") || path.startsWith("/analytics")) return null;
  return path;
}

// Hits store a utm_source value or the referrer's hostname ("direct" when there was none).
function acquisitionSource(raw) {
  const value = typeof raw === "string" ? raw.trim().toLowerCase() : "";
  if (!value || value === "direct") return "direct-or-unknown";
  if (!value.includes(".")) {
    if (!/^[a-z0-9._-]{1,40}$/.test(value)) return "campaign:other";
    return CAMPAIGN_SOURCES[value] ?? "campaign:other";
  }
  const hostname = value.replace(/^www\./, "").replace(/\.$/, "");
  if (hostname === SITE_HOSTNAME) return "direct-or-unknown";
  if (/^google\.[a-z.]+$/.test(hostname)) return "search:google";
  for (const [source, domains] of REFERRER_CATEGORIES) {
    if (domains.some((domain) => hostname === domain || hostname.endsWith(`.${domain}`))) return source;
  }
  return /^[a-z0-9.-]{1,100}$/.test(hostname) ? `ref:${hostname}` : "ref:other";
}

function tally(rows, key, isNewVisitor) {
  const row = rows.get(key) ?? { pv: 0, uv: 0 };
  row.pv += 1;
  if (isNewVisitor) row.uv += 1;
  rows.set(key, row);
}

function breakdownRows(rows, field) {
  return [...rows]
    .map(([key, row]) => ({ [field]: key, pv: row.pv, uv: row.uv }))
    .sort((a, b) => b.pv - a.pv || b.uv - a.uv);
}

function clampDays(raw) {
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n) || n < 1) return 0;
  return Math.min(n, 365);
}

async function hashVisitorId(visitorId) {
  const bytes = new TextEncoder().encode(visitorId);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}
