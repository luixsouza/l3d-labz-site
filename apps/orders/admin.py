from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity", "line_total")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "payment_method", "payment_status", "total", "created_at")
    list_filter = ("status", "payment_method", "payment_status")
    search_fields = ("number", "user__email", "recipient")
    readonly_fields = ("number", "subtotal", "discount", "shipping", "total", "created_at", "updated_at")
    inlines = [OrderItemInline]
    list_select_related = ("user",)
