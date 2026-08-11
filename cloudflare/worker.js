export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/data/status.json") {
      const status = await env.BORDALAS_STATUS.get("status.json");

      if (!status) {
        return new Response(
          JSON.stringify({
            error: "Dashboard telemetry not available yet"
          }),
          {
            status: 503,
            headers: {
              "content-type": "application/json; charset=utf-8",
              "cache-control": "no-store"
            }
          }
        );
      }

      return new Response(status, {
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "no-store"
        }
      });
    }

    return env.ASSETS.fetch(request);
  }
};
