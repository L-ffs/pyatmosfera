// ── Elementos ───────────────────────────────────────────────
var cityList = document.getElementById("city-list");
var errorEl = document.getElementById("error");
var accountName = document.getElementById("account-name");
var searchInput = document.getElementById("search-input");
var searchResults = document.getElementById("search-results");
var searchMsg = document.getElementById("search-msg");

var favoriteKeys = {};   // chaves das cidades já favoritadas
var searchTimer = null;
var searchSeq = 0;       // descarta respostas antigas da busca

function el(tag, className, text) {
  var node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function goToLogin() { window.location.href = "/"; }

function showError(message) { errorEl.textContent = message || ""; }

// Respostas 401 significam sessão expirada: volta para o login.
function guard(result) {
  if (result.status === 401) { goToLogin(); return false; }
  return true;
}

// ── Ícones e formatação ─────────────────────────────────────
function iconFor(code, isDay) {
  if (code === 0) return isDay ? "☀️" : "🌙";
  if (code === 1 || code === 2) return isDay ? "🌤️" : "☁️";
  if (code === 3) return "☁️";
  if (code === 45 || code === 48) return "🌫️";
  if (code >= 51 && code <= 57) return "🌦️";
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) return "🌧️";
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "❄️";
  if (code >= 95) return "⛈️";
  return "🌡️";
}

function round(n) { return Math.round(n); }

function weekday(dateText, index) {
  if (index === 0) return "Hoje";
  return new Date(dateText + "T12:00:00").toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "");
}

function placeText(city) {
  return [city.state, city.country].filter(Boolean).join(" — ");
}

// ── Cartões de clima (RF5) ──────────────────────────────────
function buildCard(item) {
  var card = el("article", "card weather-card");
  var city = item.city;

  var top = el("div", "weather-top");
  var title = el("div");
  title.appendChild(el("div", "city-name", city.name));
  title.appendChild(el("div", "city-place", placeText(city)));
  var remove = el("button", "remove", "×");
  remove.type = "button";
  remove.title = "Remover " + city.name + " dos favoritos";
  remove.setAttribute("aria-label", remove.title);
  remove.addEventListener("click", function () { removeCity(city, card); });
  top.appendChild(title);
  top.appendChild(remove);
  card.appendChild(top);

  if (item.error || !item.current) {
    card.classList.add("unavailable");
    card.appendChild(el("p", "unavailable-text", "Clima indisponível no momento."));
    return card;
  }

  var current = item.current;
  var now = el("div", "now");
  now.appendChild(el("div", "now-icon", iconFor(current.weathercode, current.is_day)));
  var temp = el("div", "temp", String(round(current.temperature)));
  temp.appendChild(el("small", "", " °C"));
  var text = el("div");
  text.appendChild(temp);
  text.appendChild(el("div", "condition", current.condition));
  now.appendChild(text);
  card.appendChild(now);

  var details = el("div", "details");
  details.appendChild(el("span", "", "Vento " + round(current.windspeed) + " km/h"));
  if (item.daily && item.daily.length) {
    var today = item.daily[0];
    details.appendChild(el("span", "", "Mín " + round(today.temp_min) + "° · Máx " + round(today.temp_max) + "°"));
  }
  card.appendChild(details);

  if (item.daily && item.daily.length > 1) {
    var list = el("ul", "forecast hidden");
    item.daily.forEach(function (day, i) {
      var li = el("li");
      li.appendChild(el("span", "day", weekday(day.date, i)));
      li.appendChild(el("span", "", iconFor(day.weathercode, true)));
      li.appendChild(el("span", "", day.condition));
      li.appendChild(el("span", "range", round(day.temp_min) + "° / " + round(day.temp_max) + "°"));
      list.appendChild(li);
    });
    var more = el("button", "more", "Ver próximos dias");
    more.type = "button";
    more.setAttribute("aria-expanded", "false");
    more.addEventListener("click", function () {
      var open = list.classList.toggle("hidden") === false;
      more.textContent = open ? "Ocultar próximos dias" : "Ver próximos dias";
      more.setAttribute("aria-expanded", String(open));
    });
    card.appendChild(more);
    card.appendChild(list);
  }
  return card;
}

async function loadFavorites() {
  showError("");
  try {
    var result = await api("/api/weather/favorites");
    if (!guard(result)) return;
    if (!result.ok) { cityList.replaceChildren(); showError(apiError(result)); return; }

    var items = result.data.cities || [];
    favoriteKeys = {};
    items.forEach(function (item) { favoriteKeys[item.city.key] = true; });

    cityList.replaceChildren();
    if (items.length === 0) {
      cityList.appendChild(el("p", "empty", "Você ainda não favoritou nenhuma cidade. Pesquise uma acima para ver o clima dela aqui."));
      return;
    }
    items.forEach(function (item) { cityList.appendChild(buildCard(item)); });
  } catch (e) {
    cityList.replaceChildren();
    showError("Não foi possível conectar ao servidor.");
  }
}

// ── Remover favorita (RF6) ──────────────────────────────────
async function removeCity(city, card) {
  if (!window.confirm("Remover " + city.name + " dos favoritos?")) return;
  card.style.opacity = ".5";
  card.style.pointerEvents = "none";
  try {
    var result = await api("/api/favorites/" + encodeURIComponent(city.key), { method: "DELETE" });
    if (!guard(result)) return;
    if (result.ok || result.status === 404) { loadFavorites(); return; }
    showError(apiError(result));
  } catch (e) {
    showError("Não foi possível remover a cidade.");
  }
  card.style.opacity = "";
  card.style.pointerEvents = "";
}

// ── Pesquisar (RF3) e favoritar (RF4) ───────────────────────
function clearSearch() {
  searchResults.replaceChildren();
  searchResults.classList.add("hidden");
  searchMsg.textContent = "";
  searchMsg.className = "msg";
}

function renderResults(query, cities) {
  clearSearch();
  if (cities.length === 0) {
    searchMsg.textContent = "Nenhuma cidade encontrada para “" + query + "”. Confira o nome e tente de novo.";
    return;
  }
  cities.forEach(function (city) {
    var li = el("li", "result");
    var label = el("div");
    label.appendChild(document.createTextNode(city.name));
    label.appendChild(el("small", "", placeText(city)));
    var button = el("button", "btn small", favoriteKeys[city.key] ? "Já favorita" : "Favoritar");
    button.type = "button";
    button.disabled = !!favoriteKeys[city.key];
    button.addEventListener("click", function () { addFavorite(city, button); });
    li.appendChild(label);
    li.appendChild(button);
    searchResults.appendChild(li);
  });
  searchResults.classList.remove("hidden");
}

searchInput.addEventListener("input", function () {
  clearTimeout(searchTimer);
  var query = searchInput.value.trim();
  if (query.length < 2) { searchSeq++; clearSearch(); return; }

  searchTimer = setTimeout(async function () {
    var seq = ++searchSeq;
    try {
      var result = await api("/api/cities/search?q=" + encodeURIComponent(query));
      if (seq !== searchSeq) return;
      if (!guard(result)) return;
      if (!result.ok) { clearSearch(); searchMsg.className = "msg error"; searchMsg.textContent = apiError(result); return; }
      renderResults(query, result.data.results || []);
    } catch (e) {
      if (seq !== searchSeq) return;
      clearSearch();
      searchMsg.className = "msg error";
      searchMsg.textContent = "Não foi possível conectar ao servidor.";
    }
  }, 350);
});

async function addFavorite(city, button) {
  button.disabled = true;
  try {
    var result = await api("/api/favorites", {
      method: "POST",
      body: {
        name: city.name, state: city.state, country: city.country,
        latitude: city.latitude, longitude: city.longitude, timezone: city.timezone
      }
    });
    if (!guard(result)) return;
    if (result.ok || result.status === 409) {
      searchInput.value = "";
      clearSearch();
      loadFavorites();
      return;
    }
    searchMsg.className = "msg error";
    searchMsg.textContent = apiError(result);
  } catch (e) {
    searchMsg.className = "msg error";
    searchMsg.textContent = "Não foi possível favoritar a cidade.";
  }
  button.disabled = false;
}

// ── Conta: sair e trocar senha (RF7) ────────────────────────
document.getElementById("logout-btn").addEventListener("click", async function () {
  try { await api("/api/auth/logout", { method: "POST" }); } finally { goToLogin(); }
});

var dialog = document.getElementById("password-dialog");
var passwordForm = document.getElementById("password-form");
var passwordMsg = document.getElementById("password-msg");
var passwordSubmit = document.getElementById("password-submit");

function setPasswordMessage(text, kind) {
  passwordMsg.textContent = text;
  passwordMsg.className = "msg" + (kind ? " " + kind : "");
}

document.getElementById("change-password-btn").addEventListener("click", function () {
  passwordForm.reset();
  setPasswordMessage("");
  dialog.showModal();
  document.getElementById("senha-atual").focus();
});
document.getElementById("password-cancel").addEventListener("click", function () { dialog.close(); });

passwordForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  var atual = document.getElementById("senha-atual").value;
  var nova = document.getElementById("nova-senha").value;
  var confirmar = document.getElementById("confirmar-senha").value;

  if (!atual) return setPasswordMessage("Informe a senha atual.", "error");
  if (nova.length < 8) return setPasswordMessage("A nova senha deve ter pelo menos 8 caracteres.", "error");
  if (nova !== confirmar) return setPasswordMessage("As senhas não coincidem.", "error");

  passwordSubmit.disabled = true;
  try {
    var result = await api("/api/auth/password", { method: "POST", body: { senha_atual: atual, nova_senha: nova } });
    if (result.status === 401) { goToLogin(); return; }
    if (result.ok) {
      setPasswordMessage("Senha alterada com sucesso.", "ok");
      setTimeout(function () { dialog.close(); }, 1200);
    } else {
      setPasswordMessage(apiError(result), "error");
    }
  } catch (e) {
    setPasswordMessage("Não foi possível conectar ao servidor.", "error");
  } finally {
    passwordSubmit.disabled = false;
  }
});

// ── Início ──────────────────────────────────────────────────
(async function init() {
  try {
    var me = await api("/api/me");
    if (!guard(me)) return;
    if (me.ok) accountName.textContent = me.data.name;
  } catch (e) { /* a lista mostra o erro de conexão */ }
  loadFavorites();
})();
