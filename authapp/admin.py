from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import StaffPermission, User


class StaffPermissionInline(admin.StackedInline):
    model = StaffPermission
    can_delete = False
    verbose_name_plural = 'Staff Permissions'
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extends Django's default UserAdmin to show role and phone."""

    list_display = ('username', 'email', 'get_full_name', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Add role + phone to the user edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Portal Settings', {
            'fields': ('role', 'phone'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Portal Settings', {
            'fields': ('role', 'phone'),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """Only show StaffPermission inline for staff-role users."""
        if obj and obj.role == User.Role.STAFF:
            return [StaffPermissionInline(self.model, self.admin_site)]
        return []


@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'can_manage_products', 'can_manage_distributors',
        'can_manage_orders', 'can_manage_invoices',
        'can_manage_announcements', 'can_view_analytics', 'can_manage_settings',
    )
    search_fields = ('user__username', 'user__email')
