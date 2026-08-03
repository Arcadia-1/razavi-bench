const DAY_MS = 24 * 60 * 60 * 1000;
const STATS_CACHE_TTL_MS = 5 * 60 * 1000;
const VISITOR_HASH_PATTERN = /^[0-9a-f]{64}$/;
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
  }

  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/hit") {
      const body = await request.json().catch(() => null);
      const visitorHash = typeof body?.visitorHash === "string" ? body.visitorHash : "";
      if (!VISITOR_HASH_PATTERN.test(visitorHash)) {
        return Response.json({ error: "Invalid visitor hash" }, { status: 400 });
      }

      const now = Date.now();
      this.recordHit(visitorHash, now);
      return Response.json({ ...this.readStats(now), scope: "all" });
    }

    if (request.method === "GET" && url.pathname === "/stats") {
      return Response.json({ ...this.readStats(Date.now()), scope: "all" });
    }

    return Response.json({ error: "Not found" }, { status: 404 });
  }

  recordHit(visitorHash, now) {
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
      this.sql.exec("DELETE FROM stats_cache");
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

}

export async function recordPageView(namespace, visitorId) {
  const visitorHash = await hashVisitorId(visitorId);
  const stub = namespace.get(namespace.idFromName(DURABLE_OBJECT_NAME));
  const response = await stub.fetch("https://visit-stats.internal/hit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ visitorHash }),
  });
  if (!response.ok) throw new Error(`Visit tracking failed (${response.status})`);
  return response.json();
}

export async function queryVisitStats(namespace) {
  const stub = namespace.get(namespace.idFromName(DURABLE_OBJECT_NAME));
  const response = await stub.fetch("https://visit-stats.internal/stats");
  if (!response.ok) throw new Error(`Visit stats failed (${response.status})`);
  return response.json();
}

function utcDay(timestamp) {
  return Math.floor(timestamp / DAY_MS);
}

async function hashVisitorId(visitorId) {
  const bytes = new TextEncoder().encode(visitorId);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}
