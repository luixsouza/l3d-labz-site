"""Admin do catálogo — turbinado para cadastro manual visual."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage


# ---------------------------------------------------------------------------
# Helper de thumbnail
# ---------------------------------------------------------------------------

def _thumb_html(image_field, height="48px"):
    """Retorna um <img> seguro via format_html para um ImageField.

    Se o campo estiver vazio, devolve "—".
    """
    if not image_field:
        return "—"
    return format_html(
        '<img src="{}" height="{}" style="object-fit:cover;border-radius:4px;" />',
        image_field.url,
        height,
    )


# ---------------------------------------------------------------------------
# Inline de galeria
# ---------------------------------------------------------------------------

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ("preview",)
    fields = ("image", "preview", "order")

    @admin.display(description="pré-visualização")
    def preview(self, obj):
        """Thumbnail da imagem de galeria no inline."""
        return _thumb_html(obj.image, height="60px")


# ---------------------------------------------------------------------------
# Admin de Categoria (não alterar comportamento)
# ---------------------------------------------------------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "accent", "is_highlighted", "order")
    list_editable = ("order", "is_highlighted")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


# ---------------------------------------------------------------------------
# Admin de Produto — cadastro manual visual
# ---------------------------------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # --- listagem ---
    list_display = (
        "thumb", "name", "category",
        "price", "compare_at_price",
        "stock", "is_featured", "is_active",
    )
    list_filter = ("category", "is_featured", "is_active", "material")
    list_editable = ("price", "stock", "is_featured", "is_active")

    # --- formulário ---
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    autocomplete_fields = ("category",)
    inlines = (ProductImageInline,)
    readonly_fields = ("image_preview",)

    # Fieldsets ordenados para cadastro manual:
    # o que o lojista preenche primeiro em destaque, automação/scraper colapsados.
    fieldsets = (
        (None, {
            "fields": ("category", "name", "slug", "description"),
        }),
        ("Imagem principal", {
            "fields": ("image", "image_preview"),
        }),
        ("Preço & estoque", {
            "fields": ("price", "compare_at_price", "stock"),
        }),
        ("Impressão 3D", {
            "fields": ("material", "dimensions", "print_time_hours"),
        }),
        ("Destaque", {
            "fields": ("is_featured", "is_active"),
        }),
        ("Modelos 3D (download/visualizador)", {
            "fields": ("model_3d", "model_stl"),
            "classes": ("collapse",),
        }),
        ("Automação / scraper", {
            "fields": ("rating", "sales_count", "filament_grams", "color_count", "image_url"),
            "classes": ("collapse",),
        }),
    )

    # --- métodos de listagem ---

    @admin.display(description="foto")
    def thumb(self, obj):
        """Thumbnail pequena na listagem (48 px)."""
        return _thumb_html(obj.image, height="48px")

    # --- métodos de formulário ---

    @admin.display(description="pré-visualização da imagem")
    def image_preview(self, obj):
        """Preview maior da imagem principal dentro do form (200 px)."""
        return _thumb_html(obj.image, height="200px")
