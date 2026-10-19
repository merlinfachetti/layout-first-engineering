/*
 * VS-01 Lista de leituras. JavaScript sem dependências e sem rede.
 *
 * FR-001 adicionar com título obrigatório · FR-002 persistir no localStorage
 * FR-003 marcar como lida, com persistência · FR-004 recusar título vazio, anunciando o erro
 * FR-005 se o armazenamento falhar, mostrar o erro e não fingir sucesso
 *
 * Regra central: a interface só muda depois que a gravação deu certo. Se `setItem` lançar
 * erro, nada muda na lista e o título digitado continua no campo.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "lfe-vs01:readings:v1";
  var MAX_TITLE = 200;
  var MONTHS = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."];

  var form = document.getElementById("reading-form");
  var input = document.getElementById("reading-title");
  var fieldError = document.getElementById("reading-error");
  var storageError = document.getElementById("storage-error");
  var statusRegion = document.getElementById("reading-status");
  var list = document.getElementById("reading-list");
  var summary = document.getElementById("reading-summary");
  var emptyState = document.getElementById("empty-state");

  // Itens em ordem de criação; a tela mostra do mais novo para o mais antigo.
  var readings = [];
  // null, "unavailable" (o navegador bloqueou o acesso) ou "corrupt" (dados ilegíveis).
  var loadProblem = null;

  /* ---- Armazenamento ------------------------------------------------- */

  function isReading(value) {
    return value !== null && typeof value === "object" &&
      typeof value.id === "string" && value.id.length > 0 &&
      typeof value.title === "string" && value.title.trim().length > 0 &&
      typeof value.done === "boolean" &&
      typeof value.createdAt === "string" && !isNaN(Date.parse(value.createdAt));
  }

  function load() {
    var raw;
    try {
      // Acessar `localStorage` já pode lançar erro (cookies bloqueados, modo restrito).
      raw = window.localStorage.getItem(STORAGE_KEY);
    } catch (err) {
      return { items: [], problem: "unavailable" };
    }
    if (raw === null) {
      return { items: [], problem: null };
    }
    try {
      var data = JSON.parse(raw);
      if (Array.isArray(data) && data.every(isReading)) {
        return { items: data, problem: null };
      }
    } catch (err) {
      // cai no retorno abaixo
    }
    return { items: [], problem: "corrupt" };
  }

  function save(items) {
    if (loadProblem === "corrupt") {
      // Gravar agora apagaria dados que não conseguimos ler. Melhor recusar.
      throw new Error("corrupt-data");
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }

  function newId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return window.crypto.randomUUID();
    }
    return "r-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
  }

  /* ---- Mensagens ----------------------------------------------------- */

  function quoted(title) {
    return "“" + title + "”";
  }

  function announce(message) {
    // Esvaziar antes garante que a mesma frase seja anunciada de novo.
    statusRegion.textContent = "";
    window.setTimeout(function () {
      statusRegion.textContent = message;
    }, 50);
  }

  function showFieldError(message) {
    input.setAttribute("aria-invalid", "true");
    fieldError.textContent = "";
    window.setTimeout(function () {
      fieldError.textContent = message;
    }, 50);
  }

  function clearFieldError() {
    input.removeAttribute("aria-invalid");
    fieldError.textContent = "";
  }

  function showStorageError(headline, detail) {
    storageError.textContent = "";
    var first = document.createElement("p");
    var strong = document.createElement("strong");
    strong.textContent = headline;
    first.appendChild(strong);
    storageError.appendChild(first);
    if (detail) {
      var second = document.createElement("p");
      second.textContent = detail;
      storageError.appendChild(second);
    }
    storageError.hidden = false;
  }

  function clearStorageError() {
    storageError.hidden = true;
    storageError.textContent = "";
  }

  function storageDetail() {
    if (loadProblem === "corrupt") {
      return "Os dados guardados neste navegador não estão no formato esperado. " +
        "Para não apagar nada, a lista não grava até que eles sejam removidos.";
    }
    return "O navegador recusou a gravação: o armazenamento local pode estar cheio ou bloqueado.";
  }

  /* ---- Desenho ------------------------------------------------------- */

  function formatDate(iso) {
    var date = new Date(iso);
    var text = date.getDate() + " " + MONTHS[date.getMonth()];
    if (date.getFullYear() !== new Date().getFullYear()) {
      text += " " + date.getFullYear();
    }
    return text;
  }

  function plural(count, one, many) {
    return count + " " + (count === 1 ? one : many);
  }

  function renderSummary() {
    var done = readings.filter(function (r) { return r.done; }).length;
    var pending = readings.length - done;
    summary.textContent = readings.length === 0 ? "" :
      pending + " para ler, " + plural(done, "lida", "lidas");
    emptyState.hidden = readings.length > 0 || loadProblem === "corrupt";
  }

  function buildEntry(reading) {
    var item = document.createElement("li");
    item.className = "entry" + (reading.done ? " is-done" : "");
    item.dataset.id = reading.id;

    var check = document.createElement("input");
    check.type = "checkbox";
    check.className = "entry-check";
    check.id = "done-" + reading.id;
    check.checked = reading.done;
    check.setAttribute("aria-describedby", "date-" + reading.id);

    var line = document.createElement("div");
    line.className = "entry-line";

    var label = document.createElement("label");
    label.className = "entry-title";
    label.htmlFor = check.id;
    label.textContent = reading.title;

    var leader = document.createElement("span");
    leader.className = "entry-leader";
    leader.setAttribute("aria-hidden", "true");

    line.appendChild(label);
    line.appendChild(leader);

    var date = document.createElement("time");
    date.className = "entry-date";
    date.id = "date-" + reading.id;
    date.dateTime = reading.createdAt;
    var prefix = document.createElement("span");
    prefix.className = "visually-hidden";
    prefix.textContent = "adicionada em ";
    date.appendChild(prefix);
    date.appendChild(document.createTextNode(formatDate(reading.createdAt)));

    item.appendChild(check);
    item.appendChild(line);
    item.appendChild(date);
    return item;
  }

  function render(newId) {
    list.textContent = "";
    for (var i = readings.length - 1; i >= 0; i -= 1) {
      var entry = buildEntry(readings[i]);
      if (readings[i].id === newId) {
        entry.classList.add("is-new");
      }
      list.appendChild(entry);
    }
    renderSummary();
  }

  /* ---- Ações --------------------------------------------------------- */

  function addReading(rawTitle) {
    var title = rawTitle.trim();
    if (title.length === 0) {
      showFieldError("Escreva um título antes de adicionar. Espaços em branco não contam.");
      input.focus();
      return;
    }
    if (title.length > MAX_TITLE) {
      showFieldError("Use no máximo " + MAX_TITLE + " caracteres no título.");
      input.focus();
      return;
    }
    clearFieldError();

    var reading = { id: newId(), title: title, done: false, createdAt: new Date().toISOString() };
    var next = readings.concat([reading]);
    try {
      save(next);
    } catch (err) {
      showStorageError("Não foi possível salvar " + quoted(title) + ".",
        storageDetail() + " A leitura não foi adicionada; o título continua no campo.");
      input.focus();
      return;
    }

    readings = next;
    if (loadProblem === "unavailable") {
      loadProblem = null;
    }
    clearStorageError();
    render(reading.id);
    input.value = "";
    input.focus();
    announce(quoted(title) + " adicionada ao sumário.");
  }

  function setDone(id, done, checkbox) {
    var target = null;
    var next = readings.map(function (r) {
      if (r.id !== id) {
        return r;
      }
      target = { id: r.id, title: r.title, done: done, createdAt: r.createdAt };
      return target;
    });
    if (target === null) {
      return;
    }
    try {
      save(next);
    } catch (err) {
      checkbox.checked = !done;
      showStorageError("Não foi possível salvar a mudança em " + quoted(target.title) + ".",
        storageDetail() + " A leitura continua como estava.");
      return;
    }

    readings = next;
    if (loadProblem === "unavailable") {
      loadProblem = null;
    }
    clearStorageError();
    // Atualiza só o item, sem redesenhar a lista, para o foco ficar onde a pessoa está.
    checkbox.closest(".entry").classList.toggle("is-done", done);
    renderSummary();
    announce(quoted(target.title) + (done ? " marcada como lida." : " marcada como não lida."));
  }

  /* ---- Início -------------------------------------------------------- */

  function start() {
    var result = load();
    readings = result.items;
    loadProblem = result.problem;
    render(null);
    if (loadProblem === "unavailable") {
      showStorageError("O armazenamento deste navegador está bloqueado.",
        "Você pode usar a página, mas nada será salvo enquanto o armazenamento local estiver " +
        "indisponível (por exemplo, em algumas janelas privadas).");
    } else if (loadProblem === "corrupt") {
      showStorageError("Não foi possível ler as leituras guardadas.", storageDetail());
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      addReading(input.value);
    });

    input.addEventListener("input", function () {
      if (input.getAttribute("aria-invalid") === "true" && input.value.trim().length > 0) {
        clearFieldError();
      }
    });

    list.addEventListener("change", function (event) {
      var checkbox = event.target;
      if (!checkbox.classList || !checkbox.classList.contains("entry-check")) {
        return;
      }
      setDone(checkbox.closest(".entry").dataset.id, checkbox.checked, checkbox);
    });

    // Outra aba mudou a lista: recarrega para não gravar por cima de dados mais novos.
    window.addEventListener("storage", function (event) {
      if (event.key !== STORAGE_KEY) {
        return;
      }
      var fresh = load();
      readings = fresh.items;
      loadProblem = fresh.problem;
      if (loadProblem === null) {
        clearStorageError();
      }
      render(null);
    });
  }

  start();
})();
