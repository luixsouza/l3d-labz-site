from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "accent", "is_highlighted", "order")
    list_editable = ("order", "is_highlighted")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "compare_at_price", "stock", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active", "material")
    list_editable = ("price", "stock", "is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description")}),
        ("Preço", {"fields": ("price", "compare_at_price")}),
        ("Visual", {"fields": ("image",)}),
        ("Modelos 3D", {"fields": ("model_3d", "model_stl")}),
        ("Estoque & métricas", {"fields": ("stock", "rating", "sales_count")}),
        ("Impressão 3D", {"fields": ("material", "dimensions", "print_time_hours")}),
        ("Flags", {"fields": ("is_featured", "is_active")}),
    )
