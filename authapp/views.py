"""
authapp/views.py — Hardik International Portal
Handles all authentication flows:
  • Distributor login  → /login/
  • Admin/Staff login  → /admin-login/
  • Forgot password    → /forgot-password/
  • Logout             → /logout/
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

User = get_user_model()


def _redirect_after_login(user):
    """Return the correct named URL after a successful login based on role."""
    if user.is_admin:
        return 'admin_dashboard'
    return 'dashboard'


# ---------------------------------------------------------------------------
# Distributor Login
# ---------------------------------------------------------------------------

def login_view(request):
    """
    Entry point for Distributor users.
    Admin/Staff are blocked here and directed to the admin login portal.
    """
    if request.user.is_authenticated:
        return redirect(_redirect_after_login(request.user))

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # Support login via Distributor ID (username) or Email
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email
        else:
            username = username_or_email

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid Distributor ID / Email or password. Please try again.')
            return render(request, 'authapp/login.html')

        if not user.is_active:
            messages.error(request, 'Your account has been deactivated. Contact support.')
            return render(request, 'authapp/login.html')

        if user.is_admin or user.is_staff_member:
            messages.error(
                request,
                'Admin and Staff accounts must use the Admin Portal login.',
            )
            return render(request, 'authapp/login.html')

        login(request, user)
        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
        return redirect('dashboard')

    return render(request, 'authapp/login.html')


# ---------------------------------------------------------------------------
# Admin / Staff Login
# ---------------------------------------------------------------------------

def admin_login_view(request):
    """
    Separate login portal for Admin and Staff users.
    Distributor accounts are blocked from this endpoint.
    """
    if request.user.is_authenticated:
        return redirect(_redirect_after_login(request.user))

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid credentials. Please try again.')
            return render(request, 'authapp/admin_login.html')

        if not user.is_active:
            messages.error(request, 'Your account has been deactivated. Contact the administrator.')
            return render(request, 'authapp/admin_login.html')

        if user.is_distributor and not user.is_superuser:
            messages.error(
                request,
                'Distributor accounts cannot access the Admin Portal.',
            )
            return render(request, 'authapp/admin_login.html')

        login(request, user)
        messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
        return redirect('admin_dashboard')

    return render(request, 'authapp/admin_login.html')


# ---------------------------------------------------------------------------
# Forgot Password
# ---------------------------------------------------------------------------

def forgot_password_view(request):
    """
    Forgot password page.
    Currently shows a confirmation message; wire up to Django's
    built-in PasswordResetView (email) in Phase 5.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        # TODO (Phase 5): Trigger Django's password-reset email flow
        # For now, always show the same message to avoid user enumeration.
        messages.success(
            request,
            f'If {email} is registered, a reset link has been sent. Please check your inbox.',
        )
        return redirect('forgot_password')

    return render(request, 'authapp/forgot_password.html')


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def logout_view(request):
    """Log out any authenticated user and redirect to the distributor login."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')
