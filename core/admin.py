"""
core/admin.py — Hardik International Portal
Registers all Phase 1 models with the Django admin site.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Announcement,
    CompanySetting,
    Distributor,
    Invoice,
    LedgerEntry,
    Order,
    OrderItem,
    Product,
    ProductCategory,
)


# ---------------------------------------------------------------------------
# Distributor
# ---------------------------------------------------------------------------

@admin.register(Distributor)
class DistributorAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'code', 'owner_name', 'city', 'status', 'credit_limit', 'joined_on')
    list_filter = ('status', 'state')
    search_fields = ('business_name', 'code', 'email', 'owner_name', 'gst_number')
    readonly_fields = ('code', 'created_at', 'updated_at')
    fieldsets = (
        ('Business Info', {
            'fields': ('code', 'business_name', 'owner_name', 'email', 'phone', 'alternate_phone', 'status', 'notes')
        }),
        ('Address', {
            'fields': ('street_address', 'city', 'state', 'pincode')
        }),
        ('Compliance', {
            'fields': ('gst_number', 'drug_license_number', 'pan_number')
        }),
        ('Financial', {
            'fields': ('credit_limit', 'payment_terms_days')
        }),
        ('Bank Details', {
            'fields': ('bank_name', 'account_number', 'ifsc_code')
        }),
        ('Meta', {
            'fields': ('user', 'joined_on', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'mrp', 'selling_price', 'stock_quantity', 'stock_status_badge', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'manufacturer', 'batch_number')
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Stock Status')
    def stock_status_badge(self, obj):
        colours = {'in': 'green', 'low': 'orange', 'out': 'red'}
        labels = {'in': 'In Stock', 'low': 'Low', 'out': 'Out'}
        status = obj.stock_status
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colours.get(status, 'grey'),
            labels.get(status, status),
        )


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'distributor', 'order_date', 'status', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('order_id', 'distributor__business_name')
    inlines = [OrderItemInline]
    readonly_fields = ('order_id', 'total_amount', 'created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Invoices & Ledger
# ---------------------------------------------------------------------------

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'distributor', 'invoice_date', 'due_date', 'amount', 'status')
    list_filter = ('status', 'invoice_date')
    search_fields = ('invoice_number', 'distributor__business_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('distributor', 'entry_date', 'reference', 'entry_type', 'debit', 'credit', 'balance')
    list_filter = ('entry_type', 'entry_date')
    search_fields = ('distributor__business_name', 'reference', 'description')
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'published_at')
    list_filter = ('category', 'status')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')


# ---------------------------------------------------------------------------
# Company Settings
# ---------------------------------------------------------------------------

@admin.register(CompanySetting)
class CompanySettingAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'support_email', 'support_phone', 'currency')

    def has_add_permission(self, request):
        # Enforce singleton — block creation if one already exists
        return not CompanySetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Never delete the singleton
