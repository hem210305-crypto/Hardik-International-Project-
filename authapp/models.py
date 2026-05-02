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


class StaffPermission(models.Model):
    """
    Granular, per-module access control for Staff users.
    Each boolean controls whether the staff member can access that module.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_permissions',
        limit_choices_to={'role': User.Role.STAFF},
    )

    # Module-level access flags
    can_manage_products = models.BooleanField(default=False)
    can_manage_distributors = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    can_manage_invoices = models.BooleanField(default=False)
    can_manage_announcements = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Staff Permission'
        verbose_name_plural = 'Staff Permissions'

    def __str__(self):
        return f"Permissions → {self.user.username}"

    def has_module_access(self, module: str) -> bool:
        """Check access dynamically by module name string."""
        return getattr(self, f'can_manage_{module}', False)

