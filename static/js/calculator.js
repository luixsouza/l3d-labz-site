// L3D Labz — Calculadora de Precificação de Impressão 3D (vanilla JS, sem framework)
// Espelha EXATAMENTE as fórmulas de apps/calculator/services.py (PricingService.calcular).
// Cálculo 100% client-side em tempo real — zero fetch.
(function () {
  "use strict";

  /* ---- helpers de leitura de input ---- */
  function num(id, fallback) {
    var v = parseFloat(document.getElementById(id) && document.getElementById(id).value);
    return isNaN(v) || v < 0 ? fallback : v;
  }

  /* ---- formatação BRL (espelha format_brl do Python) ---- */
  function brl(valor) {
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  /* ---- escreve valor num elemento ---- */
  function escrever(id, valor) {
    var el = document.getElementById(id);
    if (el) el.textContent = brl(valor);
  }

  /* ---- fórmulas de precificação (espelho de PricingService.calcular) ----
   *
   * custo_material   = (peso_g / 1000) * preco_kg
   * custo_energia    = (potencia_w / 1000) * tempo_h * tarifa_kwh
   * custo_depreciacao= (valor_maquina / vida_util_h) * tempo_h
   * custo_maoobra    = valor fixo informado (passthrough)
   * subtotal         = soma dos quatro acima
   * ajuste_falha     = subtotal * (taxa_falha_pct / 100)
   * custo_total      = subtotal + ajuste_falha
   * preco_venda      = custo_total * (1 + margem_pct / 100)
   */
  function calcular() {
    var peso_g          = num("id_peso_g",        50);
    var preco_kg        = num("id_preco_kg",       120);
    var potencia_w      = num("id_potencia_w",     110);
    var tempo_h         = num("id_tempo_h",        4);
    var tarifa_kwh      = num("id_tarifa_kwh",     0.95);
    var valor_maquina   = num("id_valor_maquina",  2000);
    var vida_util_h     = num("id_vida_util_h",    2000);
    var custo_maoobra   = num("id_custo_maoobra",  10);
    var taxa_falha_pct  = num("id_taxa_falha_pct", 10);
    var margem_pct      = num("id_margem_pct",     150);

    var custo_material    = (peso_g / 1000) * preco_kg;
    var custo_energia     = (potencia_w / 1000) * tempo_h * tarifa_kwh;
    var custo_depreciacao = (valor_maquina / vida_util_h) * tempo_h;
    var subtotal          = custo_material + custo_energia + custo_depreciacao + custo_maoobra;
    var ajuste_falha      = subtotal * (taxa_falha_pct / 100);
    var custo_total       = subtotal + ajuste_falha;
    var preco_venda       = custo_total * (1 + margem_pct / 100);

    escrever("res_custo_material",    custo_material);
    escrever("res_custo_energia",     custo_energia);
    escrever("res_custo_depreciacao", custo_depreciacao);
    escrever("res_custo_maoobra",     custo_maoobra);
    escrever("res_subtotal",          subtotal);
    escrever("res_ajuste_falha",      ajuste_falha);
    escrever("res_custo_total",       custo_total);
    escrever("res_preco_venda",       preco_venda);
  }

  /* ---- inicialização ---- */
  function init() {
    var form = document.getElementById("calcForm");
    if (!form) return;

    // atualiza ao mudar qualquer input
    form.addEventListener("input", calcular);
    form.addEventListener("change", calcular);

    // cálculo inicial com os defaults
    calcular();
  }

  // aguarda DOM pronto (o script tem defer, mas garantimos)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();
