// L3D Labz — Calculadora de Precificação 3D v2 (vanilla JS, IIFE, sem framework)
// Espelha EXATAMENTE as fórmulas de apps/calculator/services.py (PricingService.calcular).
//
// ATENÇÃO: este arquivo é apenas preview client-side.
// O servidor é a fonte da verdade — diferença de ±R$ 0,01 por floating point é aceitável.
// O orçamento formal é sempre recalculado server-side via PricingService.
(function () {
  "use strict";

  // ---- leitura dos presets via json_script (sem hardcode de números) ----
  var PRESETS = (function () {
    var el = document.getElementById("calc-presets");
    if (!el) return { impressoras: {}, filamentos: {}, bandeiras: {} };
    try { return JSON.parse(el.textContent); }
    catch (e) { return { impressoras: {}, filamentos: {}, bandeiras: {} }; }
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
    // guarda anti-NaN: campo vazio ou cálculo com zero produz NaN em alguns paths
    var n = Number(valor);
    if (isNaN(n)) n = 0;
    return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  // ---- escreve valor monetário num elemento ----
  function escrever(id, valor) {
    setText(id, brl(valor));
  }

  // ---- auto-preenchimento por preset de impressora ----
  function aplicarPresetImpressora(key) {
    var p = PRESETS.impressoras && PRESETS.impressoras[key];
    if (!p || key === "manual") return;
    setVal("id_potencia_w",    p.potencia_w);
    setVal("id_valor_maquina", p.valor_maquina);
    setVal("id_vida_util_h",   p.vida_util_h);
  }

  // ---- auto-preenchimento por preset de filamento ----
  function aplicarPresetFilamento(key) {
    var p = PRESETS.filamentos && PRESETS.filamentos[key];
    if (!p || key === "manual") return;
    setVal("id_preco_kg", p.preco_kg_default);
  }

  // ---- calcula e exibe tarifa efetiva ----
  function atualizarTarifaEfetiva() {
    var tarifa_base   = num("id_tarifa_base", 0);
    var bandeiraKey   = selVal("id_bandeira");
    var b             = PRESETS.bandeiras && PRESETS.bandeiras[bandeiraKey];
    var adicional     = b ? b.adicional_kwh : 0;
    var tarifa_efetiva = tarifa_base + adicional;

    var el = document.getElementById("res_tarifa_efetiva");
    if (el) {
      var base_fmt  = brl(tarifa_base);
      var adic_fmt  = adicional === 0
        ? "sem adicional"
        : "Bandeira +" + brl(adicional).replace("R$ ", "R$ ");
      el.textContent = "Tarifa efetiva: " + brl(tarifa_efetiva) + "/kWh"
        + " (base " + base_fmt + " + " + adic_fmt + ")";
    }
    return tarifa_efetiva;
  }

  // ---- atualiza barra de breakdown ----
  function atualizarBarra(idBarra, idPct, valor, total) {
    var pct  = total > 0 ? Math.round((valor / total) * 1000) / 10 : 0;
    var barEl = document.getElementById(idBarra);
    var pctEl = document.getElementById(idPct);
    if (barEl) barEl.style.width = pct + "%";
    if (pctEl) pctEl.textContent = pct.toFixed(1) + "%";
  }

  // ---- fórmulas de precificação (espelho exato de PricingService.calcular) ----
  //
  // custo_material    = (peso_g / 1000) * preco_kg
  // custo_energia     = (potencia_w / 1000) * tempo_h * tarifa_efetiva
  // custo_depreciacao = (valor_maquina / vida_util_h) * tempo_h
  // custo_maoobra     = valor fixo informado (passthrough)
  // subtotal          = custo_material + custo_energia + custo_depreciacao + custo_maoobra
  // ajuste_falha      = subtotal * (taxa_falha_pct / 100)
  // custo_total       = subtotal + ajuste_falha
  // preco_venda       = custo_total * (1 + margem_pct / 100)
  function calcular() {
    var peso_g         = num("id_peso_g",        0);
    var preco_kg       = num("id_preco_kg",       0);
    var potencia_w     = num("id_potencia_w",     0);
    var tempo_h        = num("id_tempo_h",        0);
    var tarifa_efetiva = atualizarTarifaEfetiva(); // tarifa_base + adicional_bandeira
    var valor_maquina  = num("id_valor_maquina",  0);
    var vida_util_h    = num("id_vida_util_h",    0);
    var custo_maoobra  = num("id_custo_maoobra",  0);
    var taxa_falha_pct = num("id_taxa_falha_pct", 0);
    var margem_pct     = num("id_margem_pct",     0);
    var quantidade     = Math.max(1, Math.round(num("id_quantidade_pub", 1)));

    // --- cálculos (espelhando Python com mesma ordem) ---
    var custo_material    = (peso_g / 1000) * preco_kg;
    var custo_energia     = (potencia_w / 1000) * tempo_h * tarifa_efetiva;
    var custo_depreciacao = vida_util_h > 0 ? (valor_maquina / vida_util_h) * tempo_h : 0;
    var subtotal          = custo_material + custo_energia + custo_depreciacao + custo_maoobra;
    var ajuste_falha      = subtotal * (taxa_falha_pct / 100);
    var custo_total       = subtotal + ajuste_falha;
    var preco_venda       = custo_total * (1 + margem_pct / 100);

    // --- exibe valores monetários ---
    escrever("res_custo_material",    custo_material);
    escrever("res_custo_energia",     custo_energia);
    escrever("res_custo_depreciacao", custo_depreciacao);
    escrever("res_custo_maoobra",     custo_maoobra);
    escrever("res_subtotal",          subtotal);
    escrever("res_ajuste_falha",      ajuste_falha);
    escrever("res_custo_total",       custo_total);
    escrever("res_preco_venda",       preco_venda);

    // --- breakdown: % de cada componente sobre custo_total ---
    atualizarBarra("bar_custo_material",    "pct_custo_material",    custo_material,    custo_total);
    atualizarBarra("bar_custo_energia",     "pct_custo_energia",     custo_energia,     custo_total);
    atualizarBarra("bar_custo_depreciacao", "pct_custo_depreciacao", custo_depreciacao, custo_total);
    atualizarBarra("bar_custo_maoobra",     "pct_custo_maoobra",     custo_maoobra,     custo_total);
    atualizarBarra("bar_ajuste_falha",      "pct_ajuste_falha",      ajuste_falha,      custo_total);

    // --- custo por hora ---
    var horaWrap = document.getElementById("res_custo_hora_wrap");
    if (tempo_h > 0 && custo_total > 0) {
      escrever("res_custo_hora", custo_total / tempo_h);
      if (horaWrap) horaWrap.style.display = "";
    } else {
      if (horaWrap) horaWrap.style.display = "none";
    }

    // --- total por quantidade (exibe só quando qtd > 1) ---
    var totalWrap = document.getElementById("res_total_qtd_wrap");
    if (quantidade > 1) {
      escrever("res_total_qtd", preco_venda * quantidade);
      setText("res_qtd_label", String(quantidade));
      if (totalWrap) totalWrap.style.display = "";
    } else {
      if (totalWrap) totalWrap.style.display = "none";
    }

    // --- permalink: serializa campos na query string ---
    atualizarPermalink();
  }

  // ---- permalink (query string compartilhável) ----
  var CAMPOS_PERMALINK = [
    "id_peso_g", "id_preco_kg", "id_potencia_w", "id_tempo_h",
    "id_tarifa_base", "id_bandeira", "id_valor_maquina", "id_vida_util_h",
    "id_custo_maoobra", "id_taxa_falha_pct", "id_margem_pct",
    "id_quantidade_pub", "id_impressora", "id_filamento"
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
    // aplica presets já reidratados (mantém valores se preset != manual foi carregado)
    var impressoraKey = selVal("id_impressora");
    if (impressoraKey && impressoraKey !== "manual") aplicarPresetImpressora(impressoraKey);
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
      "Depreciação máquina:  " + (document.getElementById("res_custo_depreciacao") || {}).textContent,
      "Mão de obra:          " + (document.getElementById("res_custo_maoobra") || {}).textContent,
      "Ajuste de falha:      " + (document.getElementById("res_ajuste_falha") || {}).textContent,
      "Custo total:          " + (document.getElementById("res_custo_total") || {}).textContent,
      "==========================",
      "PREÇO DE VENDA: " + (document.getElementById("res_preco_venda") || {}).textContent,
    ];

    var qtdWrap = document.getElementById("res_total_qtd_wrap");
    if (qtdWrap && qtdWrap.style.display !== "none") {
      linhas.push("Total (" + (document.getElementById("res_qtd_label") || {}).textContent + " unid.): "
        + (document.getElementById("res_total_qtd") || {}).textContent);
    }

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

    // listeners de preset de impressora
    var selImpressora = document.getElementById("id_impressora");
    if (selImpressora) {
      selImpressora.addEventListener("change", function () {
        if (this.value !== "manual") aplicarPresetImpressora(this.value);
        calcular();
      });
    }

    // listeners de preset de filamento
    var selFilamento = document.getElementById("id_filamento");
    if (selFilamento) {
      selFilamento.addEventListener("change", function () {
        if (this.value !== "manual") aplicarPresetFilamento(this.value);
        calcular();
      });
    }

    // listener do select de bandeira (separado para atualizar tarifa efetiva imediatamente)
    var selBandeira = document.getElementById("id_bandeira");
    if (selBandeira) {
      selBandeira.addEventListener("change", calcular);
    }

    // listeners genéricos em todos os inputs do form
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
