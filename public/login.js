var form = document.getElementById("form");
var errorEl = document.getElementById("error");
var submit = document.getElementById("submit");

if (new URLSearchParams(location.search).get("conta") === "criada") {
  document.getElementById("created").classList.remove("hidden");
}

document.querySelectorAll(".toggle").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var input = document.getElementById(btn.dataset.target);
    var show = input.type === "password";
    input.type = show ? "text" : "password";
    btn.textContent = show ? "🙈" : "👁️";
    btn.setAttribute("aria-pressed", String(show));
    btn.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
    input.focus();
  });
});

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  errorEl.textContent = "";

  var email = document.getElementById("email").value.trim();
  var senha = document.getElementById("senha").value;
  if (!email || !senha) {
    errorEl.textContent = "Informe o e-mail e a senha.";
    return;
  }

  submit.disabled = true;
  try {
    var result = await api("/api/auth/login", { method: "POST", body: { email: email, senha: senha } });
    if (result.ok) {
      window.location.href = "/home";
    } else {
      errorEl.textContent = apiError(result);
    }
  } catch (e) {
    errorEl.textContent = "Não foi possível conectar ao servidor.";
  } finally {
    submit.disabled = false;
  }
});
