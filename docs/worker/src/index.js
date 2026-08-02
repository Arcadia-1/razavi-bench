const INDEX_KEY = "direct_qa/index.json";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

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

    return new Response("Not found", { status: 404 });
  },
};
