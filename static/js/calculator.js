// L3D Labz — Calculadora de Precificação 3D (vanilla JS, IIFE, sem framework)
// Espelha EXATAMENTE as fórmulas de apps/calculator/services.py (PricingService.calcular enxuto).
//
// Fórmula enxuta (decisão D-01 enxuto — 2026-06-17):
//   custo_material = (peso_g / 1000) * preco_kg
//   custo_energia  = (potencia_w / 1000) * tempo_h * valor_kwh
//   subtotal       = custo_material + custo_energia + custo_maoobra + custos_fixos
//   preco_venda    = subtotal * (1 + margem_pct / 100)
//
// ATENÇÃO: este arquivo é apenas preview client-side.
// O servidor é a fonte da verdade — diferença de ±R$ 0,01 por floating point é aceitável.
(function () {
  "use strict";

  // ---- leitura dos presets via json_script (sem hardcode de números) ----
  var PRESETS = (function () {
    var el = document.getElementById("calc-presets");
    if (!el) return { filamentos: {}, consumo_chips: [], bandeira_kwh: {} };
    try { return JSON.parse(el.textContent); }
    catch (e) { return { filamentos: {}, consumo_chips: [], bandeira_kwh: {} }; }
  }());

  // ---- helpers de leitura de input ----
  function num(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    var v = parseFloat(el.value);
    return isNaN(v) || v < 0 ? fallback : v;
  }

  function selVal(id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
  }

  function setVal(id, v) {
    var el = document.getElementById(id);
    if (el) el.value = v;
  }

  function setText(id, txt) {
    var el = document.getElementById(id);
    if (el) el.textContent = txt;
  }

  // ---- formatação BRL ----
  function brl(valor) {
    var n = Number(valor);
    if (isNaN(n)) n = 0;
    return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  // ---- escreve valor monetário num elemento ----
  function escrever(id, valor) {
    setText(id, brl(valor));
  }

  // ---- auto-preenchimento por preset de filamento ----
  function aplicarPresetFilamento(key) {
    var p = PRESETS.filamentos && PRESETS.filamentos[key];
    if (!p || key === "manual") return;
    setVal("id_preco_kg", p.preco_kg_default);
  }

  // ---- chips: marca o ativo e limpa os outros ----
  function marcarChipAtivo(chipAtivo, grupo) {
    if (!grupo) return;
    var chips = grupo.querySelectorAll(".pill");
    chips.forEach(function (c) { c.classList.remove("active"); });
    if (chipAtivo) chipAtivo.classList.add("active");
  }

  // ---- atualiza barra de breakdown ----
  function atualizarBarra(idBarra, idPct, valor, total) {
    var pct  = total > 0 ? Math.round((valor / total) * 1000) / 10 : 0;
    var barEl = document.getElementById(idBarra);
    var pctEl = document.getElementById(idPct);
    if (barEl) barEl.style.width = pct + "%";
    if (pctEl) pctEl.textContent = pct.toFixed(1) + "%";
  }

  // ---- fórmulas de precificação (espelho exato de PricingService.calcular enxuto) ----
  //
  // custo_material = (peso_g / 1000) * preco_kg
  // custo_energia  = (potencia_w / 1000) * tempo_h * valor_kwh
  // custo_maoobra  = valor fixo informado (passthrough)
  // custos_fixos   = valor fixo informado (passthrough)
  // subtotal       = custo_material + custo_energia + custo_maoobra + custos_fixos
  // preco_venda    = subtotal * (1 + margem_pct / 100)
  function calcular() {
    var peso_g        = num("id_peso_g",          0);
    var preco_kg      = num("id_preco_kg",         0);
    var potencia_w    = num("id_potencia_w",       0);
    var tempo_h       = num("id_tempo_h",          0);
    var valor_kwh     = num("id_valor_kwh",        0);
    var custo_maoobra = num("id_custo_maoobra",    0);
    var custos_fixos  = num("id_custos_fixos",     0);
    var margem_pct    = num("id_margem_pct",       0);

    // --- cálculos (espelhando Python com mesma ordem) ---
    var custo_material = (peso_g / 1000) * preco_kg;
    var custo_energia  = (potencia_w / 1000) * tempo_h * valor_kwh;
    var subtotal       = custo_material + custo_energia + custo_maoobra + custos_fixos;
    var preco_venda    = subtotal * (1 + margem_pct / 100);

    // --- exibe valores monetários ---
    escrever("res_custo_material", custo_material);
    escrever("res_custo_energia",  custo_energia);
    escrever("res_custo_maoobra",  custo_maoobra);
    escrever("res_custos_fixos",   custos_fixos);
    escrever("res_subtotal",       subtotal);
    escrever("res_preco_venda",    preco_venda);

    // --- breakdown: % de cada componente sobre subtotal ---
    atualizarBarra("bar_custo_material", "pct_custo_material", custo_material, subtotal);
    atualizarBarra("bar_custo_energia",  "pct_custo_energia",  custo_energia,  subtotal);
    atualizarBarra("bar_custo_maoobra",  "pct_custo_maoobra",  custo_maoobra,  subtotal);
    atualizarBarra("bar_custos_fixos",   "pct_custos_fixos",   custos_fixos,   subtotal);

    // --- permalink: serializa campos na query string ---
    atualizarPermalink();
  }

  // ---- permalink (query string compartilhável) ----
  var CAMPOS_PERMALINK = [
    "id_peso_g", "id_preco_kg", "id_potencia_w", "id_tempo_h",
    "id_valor_kwh", "id_custo_maoobra", "id_custos_fixos", "id_margem_pct",
    "id_filamento"
  ];

  function atualizarPermalink() {
    var params = new URLSearchParams();
    CAMPOS_PERMALINK.forEach(function (id) {
      var el = document.getElementById(id);
      if (el && el.value !== "") params.set(id.replace("id_", ""), el.value);
    });
    try {
      history.replaceState(null, "", "?" + params.toString());
    } catch (e) { /* silencioso */ }
  }

  function reidratarPermalink() {
    if (!location.search) return;
    var params = new URLSearchParams(location.search);
    CAMPOS_PERMALINK.forEach(function (id) {
      var key = id.replace("id_", "");
      if (params.has(key)) {
        var el = document.getElementById(id);
        if (el) el.value = params.get(key);
      }
    });
    // aplica presets de filamento reidratados
    var filamentoKey = selVal("id_filamento");
    if (filamentoKey && filamentoKey !== "manual") aplicarPresetFilamento(filamentoKey);
  }

  // ---- botão Copiar resultado ----
  function copiarResultado() {
    var linhas = [
      "Calculadora 3D — L3D Labz",
      "==========================",
      "Material (filamento): " + (document.getElementById("res_custo_material") || {}).textContent,
      "Energia elétrica:     " + (document.getElementById("res_custo_energia") || {}).textContent,
      "Mão de obra:          " + (document.getElementById("res_custo_maoobra") || {}).textContent,
      "Custos fixos:         " + (document.getElementById("res_custos_fixos") || {}).textContent,
      "Subtotal:             " + (document.getElementById("res_subtotal") || {}).textContent,
      "==========================",
      "PREÇO DE VENDA: " + (document.getElementById("res_preco_venda") || {}).textContent,
    ];

    var texto = linhas.join("\n");
    var btn = document.getElementById("btnCopiar");

    function feedback(ok) {
      if (!btn) return;
      var original = btn.textContent;
      btn.textContent = ok ? "Copiado!" : "Erro ao copiar";
      btn.setAttribute("aria-pressed", "true");
      setTimeout(function () {
        btn.textContent = original;
        btn.removeAttribute("aria-pressed");
      }, 2000);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(
        function () { feedback(true); },
        function () { fallbackCopiar(texto, feedback); }
      );
    } else {
      fallbackCopiar(texto, feedback);
    }
  }

  function fallbackCopiar(texto, feedback) {
    var ta = document.createElement("textarea");
    ta.value = texto;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    feedback(ok);
  }

  // ---- inicialização ----
  function init() {
    var form = document.getElementById("calcForm");
    if (!form) return;

    // reidrata permalink antes do primeiro cálculo
    reidratarPermalink();

    // listener de preset de filamento
    var selFilamento = document.getElementById("id_filamento");
    if (selFilamento) {
      selFilamento.addEventListener("change", function () {
        if (this.value !== "manual") aplicarPresetFilamento(this.value);
        calcular();
      });
    }

    // botão "Puxar preço do site" — preenche preco_kg com o default do filamento selecionado
    var btnPuxar = document.getElementById("btnPuxarPreco");
    if (btnPuxar) {
      btnPuxar.addEventListener("click", function () {
        var key = selVal("id_filamento");
        aplicarPresetFilamento(key);
        calcular();
      });
    }

    // botão "Restaurar preço automático" — idem (ambos usam a mesma referência)
    var btnRestaurar = document.getElementById("btnRestaurarPreco");
    if (btnRestaurar) {
      btnRestaurar.addEventListener("click", function () {
        var key = selVal("id_filamento");
        aplicarPresetFilamento(key);
        calcular();
      });
    }

    // botão "Calcular Custo" (redundante mas explícito)
    var btnCalcular = document.getElementById("btnCalcular");
    if (btnCalcular) {
      btnCalcular.addEventListener("click", calcular);
    }

    // botão "Limpar"
    var btnLimpar = document.getElementById("btnLimpar");
    if (btnLimpar) {
      btnLimpar.addEventListener("click", function () {
        form.reset();
        // limpa chips ativos
        document.querySelectorAll(".pill.active").forEach(function (c) { c.classList.remove("active"); });
        calcular();
      });
    }

    // chips de consumo de impressora (data-w)
    var consumoGrupo = document.getElementById("consumo-chips");
    if (consumoGrupo) {
      consumoGrupo.addEventListener("click", function (e) {
        var btn = e.target.closest(".pill[data-w]");
        if (!btn) return;
        setVal("id_potencia_w", btn.dataset.w);
        marcarChipAtivo(btn, consumoGrupo);
        calcular();
      });
    }

    // chips de bandeira tarifária (data-kwh)
    var bandeiraGrupo = document.getElementById("bandeira-chips");
    if (bandeiraGrupo) {
      bandeiraGrupo.addEventListener("click", function (e) {
        var btn = e.target.closest(".pill[data-kwh]");
        if (!btn) return;
        setVal("id_valor_kwh", btn.dataset.kwh);
        marcarChipAtivo(btn, bandeiraGrupo);
        calcular();
      });
    }

    // chips de margem (data-margem)
    var margemGrupo = document.getElementById("margem-chips");
    if (margemGrupo) {
      margemGrupo.addEventListener("click", function (e) {
        var btn = e.target.closest(".pill[data-margem]");
        if (!btn) return;
        setVal("id_margem_pct", btn.dataset.margem);
        marcarChipAtivo(btn, margemGrupo);
        calcular();
      });
    }

    // listeners genéricos em todos os inputs do form (recalcula em tempo real)
    form.addEventListener("input", calcular);
    form.addEventListener("change", calcular);

    // botão copiar
    var btnCopiar = document.getElementById("btnCopiar");
    if (btnCopiar) btnCopiar.addEventListener("click", copiarResultado);

    // cálculo inicial
    calcular();
  }

  // aguarda DOM (script tem defer, mas garantimos)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

}());
