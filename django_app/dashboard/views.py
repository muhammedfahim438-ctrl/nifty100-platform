"""
dashboard/views.py
Renders all public-facing HTML pages (Django templates + Tailwind + Chart.js).
All actual data fetching happens client-side via JS calling /api/v1/ —
these views just render the template shell and pass minimal context
(e.g. the symbol or sector name from the URL).
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from companies.models import DimCompany, DimSector


def home(request):
    """Home page — search bar, featured companies, sector grid, insights ticker."""
    return render(request, 'home.html')


def company_list(request):
    """All companies — sortable, filterable table."""
    return render(request, 'company_list.html')


def company_detail(request, symbol):
    """Single company deep-dive page with 8 Chart.js charts."""
    symbol = symbol.upper()
    # Light validation — confirm the company exists before rendering charts
    exists = DimCompany.objects.filter(symbol=symbol).exists()
    if not exists:
        messages.error(request, f'Company "{symbol}" was not found in the database.')
        return redirect('company_list')
    return render(request, 'company_detail.html', {'symbol': symbol})


def company_search(request):
    """
    Handles the navbar/home search box.
    If query matches exactly one company, redirect straight to its detail page.
    Otherwise send to the company list — its own JS search box picks up ?q=.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('company_list')

    # Try exact symbol match first
    exact = DimCompany.objects.filter(symbol__iexact=query).first()
    if exact:
        return redirect('company_detail', symbol=exact.symbol)

    return redirect(f"/companies/?q={query}")


def screener(request):
    """Multi-filter screener page."""
    return render(request, 'screener.html')


def compare(request):
    """Side-by-side company comparison page."""
    return render(request, 'compare.html')


def sector_list(request):
    """Lists all sectors — links into sector_detail."""
    sectors = DimSector.objects.all().order_by('sector_name')
    return render(request, 'sector_list.html', {'sectors': sectors})


def sector_detail(request, name):
    """Single sector page — companies, rankings, trends."""
    return render(request, 'sector_detail.html', {'sector_name': name})


def health_scores(request):
    """ML health score leaderboard page."""
    return render(request, 'health_scores.html')