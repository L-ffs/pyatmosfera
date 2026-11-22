// Pequeno cliente da API: manda JSON, usa o cookie de sessão e devolve { status, data }.
async function api(path, options) {
  options = options || {};
  var init = { method: options.method || "GET", headers: {}, credentials: "same-origin" };
  if (options.body !== undefined) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  var response = await fetch(path, init);
  var data = {};
  try { data = await response.json(); } catch (e) { /* resposta sem corpo */ }
  return { status: response.status, ok: response.ok, data: data };
}

// Cria o texto de erro padrão a partir da resposta da API.
function apiError(result) {
  return (result.data && result.data.error) || "Algo deu errado. Tente novamente.";
}
