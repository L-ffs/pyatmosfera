var form = document.getElementById("form");
var errorEl = document.getElementById("error");
var submit = document.getElementById("submit");
var FIELDS = ["nome", "email", "senha", "confirmar"];

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

function showFieldErrors(messages) {
  FIELDS.forEach(function (id) {
    var msg = messages[id] || "";
    document.getElementById("err-" + id).textContent = msg;
    document.getElementById(id).setAttribute("aria-invalid", msg ? "true" : "false");
  });
}

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  errorEl.textContent = "";

  var nome = document.getElementById("nome").value.trim();
  var email = document.getElementById("email").value.trim();
  var senha = document.getElementById("senha").value;
  var confirmar = document.getElementById("confirmar").value;

  // As mesmas regras são conferidas de novo no servidor; aqui é só para avisar mais rápido.
  var messages = {};
  if (nome.length < 2) messages.nome = "Informe como podemos te chamar.";
  if (!/^[^\s@/]+@[^\s@/]+\.[^\s@/]{2,}$/.test(email)) messages.email = "Informe um e-mail válido.";
  if (senha.length < 8) messages.senha = "Use pelo menos 8 caracteres.";
  if (!confirmar || confirmar !== senha) messages.confirmar = "As senhas não coincidem.";
  showFieldErrors(messages);

  var first = FIELDS.find(function (id) { return messages[id]; });
  if (first) {
    document.getElementById(first).focus();
    return;
  }

  submit.disabled = true;
  try {
    var result = await api("/api/auth/signup", { method: "POST", body: { nome: nome, email: email, senha: senha } });
    if (result.status === 201) {
      window.location.href = "/?conta=criada";
      return;
    }
    var field = result.data && result.data.field;
    if (FIELDS.indexOf(field) !== -1) {
      var single = {};
      single[field] = apiError(result);
      showFieldErrors(single);
    } else {
      errorEl.textContent = apiError(result);
    }
  } catch (e) {
    errorEl.textContent = "Não foi possível conectar ao servidor.";
  } finally {
    submit.disabled = false;
  }
});
