"""
ml_engine/models.py

IMPORTANT: This app does NOT define its own database tables.
The ML score, anomaly, and cluster data already lives in the warehouse
fact tables (fact_ml_scores, fact_anomalies, fact_clusters), which are
modelled in companies/models.py as FactMLScore, FactAnomaly, FactCluster.

This app exists to hold the Celery tasks that COMPUTE and WRITE to
those tables (ml_engine/tasks.py), plus any orchestration logic.
We import the models from companies.models rather than duplicating
them here, to keep a single source of truth for the schema.
"""
from companies.models import FactMLScore, FactAnomaly, FactCluster  # noqa: F401

# Re-exported so other ml_engine modules can do:
#   from ml_engine.models import FactMLScore
# without caring that the table is actually owned by the companies app.