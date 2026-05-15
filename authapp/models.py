from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.
    A single User can be an Admin, Staff, or Distributor.
    The role field controls which portal the user accesses.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'
        DISTRIBUTOR = 'distributor', 'Distributor'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DISTRIBUTOR,
    )
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True, help_text="e.g. Manager, Sales Executive")

    class Meta:
        ordering = ['username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # -------------------------------------------------------------------------
    # Role helpers
    # -------------------------------------------------------------------------
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF

    @property
    def is_distributor(self):
        return self.role == self.Role.DISTRIBUTOR

    @property
    def staff_id(self):
        if self.role == self.Role.STAFF:
            return f"STF-{self.id:03d}"
        return None


class StaffPermission(models.Model):
    """
    Granular, per-module access control for Staff users.
    Matches the Access Control Panel design with View/Create/Edit/Delete etc.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_permissions',
        limit_choices_to={'role': User.Role.STAFF},
    )

    # Dashboard
    dashboard_view = models.BooleanField(default=False)

    # Distributors
    distributors_view = models.BooleanField(default=False)
    distributors_create = models.BooleanField(default=False)
    distributors_edit = models.BooleanField(default=False)
    distributors_delete = models.BooleanField(default=False)

    # Products
    products_view = models.BooleanField(default=False)
    products_create = models.BooleanField(default=False)
    products_edit = models.BooleanField(default=False)
    products_delete = models.BooleanField(default=False)

    # Orders
    orders_view = models.BooleanField(default=False)
    orders_create = models.BooleanField(default=False)
    orders_edit = models.BooleanField(default=False)
    orders_delete = models.BooleanField(default=False)
    orders_approve = models.BooleanField(default=False)

    # Invoices
    invoices_view = models.BooleanField(default=False)
    invoices_create = models.BooleanField(default=False)
    invoices_edit = models.BooleanField(default=False)
    invoices_delete = models.BooleanField(default=False)
    invoices_download = models.BooleanField(default=False)

    # Announcements
    announcements_view = models.BooleanField(default=False)
    announcements_create = models.BooleanField(default=False)
    announcements_edit = models.BooleanField(default=False)
    announcements_delete = models.BooleanField(default=False)

    # Analytics
    analytics_view = models.BooleanField(default=False)
    analytics_export = models.BooleanField(default=False)

    # Settings
    settings_view = models.BooleanField(default=False)
    settings_edit = models.BooleanField(default=False)

    # Expiry
    access_expiry = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Staff Permission'
        verbose_name_plural = 'Staff Permissions'

    def __str__(self):
        return f"Permissions → {self.user.username}"

    def active_permissions_count(self):
        """Count how many permission flags are set to True."""
        count = 0
        for field in self._meta.fields:
            if isinstance(field, models.BooleanField) and getattr(self, field.name):
                count += 1
        return count

    def get_active_modules(self):
        """Return a list of module names that have at least one permission active."""
        modules = []
        mapping = {
            'dashboard': 'Dashboard',
            'distributors': 'Distributors',
            'products': 'Products',
            'orders': 'Orders',
            'invoices': 'Invoices',
            'announcements': 'Announcements',
            'analytics': 'Analytics',
            'settings': 'Settings',
        }
        for prefix, name in mapping.items():
            # Check if any field starting with prefix is True
            is_active = any(
                getattr(self, f.name) for f in self._meta.fields 
                if f.name.startswith(f"{prefix}_") and isinstance(f, models.BooleanField)
            )
            if is_active:
                modules.append(name)
        return modules

