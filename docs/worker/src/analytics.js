const DAY_MS = 24 * 60 * 60 * 1000;
const STATS_CACHE_TTL_MS = 5 * 60 * 1000;
const VISITOR_HASH_PATTERN = /^[0-9a-f]{64}$/;
const COUNTRY_PATTERN = /^[A-Z]{2}$/;
const DURABLE_OBJECT_NAME = "global";

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

      const now = Date.now();
      this.recordHit(visitorHash, country, source, path, now);
      return Response.json({ ...this.readStats(now), scope: "all" });
    }

    if (request.method === "GET" && url.pathname === "/stats") {
      const days = clampDays(url.searchParams.get("days"));
      return Response.json({ ...this.readStats(Date.now()), ...this.readDimensions(days) });
    }

    return Response.json({ error: "Not found" }, { status: 404 });
  }

  recordHit(visitorHash, country, source, path, now) {
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
          INSERT INTO hits(day, visitor_hash, country, source, path)
          VALUES (?, ?, ?, ?, ?)
        `,
        today,
        visitorHash,
        country || null,
        source || null,
        path || null,
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

function utcDay(timestamp) {
  return Math.floor(timestamp / DAY_MS);
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
