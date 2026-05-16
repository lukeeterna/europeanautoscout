// CF Pages Function: dynamic route /contract/<token>
// Static assets (sign.js, thank-you.html, index.html, /) hanno precedence:
// la function viene chiamata SOLO per path non matching file statici.
// S178 2026-05-16: workaround _redirects splat/`:param` broken.

export async function onRequest(context) {
  const { params, request, env, next } = context;
  const token = (params.token || '').toLowerCase();
  // Pass-through static assets (sign.js, thank-you.html, etc.)
  if (token.includes('.')) {
    return next();
  }
  if (!/^[a-f0-9]{32}$/.test(token)) {
    return new Response('Contract token non valido.', {
      status: 404,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
    });
  }
  const url = new URL(request.url);
  return Response.redirect(`${url.origin}/contract/?token=${token}`, 302);
}
