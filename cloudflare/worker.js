function unauthorized() {
  return new Response("Acceso restringido - Bordalas IA", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Bordalas IA"',
      "Cache-Control": "no-store"
    }
  });
}

function authorized(request, env) {
  const header = request.headers.get("Authorization");

  if (!header || !header.startsWith("Basic ")) {
    return false;
  }

  try {
    const decoded = atob(header.substring(6));
    const separator = decoded.indexOf(":");

    if (separator === -1) {
      return false;
    }

    const username = decoded.substring(0, separator);
    const password = decoded.substring(separator + 1);

    return (
      username === env.DASHBOARD_USERNAME &&
      password === env.DASHBOARD_PASSWORD
    );
  } catch {
    return false;
  }
}

export default {
  async fetch(request, env) {
    if (!authorized(request, env)) {
      return unauthorized();
    }

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
