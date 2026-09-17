(function () {
  const Lab = {
    lang: localStorage.getItem("fenwick-lang") || "en",

    toast(msg) {
      let el = document.querySelector(".toast");
      if (!el) {
        el = document.createElement("div");
        el.className = "toast";
        document.body.appendChild(el);
      }
      el.textContent = msg;
      el.style.display = "block";
      clearTimeout(Lab._t);
      Lab._t = setTimeout(() => (el.style.display = "none"), 2200);
    },

    applyLang(lang) {
      Lab.lang = lang;
      localStorage.setItem("fenwick-lang", lang);
      document.documentElement.lang = lang === "es" ? "es" : "en";
      document.querySelectorAll("[data-en]").forEach((el) => {
        const val = el.getAttribute("data-" + lang);
        if (val != null) el.textContent = val;
      });
      document.querySelectorAll("[data-ph-en]").forEach((el) => {
        const val = el.getAttribute("data-ph-" + lang);
        if (val != null) el.setAttribute("placeholder", val);
      });
      document.querySelectorAll(".lang button").forEach((b) => {
        b.classList.toggle("on", b.dataset.lang === lang);
      });
    },

    bindLangButtons() {
      document.querySelectorAll(".lang button").forEach((b) => {
        b.addEventListener("click", () => Lab.applyLang(b.dataset.lang));
      });
      Lab.applyLang(Lab.lang);
    },

    collect(root) {
      const data = {};
      root.querySelectorAll("[data-key]").forEach((el) => {
        const key = el.dataset.key;
        if (el.type === "checkbox" || el.type === "radio") {
          if (el.type === "radio") {
            if (el.checked) data[key] = el.value;
          } else {
            data[key] = el.checked;
          }
        } else {
          data[key] = el.value;
        }
      });
      return data;
    },

    fill(root, data) {
      if (!data) return;
      root.querySelectorAll("[data-key]").forEach((el) => {
        const key = el.dataset.key;
        if (!(key in data)) return;
        if (el.type === "checkbox") el.checked = !!data[key];
        else if (el.type === "radio") el.checked = el.value === data[key];
        else el.value = data[key];
      });
    },

    autosave(storageKey, root) {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      Lab.fill(root, saved);
      const persist = () => {
        localStorage.setItem(storageKey, JSON.stringify(Lab.collect(root)));
      };
      root.addEventListener("input", persist);
      root.addEventListener("change", persist);
      persist();
      return persist;
    },

    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        Lab.toast(Lab.lang === "es" ? "Copiado." : "Copied.");
      } catch {
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        ta.remove();
        Lab.toast(Lab.lang === "es" ? "Copiado." : "Copied.");
      }
    },

    async submit(text, name, period) {
      if (!(name || "").trim() || !(period || "").trim()) {
        Lab.toast(Lab.lang === "es" ? "Pon tu nombre y periodo primero." : "Type your name and period first.");
        return;
      }
      await Lab.copy(text);
      let m = document.getElementById("turnin-modal");
      if (!m) {
        m = document.createElement("div");
        m.id = "turnin-modal";
        m.className = "modal";
        m.innerHTML = `<div class="modal-card">
          <h2 data-en="Nice work. One more step." data-es="Buen trabajo. Un paso más.">Nice work. One more step.</h2>
          <ol>
            <li data-en="Open Classroom." data-es="Abre Classroom.">Open Classroom.</li>
            <li data-en="Open Ms. Fenwick’s question for today." data-es="Abre la pregunta de la Sra. Fenwick.">Open Ms. Fenwick’s question for today.</li>
            <li data-en="Click the answer box." data-es="Toca la casilla de respuesta.">Click the answer box.</li>
            <li><strong>Ctrl + V</strong> <span data-en="to paste" data-es="para pegar">to paste</span></li>
            <li data-en="Click Submit. You’re done." data-es="Toca Entregar. Listo.">Click Submit. You’re done.</li>
          </ol>
          <button type="button" class="btn btn-ok" id="turnin-ok">OK</button>
        </div>`;
        document.body.appendChild(m);
        m.addEventListener("click", (e) => {
          if (e.target === m || e.target.id === "turnin-ok") m.classList.remove("on");
        });
        Lab.applyLang(Lab.lang);
      }
      m.classList.add("on");
    },

    download(filename, text) {
      const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    },

    linesFrom(obj, order) {
      return order
        .map(([label, key]) => `${label}: ${obj[key] || ""}`)
        .join("\n");
    },
  };

  window.Lab = Lab;
  document.addEventListener("DOMContentLoaded", () => Lab.bindLangButtons());
})();
