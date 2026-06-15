"""
HTML template views for the B100 Intelligence website.
All data for charts is fetched client-side via AJAX from the REST API.
Server-side views only pass minimal context needed to render the page shell.
"""

from django.shortcuts import render, get_object_or_404
from companies.models import DimCompany, DimSector, FactMLScore


def home(request):
    """/ — Homepage with KPI cards, featured companies, sector grid."""
    sectors      = DimSector.objects.all().order_by("sector_name")
    total        = DimCompany.objects.count()
    featured     = ["TCS", "RELIANCE", "HDFCBANK", "INFY", "BAJFINANCE"]
    return render(request, "companies/home.html", {
        "sectors" : sectors,
        "total"   : total,
        "featured": featured,
    })


def company_list(request):
    """/companies/ — Filterable, sortable company table."""
    sectors = DimSector.objects.all().order_by("sector_name")
    return render(request, "companies/company_list.html", {
        "sectors": sectors,
    })


def company_detail(request, symbol):
    """/company/{symbol}/ — Full company detail with 8 Chart.js charts."""
    symbol  = symbol.upper()
    company = get_object_or_404(DimCompany.objects.select_related("sector"), symbol=symbol)
    score   = FactMLScore.objects.filter(symbol=company).order_by("-computed_at").first()

    # Banking companies need a D/E disclaimer
    banking = {"HDFCBANK", "AXISBANK", "BANKBARODA", "BAJFINANCE", "BAJAJFINSV"}
    is_banking = symbol in banking

    return render(request, "companies/company_detail.html", {
        "company"   : company,
        "score"     : score,
        "is_banking": is_banking,
        "symbol"    : symbol,
    })


def compare(request):
    """/compare/ — Side-by-side company comparison."""
    return render(request, "companies/compare.html")


def screener(request):
    """/screener/ — Multi-filter screener form."""
    sectors = DimSector.objects.all().order_by("sector_name")
    return render(request, "companies/screener.html", {
        "sectors": sectors,
    })


def sector_detail(request, name):
    """/sector/{name}/ — All companies in a sector."""
    sector = get_object_or_404(DimSector, sector_name__iexact=name)
    return render(request, "companies/sector_detail.html", {
        "sector": sector,
    })