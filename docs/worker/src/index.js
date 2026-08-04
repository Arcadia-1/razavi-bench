import { queryVisitStats, recordPageView } from "./analytics.js";

export { VisitStatsDurableObject } from "./analytics.js";

const INDEX_KEY = "direct_qa/index.json";
const TASKS_KEY = "tasks/tasks.jsonl";
const RAW_BASE = "https://raw.githubusercontent.com/Arcadia-1/razavi-bench/main";
const VISITOR_ID_PATTERN = /^[0-9a-f-]{36}$/i;

function apiHeaders(cacheControl = "no-store") {
  return {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Origin": "*",
    "Cache-Control": cacheControl,
    "Content-Type": "application/json",
  };
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS" && path.startsWith("/api/")) {
      return new Response(null, { status: 204, headers: apiHeaders() });
    }

    if (request.method === "POST" && path === "/api/hit") {
      const body = await request.json().catch(() => null);
      const visitorId = typeof body?.visitorId === "string" ? body.visitorId : "";
      if (!VISITOR_ID_PATTERN.test(visitorId)) {
        return Response.json({ error: "Invalid visitor ID" }, { status: 400, headers: apiHeaders() });
      }
      try {
        const stats = await recordPageView(env.VISIT_STATS, visitorId);
        return Response.json(stats, { headers: apiHeaders() });
      } catch (err) {
        return Response.json({ error: "Visit tracking unavailable" }, { status: 502, headers: apiHeaders() });
      }
    }

    if (request.method === "GET" && path === "/api/stats") {
      try {
        const stats = await queryVisitStats(env.VISIT_STATS);
        return Response.json(stats, { headers: apiHeaders("public, max-age=300") });
      } catch (err) {
        return Response.json({ error: "Visit stats unavailable" }, { status: 502, headers: apiHeaders() });
      }
    }

    // 数据接口
    if (request.method === "GET" && path === "/api/index.json") {
      try {
        const object = await env.BENCH_DATA.get(INDEX_KEY);
        if (object === null) {
          return new Response("Not found", { status: 404 });
        }
        const body = await object.arrayBuffer();
        return new Response(body, {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=60, s-maxage=60",
            "Access-Control-Allow-Origin": "*",
          },
        });
      } catch (err) {
        return new Response("Internal error", { status: 500 });
      }
    }

    // task 数据接口：/api/tasks.jsonl 从 R2 返回
    if (request.method === "GET" && path === "/api/tasks.jsonl") {
      try {
        const object = await env.BENCH_DATA.get(TASKS_KEY);
        if (object === null) {
          return new Response("Not found", { status: 404 });
        }
        const body = await object.arrayBuffer();
        return new Response(body, {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=300, s-maxage=300",
            "Access-Control-Allow-Origin": "*",
          },
        });
      } catch (err) {
        return new Response("Internal error", { status: 500 });
      }
    }

    // 图片代理：/figures/<path> 转发到 GitHub raw（figure 路径含 tasks/ 前缀）
    if (request.method === "GET" && path.startsWith("/figures/")) {
      const filePath = path.slice("/figures/".length);
      const upstreamUrl = RAW_BASE + "/" + filePath;
      try {
        const resp = await fetch(upstreamUrl);
        if (!resp.ok) {
          return new Response("Not found", { status: 404 });
        }
        const headers = new Headers(resp.headers);
        headers.set("Cache-Control", "public, max-age=86400, s-maxage=86400");
        headers.set("Access-Control-Allow-Origin", "*");
        return new Response(resp.body, {
          status: 200,
          headers,
        });
      } catch (err) {
        return new Response("Upstream error", { status: 502 });
      }
    }

    return new Response("Not found", { status: 404 });
  },
};
