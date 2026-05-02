"""
core/models.py — Hardik International Portal
Phase 1: Complete Database Layer

Models defined here:
  • TimestampedModel  – abstract base with created_at / updated_at
  • Distributor       – distributor business account
  • ProductCategory   – product taxonomy
  • Product           – catalogue item with stock tracking
  • Order / OrderItem – order header + line items
  • Invoice           – billing document linked to an order
  • LedgerEntry       – running debit / credit ledger per distributor
  • Announcement      – notices visible in the distributor portal
  • CompanySetting    – singleton for company-wide configuration
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class TimestampedModel(models.Model):
    """Provides created_at and updated_at on every inheriting model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Distributor
# ---------------------------------------------------------------------------

class Distributor(TimestampedModel):
    """
    Represents a registered distributor (business) in the network.
    A Distributor is linked to a User account with the 'distributor' role.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        SUSPENDED = 'suspended', 'Suspended'

    # Link to the auth user account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='distributor_profile',
        null=True,
        blank=True,
    )

    # Unique business code  (e.g. DIST-0001)
    code = models.CharField(max_length=20, unique=True)

    # Business information
    business_name = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Address
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120)
    pincode = models.CharField(max_length=10)

    # Compliance documents
    gst_number = models.CharField(max_length=20, blank=True)
    drug_license_number = models.CharField(max_length=40, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)

    # Financial terms
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    payment_terms_days = models.PositiveIntegerField(default=30)

    # Bank details
    bank_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)

    # Misc
    notes = models.TextField(blank=True)
    joined_on = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ['business_name']
        verbose_name = 'Distributor'
        verbose_name_plural = 'Distributors'

    def __str__(self):
        return f"{self.business_name} ({self.code})"

    # ------------------------------------------------------------------
    # Computed properties (no extra DB calls if invoices are prefetched)
    # ------------------------------------------------------------------

    @property
    def location(self):
        return f"{self.city}, {self.state}"

    @property
    def current_outstanding(self) -> Decimal:
        """Sum of all unpaid / overdue / partial invoices."""
        result = self.invoices.filter(
            status__in=[Invoice.Status.UNPAID, Invoice.Status.OVERDUE, Invoice.Status.PARTIAL]
        ).aggregate(total=models.Sum('amount'))
        return result['total'] or Decimal('0')

    @property
    def total_paid(self) -> Decimal:
        result = self.invoices.filter(
            status=Invoice.Status.PAID
        ).aggregate(total=models.Sum('amount'))
        return result['total'] or Decimal('0')

    @property
    def credit_available(self) -> Decimal:
        return max(Decimal('0'), self.credit_limit - self.current_outstanding)

    @property
    def latest_ledger_balance(self) -> Decimal:
        entry = self.ledger_entries.order_by('-entry_date', '-id').first()
        return entry.balance if entry else Decimal('0')


# ---------------------------------------------------------------------------
# Product Catalogue
# ---------------------------------------------------------------------------

class ProductCategory(TimestampedModel):
    """Taxonomy node for grouping products (e.g. Tablets, Injections)."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimestampedModel):
    """
    A single catalogue item.
    stock_quantity is decremented automatically on order placement.
    """

    class StockStatus(models.TextChoices):
        IN_STOCK = 'in', 'In Stock'
        LOW_STOCK = 'low', 'Low Stock'
        OUT_OF_STOCK = 'out', 'Out of Stock'

    # Identification
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
    )
    manufacturer = models.CharField(max_length=255, default='Hardik International Pvt Ltd')

    # Batch / compliance
    batch_number = models.CharField(max_length=50, blank=True)
    hsn_code = models.CharField(max_length=20, blank=True, verbose_name='HSN Code')
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Pricing
    mrp = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='MRP (₹)')
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Selling Price (₹)')

    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(
        default=0,
        help_text='Alert threshold — stock at or below this is considered low.',
    )

    # Display
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.name} [{self.sku}]"

    @property
    def stock_status(self) -> str:
        if self.stock_quantity == 0:
            return self.StockStatus.OUT_OF_STOCK
        if self.stock_quantity <= self.min_stock_level:
            return self.StockStatus.LOW_STOCK
        return self.StockStatus.IN_STOCK

    @property
    def discount_percentage(self) -> Decimal:
        """Percentage discount of selling price vs MRP."""
        if self.mrp > 0:
            return round(((self.mrp - self.selling_price) / self.mrp) * 100, 2)
        return Decimal('0')


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class Order(TimestampedModel):
    """
    A distributor's purchase order.
    total_amount is stored (denormalised) for quick reporting.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'Paid'
        UNPAID = 'unpaid', 'Unpaid'
        PARTIAL = 'partial', 'Partial'

    # Unique human-readable reference (e.g. ORD-2026-0001)
    order_id = models.CharField(max_length=30, unique=True)

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='orders',
    )

    # Dates
    order_date = models.DateField(default=timezone.now)
    dispatched_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    # Logistics metadata
    draft_person_name = models.CharField(max_length=120, blank=True)
    courier_name = models.CharField(max_length=120, blank=True)
    sales_person_name = models.CharField(max_length=120, blank=True)
    delivery_note = models.TextField(blank=True)

    # Denormalised total (recalculated on save)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['-order_date', '-id']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return self.order_id

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())

    def recalculate_total(self):
        """Recompute and save total_amount from line items."""
        total = self.items.aggregate(t=models.Sum('line_total'))['t'] or Decimal('0')
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    """A single product line within an Order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.order.order_id} — {self.product.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Always recompute line_total before saving
        self.line_total = Decimal(str(self.unit_price)) * self.quantity
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Invoicing
# ---------------------------------------------------------------------------

class Invoice(TimestampedModel):
    """Billing document generated for an Order."""

    class Status(models.TextChoices):
        UNPAID = 'unpaid', 'Unpaid'
        PARTIAL = 'partial', 'Partial'
        PAID = 'paid', 'Paid'
        OVERDUE = 'overdue', 'Overdue'

    invoice_number = models.CharField(max_length=30, unique=True)
    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='invoices',
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
    )

    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)

    class Meta:
        ordering = ['-invoice_date', '-id']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return self.invoice_number

    @property
    def is_overdue(self) -> bool:
        from datetime import date
        return self.status != self.Status.PAID and self.due_date < date.today()


# ---------------------------------------------------------------------------
# Ledger (double-entry style running balance)
# ---------------------------------------------------------------------------

class LedgerEntry(TimestampedModel):
    """
    One row per financial event for a distributor.
    balance = running balance after this entry.
    Positive balance = distributor owes money.
    """

    class EntryType(models.TextChoices):
        ORDER = 'order', 'Order'
        PAYMENT = 'payment', 'Payment Received'
        CREDIT = 'credit', 'Credit Note'
        DEBIT = 'debit', 'Debit Note'

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name='ledger_entries',
    )
    entry_date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=50, help_text='Invoice number or payment reference')
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, default=EntryType.ORDER)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['-entry_date', '-id']
        verbose_name = 'Ledger Entry'
        verbose_name_plural = 'Ledger Entries'

    def __str__(self):
        return f"{self.distributor.business_name} — {self.reference}"


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------

class Announcement(TimestampedModel):
    """Portal-wide notices shown on the distributor dashboard."""

    class Category(models.TextChoices):
        GENERAL = 'general', 'General'
        IMPORTANT = 'important', 'Important'
        URGENT = 'urgent', 'Urgent'
        MAINTENANCE = 'maintenance', 'Maintenance'

    class PublishStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    content = models.TextField()
    image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PublishStatus.choices,
        default=PublishStatus.PUBLISHED,
    )
    published_at = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-published_at', '-id']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# Company Settings (singleton)
# ---------------------------------------------------------------------------

class CompanySetting(models.Model):
    """
    Singleton model — only one row (pk=1) should ever exist.
    Use CompanySetting.objects.get_or_create(pk=1) to retrieve it.
    """

    company_name = models.CharField(max_length=255, default='Hardik International Pvt Ltd')
    support_email = models.EmailField(default='support@hardikinternational.com')
    support_phone = models.CharField(max_length=20, default='+91 99999 12345')
    support_hours = models.CharField(max_length=120, default='Mon–Sat, 10:00 AM to 6:00 PM IST')
    currency = models.CharField(max_length=10, default='INR')

    # Security
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    password_expiry_days = models.PositiveIntegerField(default=90)
    two_factor_enabled = models.BooleanField(default=False)

    # Notification toggles
    email_notifications = models.BooleanField(default=True)
    order_notifications = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    payment_reminders = models.BooleanField(default=True)

    # Email templates
    order_confirmation_template = models.TextField(default='Your order has been confirmed.')
    payment_reminder_template = models.TextField(default='Your payment is due soon.')
    welcome_email_template = models.TextField(default='Welcome to the Hardik distributor network.')

    last_backup_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Company Setting'
        verbose_name_plural = 'Company Settings'

    def __str__(self):
        return self.company_name
