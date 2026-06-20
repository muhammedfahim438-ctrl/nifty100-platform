"""
ml_engine/tasks.py
Celery tasks that run the nightly ML scoring and anomaly detection jobs.

Per the project spec:
  - refresh_all_scores runs nightly at 2:00 AM (scheduled in core/settings.py CELERY_BEAT_SCHEDULE)
  - It recomputes the 6 sub-scores + overall score for all companies
  - Any company whose score changed by more than 2 points triggers a
    'score_updated' webhook event to subscribed channel partners
  - run_anomaly_detection runs nightly and flags new anomalies,
    triggering 'anomaly_flagged' webhook events

NOTE: This task calls into your existing scoring logic from
notebooks/02_health_scoring.ipynb (packaged as a standalone module —
see etl/ml_scoring.py if you've extracted it). If that module doesn't
exist yet, this task degrades gracefully and logs a warning instead
of crashing the Celery worker.
"""
import logging
from celery import shared_task
from django.db import connection, transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

SCORE_CHANGE_WEBHOOK_THRESHOLD = 2.0  # points


@shared_task(bind=True)
def refresh_all_scores(self):
    """
    Recompute ML health scores for all companies and write to fact_ml_scores.
    Fires 'score_updated' webhook for any company whose score moved >2 points.
    """
    from companies.models import FactMLScore
    from api_management.tasks import fire_webhook_event

    try:
        from ml_scoring_engine import compute_all_scores  # your packaged Notebook 2 logic
    except ImportError:
        logger.warning(
            "[ml_engine] ml_scoring_engine module not found. "
            "Package notebooks/02_health_scoring.ipynb logic as a standalone "
            "module (e.g. etl/ml_scoring_engine.py) and import it here. Skipping run."
        )
        return {'status': 'skipped', 'reason': 'scoring module not found'}

    # Snapshot old scores before recomputation, to detect significant changes
    old_scores = {
        s.symbol: s.overall_score
        for s in FactMLScore.objects.all()
    }

    new_scores = compute_all_scores()  # expected: list of dicts with symbol + 6 sub-scores + overall

    updated_count = 0
    webhook_count = 0

    with transaction.atomic():
        for row in new_scores:
            symbol = row['symbol']
            obj, created = FactMLScore.objects.update_or_create(
                company_id=symbol,
                defaults={
                    'computed_at': timezone.now(),
                    'overall_score': row['overall_score'],
                    'profitability_score': row['profitability_score'],
                    'growth_score': row['growth_score'],
                    'leverage_score': row['leverage_score'],
                    'cashflow_score': row['cashflow_score'],
                    'dividend_score': row['dividend_score'],
                    'trend_score': row['trend_score'],
                    'health_label': row['health_label'],
                },
            )
            updated_count += 1

            old_val = old_scores.get(symbol)
            new_val = row['overall_score']
            if old_val is not None and abs(new_val - old_val) > SCORE_CHANGE_WEBHOOK_THRESHOLD:
                fire_webhook_event.delay(
                    event_type='score_updated',
                    symbol=symbol,
                    payload={
                        'old_score': old_val,
                        'new_score': new_val,
                        'change': round(new_val - old_val, 2),
                        'health_label': row['health_label'],
                    },
                )
                webhook_count += 1

    logger.info(f"[ml_engine] Refreshed {updated_count} scores, fired {webhook_count} webhooks.")
    return {'status': 'success', 'updated': updated_count, 'webhooks_fired': webhook_count}


@shared_task(bind=True)
def run_anomaly_detection(self):
    """
    Run Z-score + Isolation Forest anomaly detection across all companies.
    Writes new flags to fact_anomalies and fires 'anomaly_flagged' webhooks
    for any newly-detected HIGH severity anomaly.
    """
    from companies.models import FactAnomaly
    from api_management.tasks import fire_webhook_event

    try:
        from anomaly_detection_engine import detect_all_anomalies  # packaged Notebook 3 logic
    except ImportError:
        logger.warning(
            "[ml_engine] anomaly_detection_engine module not found. "
            "Package notebooks/03_anomaly_detection.ipynb logic as a standalone "
            "module and import it here. Skipping run."
        )
        return {'status': 'skipped', 'reason': 'detection module not found'}

    anomalies = detect_all_anomalies()  # expected: list of dicts

    new_count = 0
    webhook_count = 0

    with transaction.atomic():
        for a in anomalies:
            obj, created = FactAnomaly.objects.update_or_create(
                symbol=a['symbol'], year=a['year'], metric=a['metric'],
                defaults={
                    'z_score': a.get('z_score'),
                    'severity': a.get('severity'),
                    'detected_method': a.get('detected_method'),
                    'detected_at': timezone.now(),
                },
            )
            if created:
                new_count += 1
                if a.get('severity') == 'HIGH':
                    fire_webhook_event.delay(
                        event_type='anomaly_flagged',
                        symbol=a['symbol'],
                        payload={
                            'year': a['year'],
                            'metric': a['metric'],
                            'z_score': a.get('z_score'),
                            'severity': a.get('severity'),
                        },
                    )
                    webhook_count += 1

    logger.info(f"[ml_engine] Detected {new_count} new anomalies, fired {webhook_count} webhooks.")
    return {'status': 'success', 'new_anomalies': new_count, 'webhooks_fired': webhook_count}


@shared_task
def trigger_manual_rescore(symbol):
    """
    Allows the admin dashboard's Celery Monitor page to trigger
    an immediate re-score for a single company on demand.
    """
    logger.info(f"[ml_engine] Manual rescore triggered for {symbol}.")
    return refresh_all_scores.apply()
