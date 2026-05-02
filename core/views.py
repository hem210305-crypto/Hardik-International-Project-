"""
core/views.py — Hardik International Portal
Phase 1: Clean, error-free view layer for both portals.
"""

import datetime
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render

from authapp.models import StaffPermission
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

User = get_user_model()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_company_settings():
    """Return the singleton CompanySetting row."""
    obj, _ = CompanySetting.objects.get_or_create(pk=1)
    return obj


def role_required(*roles):
    """
    Decorator to restrict a view to specific user roles.
    Superusers always bypass the check.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def get_distributor(user):
    """Return the Distributor linked to this user, or None."""
    try:
        return user.distributor_profile
    except Distributor.DoesNotExist:
        return None


def generate_order_id():
    count = Order.objects.count() + 1
    return f"ORD-2026-{count:04d}"


def generate_invoice_number():
    count = Invoice.objects.count() + 1
    return f"INV-2026-{count:04d}"


def compute_next_balance(distributor, debit=Decimal('0'), credit=Decimal('0')):
    last = distributor.ledger_entries.order_by('-entry_date', '-id').first()
    prev = last.balance if last else Decimal('0')
    return prev + Decimal(str(debit)) - Decimal(str(credit))


def dist_ctx(request, section, title, subtitle, **extra):
    ctx = {
        'company_settings': get_company_settings(),
        'distributor': get_distributor(request.user),
        'section': section,
        'page_title': title,
        'page_subtitle': subtitle,
    }
    ctx.update(extra)
    return ctx


def admin_ctx(request, section, title, subtitle, **extra):
    ctx = {
        'company_settings': get_company_settings(),
        'section': section,
        'page_title': title,
        'page_subtitle': subtitle,
    }
    ctx.update(extra)
    return ctx


# ---------------------------------------------------------------------------
# Portal home — smart redirect by role
# ---------------------------------------------------------------------------

def portal_home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_admin:
        return redirect('admin_dashboard')
    return redirect('dashboard')


# ---------------------------------------------------------------------------
# Cart helper (session-based)
# ---------------------------------------------------------------------------

def _cart_data(request):
    cart = request.session.get('cart', {})
    if not cart:
        return [], Decimal('0'), 0
    products = Product.objects.filter(
        id__in=cart.keys(), is_active=True
    ).select_related('category')
    items, total = [], Decimal('0')
    for p in products:
        qty = int(cart.get(str(p.id), 0))
        line = p.selling_price * qty
        items.append({'product': p, 'quantity': qty, 'line_total': line})
        total += line
    return items, total, len(items)


# ---------------------------------------------------------------------------
# Distributor Portal
# ---------------------------------------------------------------------------

@role_required('distributor')
def dashboard(request):
    distributor = get_distributor(request.user)
    recent_orders = distributor.orders.prefetch_related('items').all()[:4]
    recent_invoices = distributor.invoices.all()[:4]
    announcements = Announcement.objects.filter(
        status=Announcement.PublishStatus.PUBLISHED
    )[:5]
    featured = Product.objects.filter(is_active=True).order_by('-created_at').first()
    ctx = dist_ctx(
        request, 'dashboard', 'Dashboard',
        f'Welcome back, {request.user.get_full_name() or request.user.username}!',
        metrics={
            'outstanding': distributor.current_outstanding,
            'orders_count': distributor.orders.count(),
            'paid_amount': distributor.total_paid,
            'credit_available': distributor.credit_available,
        },
        recent_orders=recent_orders,
        recent_invoices=recent_invoices,
        announcements=announcements,
        featured_product=featured,
    )
    return render(request, 'core/distributor_dashboard.html', ctx)


@role_required('distributor')
def place_order(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        cart = request.session.get('cart', {})
        if product_id:
            current_qty = int(cart.get(product_id, 0))
            if action == 'add':
                cart[product_id] = current_qty + max(1, int(request.POST.get('quantity', 1)))
                messages.success(request, 'Product added to cart.')
            elif action == 'update':
                new_qty = max(0, int(request.POST.get('quantity', 1)))
                if new_qty == 0:
                    cart.pop(product_id, None)
                else:
                    cart[product_id] = new_qty
            elif action == 'remove':
                cart.pop(product_id, None)
                messages.info(request, 'Item removed.')
        request.session['cart'] = cart
        return redirect('place_order')

    search = request.GET.get('search', '').strip()
    category_slug = request.GET.get('category', '')
    products = Product.objects.filter(is_active=True).select_related('category')
    if search:
        products = products.filter(name__icontains=search)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    cart_items, cart_total, cart_count = _cart_data(request)
    ctx = dist_ctx(
        request, 'place-order', 'Place Order', 'Browse and add products to your cart.',
        products=products,
        categories=ProductCategory.objects.all(),
        selected_category=category_slug,
        search=search,
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count,
    )
    return render(request, 'core/place_order.html', ctx)


@role_required('distributor')
def checkout(request):
    distributor = get_distributor(request.user)
    cart_items, cart_total, cart_count = _cart_data(request)
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('place_order')

    if request.method == 'POST':
        if cart_total > distributor.credit_available:
            messages.error(
                request,
                f'Order total ₹{cart_total} exceeds your available credit ₹{distributor.credit_available}.'
            )
            return redirect('checkout')

        order = Order.objects.create(
            order_id=generate_order_id(),
            distributor=distributor,
            status=Order.Status.PENDING,
            payment_status=Order.PaymentStatus.UNPAID,
            draft_person_name=request.POST.get('draft_person_name', '').strip(),
            courier_name=request.POST.get('courier_name', '').strip(),
            sales_person_name=request.POST.get('sales_person_name', '').strip(),
            delivery_note=request.POST.get('delivery_note', '').strip(),
            total_amount=cart_total,
        )
        for item in cart_items:
            p, qty = item['product'], item['quantity']
            OrderItem.objects.create(
                order=order, product=p, quantity=qty,
                unit_price=p.selling_price, line_total=p.selling_price * qty,
            )
            if p.stock_quantity >= qty:
                p.stock_quantity -= qty
                p.save(update_fields=['stock_quantity'])

        due_date = datetime.date.today() + datetime.timedelta(days=distributor.payment_terms_days)
        invoice = Invoice.objects.create(
            invoice_number=generate_invoice_number(),
            distributor=distributor, order=order,
            invoice_date=datetime.date.today(), due_date=due_date,
            amount=cart_total, status=Invoice.Status.UNPAID,
        )
        LedgerEntry.objects.create(
            distributor=distributor,
            entry_date=datetime.date.today(),
            description=f'Order placed — {order.order_id}',
            reference=invoice.invoice_number,
            entry_type=LedgerEntry.EntryType.ORDER,
            debit=cart_total, credit=Decimal('0'),
            balance=compute_next_balance(distributor, debit=cart_total),
        )
        request.session['cart'] = {}
        request.session['last_order_id'] = order.id
        messages.success(request, f'Order {order.order_id} placed successfully!')
        return redirect('order_confirmed')

    ctx = dist_ctx(
        request, 'place-order', 'Checkout', 'Review your order before placing.',
        cart_items=cart_items, cart_total=cart_total, cart_count=cart_count,
    )
    return render(request, 'core/checkout.html', ctx)


@role_required('distributor')
def order_confirmed(request):
    order_id = request.session.get('last_order_id')
    distributor = get_distributor(request.user)
    order = get_object_or_404(Order, id=order_id, distributor=distributor)
    ctx = dist_ctx(
        request, 'place-order', 'Order Confirmed', 'Your order has been placed.',
        order=order,
    )
    return render(request, 'core/order_confirmed.html', ctx)


@role_required('distributor')
def order_history(request):
    distributor = get_distributor(request.user)
    search = request.GET.get('search', '').strip()
    orders = distributor.orders.prefetch_related('items').all()
    if search:
        orders = orders.filter(order_id__icontains=search)
    ctx = dist_ctx(
        request, 'order-history', 'Order History', 'View and track all your orders.',
        orders=orders, search=search,
    )
    return render(request, 'core/order_history.html', ctx)


@role_required('distributor')
def bills_invoices(request):
    distributor = get_distributor(request.user)
    search = request.GET.get('search', '').strip()
    invoices = distributor.invoices.all()
    if search:
        invoices = invoices.filter(invoice_number__icontains=search)
    ctx = dist_ctx(
        request, 'bills-invoices', 'Bills & Invoices', 'View and download your invoices.',
        invoices=invoices,
        totals={
            'paid': distributor.total_paid,
            'unpaid': distributor.current_outstanding,
            'count': distributor.invoices.count(),
        },
        search=search,
    )
    return render(request, 'core/bills_invoices.html', ctx)


@role_required('distributor')
def ledger_payments(request):
    distributor = get_distributor(request.user)
    ctx = dist_ctx(
        request, 'ledger-payments', 'Ledger & Payment Outstanding',
        'Track your financial statement.',
        ledger_entries=distributor.ledger_entries.all(),
        summary={
            'outstanding': distributor.current_outstanding,
            'paid': distributor.total_paid,
            'balance': distributor.latest_ledger_balance,
        },
    )
    return render(request, 'core/ledger_payments.html', ctx)


@role_required('distributor')
def product_catalogue(request):
    search = request.GET.get('search', '').strip()
    category_slug = request.GET.get('category', '')
    products = Product.objects.filter(is_active=True).select_related('category')
    if search:
        products = products.filter(name__icontains=search)
    if category_slug:
        products = products.filter(category__slug=category_slug)
    ctx = dist_ctx(
        request, 'catalogue', 'Product Catalogue', 'Browse our complete product range.',
        products=products,
        categories=ProductCategory.objects.all(),
        search=search,
        selected_category=category_slug,
    )
    return render(request, 'core/product_catalogue.html', ctx)


@role_required('distributor')
def announcements(request):
    items = Announcement.objects.filter(status=Announcement.PublishStatus.PUBLISHED)
    ctx = dist_ctx(
        request, 'announcements', 'Announcements', 'Stay updated with the latest news.',
        announcements=items,
    )
    return render(request, 'core/announcements.html', ctx)


@role_required('distributor')
def profile_support(request):
    distributor = get_distributor(request.user)
    if request.method == 'POST':
        for field in ('owner_name', 'phone', 'email', 'street_address', 'city',
                      'state', 'pincode', 'bank_name', 'account_number', 'ifsc_code'):
            value = request.POST.get(field, '').strip()
            if value:
                setattr(distributor, field, value)
        distributor.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile_support')
    settings = get_company_settings()
    ctx = dist_ctx(
        request, 'profile-support', 'Profile & Support', 'Manage your account and get help.',
        support_phone=settings.support_phone,
        support_email=settings.support_email,
        support_hours=settings.support_hours,
    )
    return render(request, 'core/profile_support.html', ctx)


# ---------------------------------------------------------------------------
# Admin Portal
# ---------------------------------------------------------------------------

@role_required('admin')
def admin_dashboard(request):
    orders = Order.objects.all()
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level')
    ).select_related('category')[:5]
    pending_distributors = Distributor.objects.filter(
        status=Distributor.Status.INACTIVE
    ).order_by('-id')[:5]
    ctx = admin_ctx(
        request, 'dashboard', 'Admin Dashboard', 'Welcome back, Administrator',
        metrics={
            'distributors': Distributor.objects.count(),
            'products': Product.objects.count(),
            'orders': orders.count(),
            'revenue': orders.aggregate(t=Sum('total_amount'))['t'] or Decimal('0'),
            'pending': orders.filter(status=Order.Status.PENDING).count(),
        },
        recent_orders=orders.select_related('distributor').order_by('-order_date')[:6],
        low_stock_products=low_stock_products,
        pending_distributors=pending_distributors,
    )
    return render(request, 'core/admin_dashboard.html', ctx)


@role_required('admin')
def admin_distributors(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        if action == 'delete':
            d_id = request.POST.get('distributor_id')
            try:
                distributor = Distributor.objects.get(id=d_id)
                if distributor.user:
                    distributor.user.delete()
                distributor.delete()
                messages.success(request, "Distributor deleted successfully.")
            except Distributor.DoesNotExist:
                messages.error(request, "Distributor not found.")
            return redirect('admin_distributors')
            
        elif action == 'edit':
            d_id = request.POST.get('distributor_id')
            try:
                distributor = Distributor.objects.get(id=d_id)
                distributor.business_name = request.POST.get('business_name', '').strip()
                distributor.owner_name = request.POST.get('owner_name', '').strip()
                distributor.phone = request.POST.get('phone', '').strip()
                distributor.credit_limit = Decimal(request.POST.get('credit_limit', '0') or '0')
                distributor.payment_terms_days = int(request.POST.get('payment_terms_days', '30') or 30)
                distributor.status = request.POST.get('status', Distributor.Status.ACTIVE)
                distributor.save()
                messages.success(request, "Distributor updated successfully.")
            except Distributor.DoesNotExist:
                messages.error(request, "Distributor not found.")
            return redirect('admin_distributors')

        # create logic defaults
        email = request.POST.get('email', '').strip()
        
        # Check for duplicates before attempting to create
        if Distributor.objects.filter(email=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, f"A distributor or user with the email '{email}' already exists. Please use a different email.")
        else:
            try:
                code = f"DIST-{Distributor.objects.count() + 1:04d}"
                distributor = Distributor.objects.create(
                    code=code,
                    business_name=request.POST.get('business_name', '').strip(),
                    owner_name=request.POST.get('owner_name', '').strip(),
                    email=email,
                    phone=request.POST.get('phone', '').strip(),
                    alternate_phone=request.POST.get('alternate_phone', '').strip(),
                    street_address=request.POST.get('street_address', '').strip(),
                    city=request.POST.get('city', '').strip(),
                    state=request.POST.get('state', '').strip(),
                    pincode=request.POST.get('pincode', '').strip(),
                    gst_number=request.POST.get('gst_number', '').strip(),
                    drug_license_number=request.POST.get('drug_license_number', '').strip(),
                    pan_number=request.POST.get('pan_number', '').strip(),
                    bank_name=request.POST.get('bank_name', '').strip(),
                    account_number=request.POST.get('account_number', '').strip(),
                    ifsc_code=request.POST.get('ifsc_code', '').strip(),
                    notes=request.POST.get('notes', '').strip(),
                    credit_limit=Decimal(request.POST.get('credit_limit', '0') or '0'),
                    payment_terms_days=int(request.POST.get('payment_terms_days', '30') or 30),
                    status=request.POST.get('status', Distributor.Status.ACTIVE),
                )
                username = email.split('@')[0].lower() if email else code.lower()
                user = User.objects.create_user(
                    username=username, email=email, password='Distributor@123',
                    first_name=distributor.business_name,
                )
                user.role = User.Role.DISTRIBUTOR
                user.save()
                distributor.user = user
                distributor.save(update_fields=['user'])
                messages.success(request, f'Distributor created successfully. Login: {username} / Distributor@123')
            except Exception as e:
                messages.error(request, f"Error creating distributor: {str(e)}")
                
        return redirect('admin_distributors')

    distributors = Distributor.objects.all().order_by('-id')
    
    # Filtering logic
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    from django.db.models import Q
    if q:
        distributors = distributors.filter(
            Q(business_name__icontains=q) | 
            Q(code__icontains=q) | 
            Q(city__icontains=q) |
            Q(owner_name__icontains=q)
        )
    
    # Store totals *before* status filter so the summary cards still show absolute counts
    totals = {
        'active': Distributor.objects.filter(status=Distributor.Status.ACTIVE).count(),
        'inactive': Distributor.objects.filter(status=Distributor.Status.INACTIVE).count(),
        'suspended': Distributor.objects.filter(status=Distributor.Status.SUSPENDED).count(),
    }
    
    if status_filter:
        distributors = distributors.filter(status__iexact=status_filter)

    ctx = admin_ctx(
        request, 'distributors', 'Distributors Management', 'Manage distributor accounts.',
        distributors=distributors,
        totals=totals,
    )
    return render(request, 'core/admin_distributors.html', ctx)


@role_required('admin')
def admin_products(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'delete':
            product_id = request.POST.get('product_id')
            try:
                product = Product.objects.get(id=product_id)
                product.delete()
                messages.success(request, 'Product deleted successfully.')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found.')
        else:
            cat_name = request.POST.get('category', 'General').strip() or 'General'
            category, _ = ProductCategory.objects.get_or_create(name=cat_name)
            Product.objects.create(
                category=category,
                sku=request.POST.get('sku', '').strip() or f"PRD-{Product.objects.count() + 1:04d}",
                name=request.POST.get('name', '').strip(),
                manufacturer=request.POST.get('manufacturer', 'Hardik International Pvt Ltd').strip(),
                batch_number=request.POST.get('batch_number', '').strip(),
                hsn_code=request.POST.get('hsn_code', '').strip(),
                manufacture_date=request.POST.get('manufacture_date') or None,
                expiry_date=request.POST.get('expiry_date') or None,
                mrp=Decimal(request.POST.get('mrp', '0') or '0'),
                selling_price=Decimal(request.POST.get('selling_price', '0') or '0'),
                stock_quantity=int(request.POST.get('stock_quantity', '0') or 0),
                min_stock_level=int(request.POST.get('min_stock_level', '0') or 0),
                description=request.POST.get('description', '').strip(),
            )
            messages.success(request, 'Product added successfully.')
        return redirect('admin_products')

    products = Product.objects.select_related('category').all().order_by('-id')
    
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    from django.db.models import Q, F
    if q:
        products = products.filter(
            Q(name__icontains=q) | 
            Q(sku__icontains=q) | 
            Q(category__name__icontains=q)
        )
        
    totals = {
        'total': Product.objects.count(),
        'in_stock': Product.objects.filter(stock_quantity__gt=F('min_stock_level')).count(),
        'low_stock': Product.objects.filter(stock_quantity__gt=0, stock_quantity__lte=F('min_stock_level')).count(),
        'out': Product.objects.filter(stock_quantity=0).count(),
    }
    
    if status_filter == 'in':
        products = products.filter(stock_quantity__gt=F('min_stock_level'))
    elif status_filter == 'low':
        products = products.filter(stock_quantity__gt=0, stock_quantity__lte=F('min_stock_level'))
    elif status_filter == 'out':
        products = products.filter(stock_quantity=0)

    ctx = admin_ctx(
        request, 'products', 'Products Management', 'Manage product inventory.',
        products=products,
        categories=ProductCategory.objects.all(),
        totals=totals,
    )
    return render(request, 'core/admin_products.html', ctx)


@role_required('admin')
def admin_orders(request):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=request.POST.get('order_id'))
        new_status = request.POST.get('status', order.status)
        order.status = new_status
        if new_status in (Order.Status.SHIPPED, Order.Status.DELIVERED) and not order.dispatched_date:
            order.dispatched_date = datetime.date.today()
        if new_status == Order.Status.DELIVERED and not order.delivered_date:
            order.delivered_date = datetime.date.today()
        order.save()
        messages.success(request, f'{order.order_id} updated to {order.get_status_display()}.')
        return redirect('admin_orders')

    status_filter = request.GET.get('status', '')
    orders = Order.objects.select_related('distributor').prefetch_related('items').all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    ctx = admin_ctx(
        request, 'orders', 'Orders Management', 'Monitor and update all distributor orders.',
        orders=orders,
        status_filter=status_filter,
        status_choices=Order.Status.choices,
        status_counts={s: Order.objects.filter(status=s).count() for s, _ in Order.Status.choices},
    )
    return render(request, 'core/admin_orders.html', ctx)


@role_required('admin')
def admin_invoices(request):
    invoices = Invoice.objects.select_related('distributor', 'order').all()
    ctx = admin_ctx(
        request, 'invoices', 'Invoices', 'Track invoice status across all distributors.',
        invoices=invoices,
    )
    return render(request, 'core/admin_invoices.html', ctx)


@role_required('admin')
def admin_announcements(request):
    if request.method == 'POST':
        status = (Announcement.PublishStatus.DRAFT
                  if request.POST.get('submit_mode') == 'draft'
                  else Announcement.PublishStatus.PUBLISHED)
        Announcement.objects.create(
            title=request.POST.get('title', '').strip(),
            category=request.POST.get('category', Announcement.Category.GENERAL),
            content=request.POST.get('content', '').strip(),
            status=status,
            published_at=datetime.date.today(),
        )
        messages.success(request, 'Announcement saved.')
        return redirect('admin_announcements')

    items = Announcement.objects.all()
    ctx = admin_ctx(
        request, 'announcements', 'Announcements Management',
        'Create and manage announcements.',
        announcements=items,
        category_choices=Announcement.Category.choices,
    )
    return render(request, 'core/admin_announcements.html', ctx)


@role_required('admin')
def admin_staff(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        names = full_name.split(' ', 1)
        username = email.split('@')[0].lower() if email else f"staff{User.objects.count() + 1}"
        user = User.objects.create_user(
            username=username, email=email,
            password=request.POST.get('password', 'Staff@123') or 'Staff@123',
            first_name=names[0], last_name=names[1] if len(names) > 1 else '',
        )
        user.role = User.Role.STAFF
        user.save()
        StaffPermission.objects.create(user=user)
        messages.success(request, f'Staff created. Login: {username}')
        return redirect('admin_staff')

    staff_members = User.objects.filter(role=User.Role.STAFF).order_by('username')
    ctx = admin_ctx(
        request, 'staff', 'Staff Management', 'Manage staff accounts and permissions.',
        staff_members=staff_members,
    )
    return render(request, 'core/admin_staff.html', ctx)


@role_required('admin')
def admin_staff_access(request, pk):
    staff_user = get_object_or_404(User, pk=pk, role=User.Role.STAFF)
    permission, _ = StaffPermission.objects.get_or_create(user=staff_user)
    permission_fields = [
        ('can_manage_products', 'Manage Products'),
        ('can_manage_distributors', 'Manage Distributors'),
        ('can_manage_orders', 'Manage Orders'),
        ('can_manage_invoices', 'Manage Invoices'),
        ('can_manage_announcements', 'Manage Announcements'),
        ('can_view_analytics', 'View Analytics'),
        ('can_manage_settings', 'Manage Settings'),
    ]
    if request.method == 'POST':
        for field, _ in permission_fields:
            setattr(permission, field, field in request.POST)
        permission.save()
        messages.success(request, f'Permissions updated for {staff_user.username}.')
        return redirect('admin_staff_access', pk=pk)

    ctx = admin_ctx(
        request, 'staff', 'Access Control',
        f'Permissions for {staff_user.get_full_name() or staff_user.username}.',
        staff_user=staff_user,
        permission=permission,
        permission_fields=permission_fields,
    )
    return render(request, 'core/admin_staff_access.html', ctx)


@role_required('admin')
def admin_analytics(request):
    ctx = admin_ctx(
        request, 'analytics', 'Analytics & Reports', 'Revenue trends and order insights.',
    )
    return render(request, 'core/admin_analytics.html', ctx)


@role_required('admin')
def admin_settings(request):
    setting = get_company_settings()
    if request.method == 'POST':
        for field in ('company_name', 'support_email', 'support_phone', 'support_hours', 'currency'):
            value = request.POST.get(field, '').strip()
            if value:
                setattr(setting, field, value)
        setting.save()
        messages.success(request, 'Settings saved.')
        return redirect('admin_settings')
    ctx = admin_ctx(
        request, 'settings', 'System Settings', 'Manage company-wide configuration.',
        setting=setting,
    )
    return render(request, 'core/admin_settings.html', ctx)
