const INDEX_KEY = "direct_qa/index.json";
const RAW_BASE = "https://raw.githubusercontent.com/Arcadia-1/razavi-bench/main";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

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
