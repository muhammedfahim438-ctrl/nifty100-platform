import csv
import io
import time
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from companies.models import (
    DimCompany, DimSector, DimYear, DimHealthLabel,
    FactMLScore, FactAnomaly, FactProfitLoss, FactBalanceSheet, FactCashFlow
)
from api_management.models import ChannelPartner, APIKey, APIUsageLog, WebhookEndpoint, WebhookEvent
from ml_engine.tasks import refresh_all_scores, run_anomaly_detection, trigger_manual_rescore

# Custom decorator to restrict dashboard to staff
def staff_required(view_func):
    @login_required(login_url='accounts:login')
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("You must be a staff member to access the Admin Insights Dashboard.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@staff_required
def executive_summary(request):
    total_companies = DimCompany.objects.count()
    avg_score_val = FactMLScore.objects.aggregate(Avg('overall_score'))['overall_score__avg'] or 50.0
    good_companies = FactMLScore.objects.filter(overall_score__gte=70.0).count()
    total_sectors = DimSector.objects.count()
    
    # Sector breakdown for Chart.js
    sector_counts = DimCompany.objects.values('sector__sector_name').annotate(count=Count('symbol')).order_by('-count')
    chart_labels = []
    chart_data = []
    for sc in sector_counts:
        name = sc['sector__sector_name'] or 'Unknown'
        chart_labels.append(name)
        chart_data.append(sc['count'])

    context = {
        'total_companies': total_companies,
        'avg_score': round(avg_score_val, 1),
        'good_companies': good_companies,
        'total_sectors': total_sectors,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'active_tab': 'executive_summary',
    }
    return render(request, 'admin_insights/executive_summary.html', context)

@staff_required
def health_monitor(request):
    search_query = request.GET.get('search', '').strip()
    label_filter = request.GET.get('label', '').strip()
    
    companies_qs = DimCompany.objects.select_related('sector')
    if search_query:
        companies_qs = companies_qs.filter(Q(symbol__icontains=search_query) | Q(company_name__icontains=search_query))
        
    scores_dict = {s.company_id: s for s in FactMLScore.objects.all()}
    
    results = []
    for company in companies_qs:
        score_obj = scores_dict.get(company.symbol)
        overall_score = score_obj.overall_score if score_obj else None
        health_label = score_obj.health_label if score_obj else 'UNKNOWN'
        
        if label_filter and health_label.upper() != label_filter.upper():
            continue
            
        results.append({
            'company': company,
            'overall_score': overall_score,
            'health_label': health_label,
            'roce': company.roce_percentage,
            'roe': company.roe_percentage,
        })
        
    # Sort results by overall score (descending)
    results.sort(key=lambda x: (x['overall_score'] if x['overall_score'] is not None else -1), reverse=True)
    
    context = {
        'results': results,
        'search_query': search_query,
        'label_filter': label_filter,
        'active_tab': 'health_monitor',
    }
    return render(request, 'admin_insights/health_monitor.html', context)

@staff_required
def anomalies(request):
    anomalies_qs = FactAnomaly.objects.all().order_by('-detected_at')
    
    # Simple search or filter by severity/status
    severity_filter = request.GET.get('severity', '').strip()
    status_filter = request.GET.get('status', '').strip()
    
    if severity_filter:
        anomalies_qs = anomalies_qs.filter(severity__iexact=severity_filter)
    if status_filter:
        is_reviewed = status_filter.lower() == 'reviewed'
        anomalies_qs = anomalies_qs.filter(is_reviewed=is_reviewed)

    context = {
        'anomalies': anomalies_qs,
        'severity_filter': severity_filter,
        'status_filter': status_filter,
        'active_tab': 'anomalies',
    }
    return render(request, 'admin_insights/anomalies.html', context)

@staff_required
def review_anomaly(request, anomaly_id):
    if request.method == 'POST':
        anomaly = get_object_or_404(FactAnomaly, id=anomaly_id)
        is_reviewed = request.POST.get('is_reviewed') == 'on' or request.POST.get('is_reviewed') == 'true'
        reviewer_notes = request.POST.get('reviewer_notes', '').strip()
        
        # Raw sql execution since it's unmanaged model and we want to ensure write goes through
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE fact_anomalies SET is_reviewed = %s, reviewer_notes = %s WHERE id = %s",
                [is_reviewed, reviewer_notes, anomaly_id]
            )
        messages.success(request, f"Anomaly for {anomaly.symbol} updated successfully.")
    return redirect('admin_insights:anomalies')

@staff_required
def data_quality(request):
    # Fetch dim_year records order by sort_order
    years = DimYear.objects.filter(is_ttm=False).order_by('sort_order')
    companies = DimCompany.objects.all().order_by('symbol')
    
    # Map presence of financial records in fact_profit_loss
    # Create key: (symbol, year_id) -> bool
    pl_presence = set(FactProfitLoss.objects.values_list('symbol', 'year_id'))
    bs_presence = set(FactBalanceSheet.objects.values_list('symbol', 'year_id'))
    cf_presence = set(FactCashFlow.objects.values_list('symbol', 'year_id'))
    
    matrix = []
    for c in companies:
        row = {'company': c, 'years': []}
        for y in years:
            has_pl = (c.symbol, y.year_id) in pl_presence
            has_bs = (c.symbol, y.year_id) in bs_presence
            has_cf = (c.symbol, y.year_id) in cf_presence
            
            # Status: 0=Missing, 1=Partial, 2=Complete
            complete_count = sum([has_pl, has_bs, has_cf])
            if complete_count == 3:
                status = 'complete'
            elif complete_count > 0:
                status = 'partial'
            else:
                status = 'missing'
                
            row['years'].append({
                'year': y,
                'status': status,
                'details': f"P&L: {'✓' if has_pl else '✗'}, BS: {'✓' if has_bs else '✗'}, CF: {'✓' if has_cf else '✗'}"
            })
        matrix.append(row)
        
    context = {
        'years': years,
        'matrix': matrix,
        'active_tab': 'data_quality',
    }
    return render(request, 'admin_insights/data_quality.html', context)

@staff_required
def api_management(request):
    partners = ChannelPartner.objects.prefetch_related('api_keys').all()
    context = {
        'partners': partners,
        'active_tab': 'api_management',
    }
    return render(request, 'admin_insights/api_management.html', context)

@staff_required
def create_partner(request):
    if request.method == 'POST':
        name = request.POST.get('company_name', '').strip()
        email = request.POST.get('contact_email', '').strip()
        tier = request.POST.get('tier', 'BASIC').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not name or not email:
            messages.error(request, "Company name and contact email are required.")
            return redirect('admin_insights:api_management')
            
        try:
            ChannelPartner.objects.create(
                company_name=name,
                contact_email=email,
                tier=tier,
                notes=notes
            )
            messages.success(request, f"Channel Partner '{name}' created successfully.")
        except Exception as e:
            messages.error(request, f"Error creating partner: {e}")
            
    return redirect('admin_insights:api_management')

@staff_required
def update_partner_tier(request, partner_id):
    if request.method == 'POST':
        partner = get_object_or_404(ChannelPartner, id=partner_id)
        tier = request.POST.get('tier', 'BASIC').strip()
        partner.tier = tier
        partner.save(update_fields=['tier'])
        messages.success(request, f"Updated tier for {partner.company_name} to {tier}.")
    return redirect('admin_insights:api_management')

@staff_required
def deactivate_partner(request, partner_id):
    if request.method == 'POST':
        partner = get_object_or_404(ChannelPartner, id=partner_id)
        action = request.POST.get('action', 'deactivate')
        partner.is_active = (action == 'activate')
        partner.save(update_fields=['is_active'])
        
        # If deactivating, also deactivate all their API keys
        if not partner.is_active:
            partner.api_keys.filter(is_active=True).update(is_active=False)
            
        status_str = "activated" if partner.is_active else "deactivated"
        messages.success(request, f"Partner {partner.company_name} has been {status_str}.")
    return redirect('admin_insights:api_management')

@staff_required
def generate_api_key(request, partner_id):
    if request.method == 'POST':
        partner = get_object_or_404(ChannelPartner, id=partner_id)
        label = request.POST.get('label', 'Default Key').strip()
        
        try:
            new_key, raw_secret = APIKey.create_key_pair(partner, label=label)
            
            # Store in session so we can display it ONCE to the user
            request.session['new_key_id'] = str(new_key.key_id)
            request.session['new_key_secret'] = raw_secret
            request.session['new_key_partner'] = partner.company_name
            
            messages.success(request, f"API Key for {partner.company_name} generated successfully.")
        except Exception as e:
            messages.error(request, f"Error generating API key: {e}")
            
    return redirect('admin_insights:api_management')

@staff_required
def deactivate_api_key(request, key_id):
    if request.method == 'POST':
        key = get_object_or_404(APIKey, key_id=key_id)
        key.is_active = False
        key.save(update_fields=['is_active'])
        messages.success(request, f"API Key '{key.label}' deactivated.")
    return redirect('admin_insights:api_management')

@staff_required
def api_usage(request):
    logs_qs = APIUsageLog.objects.select_related('api_key', 'api_key__partner').all()
    
    # 30-day API call volume
    now_dt = timezone.now()
    start_dt = now_dt - timedelta(days=30)
    
    # Call count per day
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DATE(requested_at) as date_val, COUNT(*) as call_count
            FROM api_usage_logs
            WHERE requested_at >= %s
            GROUP BY DATE(requested_at)
            ORDER BY DATE(requested_at)
        """, [start_dt])
        daily_calls_raw = cursor.fetchall()
        
    daily_labels = []
    daily_data = []
    # Fill in potential gaps in days
    day_map = {r[0]: r[1] for r in daily_calls_raw}
    for i in range(31):
        d = (start_dt + timedelta(days=i)).date()
        if d <= now_dt.date():
            daily_labels.append(d.strftime('%b %d'))
            daily_data.append(day_map.get(d, 0))
            
    # Endpoint performance / breakdown
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT endpoint, method, COUNT(*) as calls, ROUND(AVG(response_time_ms), 1) as avg_latency
            FROM api_usage_logs
            GROUP BY endpoint, method
            ORDER BY calls DESC
        """)
        endpoint_stats = [
            {'endpoint': r[0], 'method': r[1], 'calls': r[2], 'latency': r[3]}
            for r in cursor.fetchall()
        ]
        
    # Latency Percentiles (P50, P95)
    latencies = list(APIUsageLog.objects.values_list('response_time_ms', flat=True).order_by('response_time_ms'))
    total_logs = len(latencies)
    if total_logs > 0:
        p50 = latencies[int(total_logs * 0.50)]
        p95 = latencies[int(total_logs * 0.95)]
        avg_lat = round(sum(latencies) / total_logs, 1)
    else:
        p50 = p95 = avg_lat = 0
        
    context = {
        'daily_labels': daily_labels,
        'daily_data': daily_data,
        'endpoint_stats': endpoint_stats,
        'p50': p50,
        'p95': p95,
        'avg_latency': avg_lat,
        'total_requests': total_logs,
        'active_tab': 'api_usage',
    }
    return render(request, 'admin_insights/api_usage.html', context)

@staff_required
def webhooks(request):
    endpoints = WebhookEndpoint.objects.select_related('partner').all()
    events = WebhookEvent.objects.select_related('endpoint', 'endpoint__partner').all().order_by('-created_at')[:100]
    
    context = {
        'endpoints': endpoints,
        'events': events,
        'active_tab': 'webhooks',
    }
    return render(request, 'admin_insights/webhooks.html', context)

@staff_required
def bulk_import(request):
    if request.method == 'POST':
        import_type = request.POST.get('import_type')
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, "Please upload a CSV file.")
            return redirect('admin_insights:bulk_import')
            
        try:
            # Decode file contents
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Map year labels to year ids to prevent extra db lookups
            year_map = {y.year_label: y.year_id for y in DimYear.objects.all()}
            company_symbols = set(DimCompany.objects.values_list('symbol', flat=True))
            
            records_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                for row in reader:
                    symbol = row.get('company_id') or row.get('symbol')
                    year_label = row.get('year_label')
                    
                    if not symbol or not year_label:
                        skipped_count += 1
                        continue
                        
                    symbol = symbol.strip().upper()
                    year_label = year_label.strip()
                    
                    if symbol not in company_symbols or year_label not in year_map:
                        skipped_count += 1
                        continue
                        
                    year_id = year_map[year_label]
                    
                    # Run target inserts based on type
                    if import_type == 'profit_loss':
                        # Clean fields safely
                        def get_float(field):
                            val = row.get(field)
                            return float(val) if val and str(val).strip() else None

                        FactProfitLoss.objects.update_or_create(
                            symbol=symbol, year_id=year_id,
                            defaults={
                                'sales': get_float('sales'),
                                'expenses': get_float('expenses'),
                                'operating_profit': get_float('operating_profit'),
                                'opm_pct': get_float('opm_percentage') or get_float('opm_pct'),
                                'other_income': get_float('other_income'),
                                'interest': get_float('interest'),
                                'depreciation': get_float('depreciation'),
                                'profit_before_tax': get_float('profit_before_tax'),
                                'tax_pct': get_float('tax_percentage') or get_float('tax_pct'),
                                'net_profit': get_float('net_profit'),
                                'eps': get_float('eps'),
                                'dividend_payout': get_float('dividend_payout'),
                                'net_profit_margin_pct': get_float('net_profit_margin_pct'),
                                'expense_ratio_pct': get_float('expense_ratio_pct'),
                                'interest_coverage': get_float('interest_coverage'),
                            }
                        )
                    elif import_type == 'balance_sheet':
                        def get_float(field):
                            val = row.get(field)
                            return float(val) if val and str(val).strip() else None

                        FactBalanceSheet.objects.update_or_create(
                            symbol=symbol, year_id=year_id,
                            defaults={
                                'equity_capital': get_float('equity_capital'),
                                'reserves': get_float('reserves'),
                                'borrowings': get_float('borrowings'),
                                'other_liabilities': get_float('other_liabilities'),
                                'total_liabilities': get_float('total_liabilities'),
                                'fixed_assets': get_float('fixed_assets'),
                                'cwip': get_float('cwip'),
                                'investments': get_float('investments'),
                                'other_assets': get_float('other_asset') or get_float('other_assets'),
                                'total_assets': get_float('total_assets'),
                                'debt_to_equity': get_float('debt_to_equity'),
                                'equity_ratio': get_float('equity_ratio'),
                            }
                        )
                    elif import_type == 'cash_flow':
                        def get_float(field):
                            val = row.get(field)
                            return float(val) if val and str(val).strip() else None

                        FactCashFlow.objects.update_or_create(
                            symbol=symbol, year_id=year_id,
                            defaults={
                                'operating_activity': get_float('operating_activity'),
                                'investing_activity': get_float('investing_activity'),
                                'financing_activity': get_float('financing_activity'),
                                'net_cash_flow': get_float('net_cash_flow'),
                                'free_cash_flow': get_float('free_cash_flow'),
                            }
                        )
                    records_count += 1
                    
            messages.success(request, f"Successfully imported {records_count} records ({skipped_count} skipped).")
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            
        return redirect('admin_insights:bulk_import')
        
    context = {
        'active_tab': 'bulk_import',
    }
    return render(request, 'admin_insights/bulk_import.html', context)

@staff_required
def celery_monitor(request):
    # Retrieve details from Redis or show the beat schedules defined in settings.py
    # Since we can't always query celery directly from django easily without django-celery-results/beat,
    # we can display standard configured tasks and offer execution controls.
    
    # We can fetch recent tasks execution if they were logged in Redis, or just display static lists of beat schedules.
    scheduled_tasks = [
        {'name': 'refresh-all-scores-nightly', 'task': 'ml_engine.tasks.refresh_all_scores', 'schedule': 'Daily at 2:00 AM'},
        {'name': 'run-anomaly-detection-nightly', 'task': 'ml_engine.tasks.run_anomaly_detection', 'schedule': 'Daily at 3:00 AM'},
    ]
    
    context = {
        'scheduled_tasks': scheduled_tasks,
        'active_tab': 'celery_monitor',
    }
    return render(request, 'admin_insights/celery_monitor.html', context)

@staff_required
def trigger_celery_task(request):
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        
        if task_name == 'refresh_all_scores':
            refresh_all_scores.delay()
            messages.success(request, "Triggered Celery task 'refresh_all_scores'.")
        elif task_name == 'run_anomaly_detection':
            run_anomaly_detection.delay()
            messages.success(request, "Triggered Celery task 'run_anomaly_detection'.")
        else:
            messages.error(request, f"Unknown task: {task_name}")
            
    return redirect('admin_insights:celery_monitor')
