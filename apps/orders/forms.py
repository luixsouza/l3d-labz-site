"""Formulário de checkout — endereço de entrega + método de pagamento."""
from __future__ import annotations

import re

from django import forms

from .models import Order

UF_CHOICES = [("", "UF")] + [(uf, uf) for uf in (
    "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
)]


class CheckoutForm(forms.Form):
    # --- entrega ---
    recipient = forms.CharField(label="Destinatário", max_length=120)
    phone = forms.CharField(label="Telefone", max_length=20, required=False)
    zip_code = forms.CharField(label="CEP", max_length=9)
    street = forms.CharField(label="Logradouro", max_length=160)
    number_addr = forms.CharField(label="Número", max_length=20)
    complement = forms.CharField(label="Complemento", max_length=80, required=False)
    district = forms.CharField(label="Bairro", max_length=80)
    city = forms.CharField(label="Cidade", max_length=80)
    state = forms.ChoiceField(label="UF", choices=UF_CHOICES)

    # --- pagamento ---
    payment_method = forms.ChoiceField(
        label="Pagamento", choices=Order.Payment.choices, widget=forms.RadioSelect
    )
    card_name = forms.CharField(label="Nome no cartão", max_length=120, required=False)
    card_number = forms.CharField(label="Número do cartão", max_length=19, required=False)
    card_expiry = forms.CharField(label="Validade (MM/AA)", max_length=5, required=False)
    card_cvv = forms.CharField(label="CVV", max_length=4, required=False)

    def clean_card_number(self):
        return re.sub(r"\D", "", self.cleaned_data.get("card_number", ""))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("payment_method") == Order.Payment.CREDIT_CARD:
            digits = cleaned.get("card_number", "")
            if not cleaned.get("card_name"):
                self.add_error("card_name", "Informe o nome no cartão.")
            if len(digits) < 13:
                self.add_error("card_number", "Número de cartão inválido.")
            if not cleaned.get("card_expiry"):
                self.add_error("card_expiry", "Informe a validade.")
            if len(cleaned.get("card_cvv", "")) < 3:
                self.add_error("card_cvv", "CVV inválido.")
        return cleaned

    def to_order_data(self) -> dict:
        """Converte o form validado no dict que o OrderService espera."""
        c = self.cleaned_data
        data = {
            "recipient": c["recipient"], "phone": c["phone"], "zip_code": c["zip_code"],
            "street": c["street"], "number_addr": c["number_addr"], "complement": c["complement"],
            "district": c["district"], "city": c["city"], "state": c["state"],
            "payment_method": c["payment_method"],
        }
        if c["payment_method"] == Order.Payment.CREDIT_CARD:
            data["card_last4"] = c["card_number"][-4:]
        return data
