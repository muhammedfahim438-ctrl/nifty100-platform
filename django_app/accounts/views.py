"""
accounts/views.py
Simple session-based login/logout for staff users.
This protects the /admin-insights/ custom dashboard — only users with
is_staff=True can sign in and view it. Regular site visitors never
need an account; the public website and partner API don't require login.
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.is_staff:
                messages.error(request, 'This account does not have admin access.')
                return render(request, 'accounts/login.html')
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'accounts:dashboard_redirect')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


@login_required(login_url='accounts:login')
def dashboard_redirect(request):
    """After login, send staff users straight into the admin dashboard."""
    if request.user.is_staff:
        return redirect('admin_insights:executive_summary')
    return redirect('home')