from django.contrib import admin

from .models import Coupon, Promotion


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "badge", "is_active", "order", "starts_at", "ends_at")
    list_filter = ("kind", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "subtitle")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_order", "is_active", "used_count", "usage_limit")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
