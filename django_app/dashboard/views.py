"""
dashboard/views.py
Renders all public-facing HTML pages (Django templates + Tailwind + Chart.js).
Financial data is fetched client-side via JS calling /api/v1/ —
these views pass the necessary server-side context each template needs.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from companies.models import DimCompany, DimSector, FactMLScore

BANKING_SYMBOLS = {
    'HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK',
    'INDUSINDBK', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'PNB',
    'FEDERALBNK', 'IDFCFIRSTB',
}

FEATURED_SYMBOLS = [
    'TCS', 'INFY', 'HDFCBANK', 'RELIANCE', 'WIPRO',
    'BAJFINANCE', 'ICICIBANK', 'MARUTI', 'SUNPHARMA', 'LT',
]


def home(request):
    """Home page — search bar, featured companies, sector grid, top-10 table."""
    total = DimCompany.objects.count()
    sectors = DimSector.objects.all().order_by('sector_name')
    return render(request, 'home.html', {
        'total': total,
        'sectors': sectors,
        'featured': FEATURED_SYMBOLS,
    })


def company_list(request):
    """All companies — sortable, filterable table."""
    sectors = DimSector.objects.all().order_by('sector_name')
    return render(request, 'company_list.html', {'sectors': sectors})


def company_detail(request, symbol):
    """Single company deep-dive page with 8 Chart.js charts."""
    symbol = symbol.upper()
    try:
        company = DimCompany.objects.select_related('sector').get(symbol=symbol)
    except DimCompany.DoesNotExist:
        messages.error(request, f'Company "{symbol}" was not found in the database.')
        return redirect('company_list')

    # Try to fetch ML score for header badge / gauge seed
    score = None
    try:
        score = FactMLScore.objects.get(company_id=symbol)
    except FactMLScore.DoesNotExist:
        pass

    is_banking = symbol in BANKING_SYMBOLS

    return render(request, 'company_detail.html', {
        'symbol': symbol,
        'company': company,
        'score': score,
        'is_banking': is_banking,
    })


def company_search(request):
    """
    Handles the navbar/home search box.
    If query matches exactly one company redirect to its detail page,
    otherwise forward to the company list with the query pre-filled.
    """
    query = request.GET.get('q', '').strip() or request.GET.get('search', '').strip()
    if not query:
        return redirect('company_list')

    exact = DimCompany.objects.filter(symbol__iexact=query).first()
    if exact:
        return redirect('company_detail', symbol=exact.symbol)

    return redirect(f'/companies/?search={query}')


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
    return render(request, 'health_score.html')