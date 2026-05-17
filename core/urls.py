"""
core/urls.py — Hardik International Portal
URL patterns for both the Distributor and Admin portals.
"""

from django.urls import path

from . import views

urlpatterns = [
    # Home — smart redirect based on role
    path('', views.portal_home, name='portal_home'),

    # -------------------------------------------------------------------------
    # Distributor Portal
    # -------------------------------------------------------------------------
    path('dashboard/', views.dashboard, name='dashboard'),
    path('place-order/', views.place_order, name='place_order'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmed/', views.order_confirmed, name='order_confirmed'),
    path('order-history/', views.order_history, name='order_history'),
    path('bills-invoices/', views.bills_invoices, name='bills_invoices'),
    path('ledger-payments/', views.ledger_payments, name='ledger_payments'),
    path('catalogue/', views.product_catalogue, name='product_catalogue'),
    path('announcements/', views.announcements, name='announcements'),
    path('profile-support/', views.profile_support, name='profile_support'),

    # -------------------------------------------------------------------------
    # Admin Portal
    # -------------------------------------------------------------------------
    path('admin-portal/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/distributors/', views.admin_distributors, name='admin_distributors'),
    path('admin-portal/products/', views.admin_products, name='admin_products'),
    path('admin-portal/orders/', views.admin_orders, name='admin_orders'),
    path('admin-portal/invoices/', views.admin_invoices, name='admin_invoices'),
    path('admin-portal/invoices/<int:pk>/', views.admin_invoice_detail, name='admin_invoice_detail'),
    path('admin-portal/invoices/<int:pk>/download/', views.admin_invoice_download, name='admin_invoice_download'),
    path('admin-portal/announcements/', views.admin_announcements, name='admin_announcements'),
    path('admin-portal/staff/', views.admin_staff, name='admin_staff'),
    path('admin-portal/staff/<int:pk>/access/', views.admin_staff_access, name='admin_staff_access'),
    path('admin-portal/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin-portal/settings/', views.admin_settings, name='admin_settings'),
]
