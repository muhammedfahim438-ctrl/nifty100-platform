import hashlib
import hmac
import time
import uuid
import pytest
from django.urls import reverse
from django.utils import timezone
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from api_management.models import ChannelPartner, APIKey, APIUsageLog

# Helper to construct HMAC signature headers
def get_hmac_headers(key_id, secret, method, path, body=b''):
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    body_hash = hashlib.sha256(body).hexdigest()
    message = f"{method}\n{path}\n{timestamp}\n{body_hash}"
    
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        'HTTP_X_API_KEY_ID': str(key_id),
        'HTTP_X_TIMESTAMP': timestamp,
        'HTTP_X_NONCE': nonce,
        'HTTP_X_SIGNATURE': signature,
    }

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def partner(db):
    return ChannelPartner.objects.create(
        company_name="Test Partner Corp",
        contact_email="dev@testpartner.com",
        tier="BASIC",
        is_active=True
    )

@pytest.fixture
def api_key(partner):
    key, raw_secret = APIKey.create_key_pair(partner, label="Test Key")
    return key, raw_secret

@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_STORE_EAGER_RESULTS=True)
def test_hmac_authentication_success(api_client, partner, api_key):
    key, raw_secret = api_key
    
    url = reverse('partner-keys-list')
    # Sign with key.key_secret_hash to match the server side-channel key verification behavior
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    
    response = api_client.get(url, **headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['key_id'] == str(key.key_id)

@pytest.mark.django_db
def test_hmac_authentication_missing_headers(api_client):
    url = reverse('partner-keys-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data['error'] == 'authentication_failed'

@pytest.mark.django_db
def test_hmac_authentication_stale_timestamp(api_client, partner, api_key):
    key, raw_secret = api_key
    url = reverse('partner-keys-list')
    
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    # Tamper with timestamp to make it old
    headers['HTTP_X_TIMESTAMP'] = str(int(time.time()) - 400)
    
    response = api_client.get(url, **headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "too old" in response.data['message']

@pytest.mark.django_db
def test_hmac_authentication_tampered_signature(api_client, partner, api_key):
    key, raw_secret = api_key
    url = reverse('partner-keys-list')
    
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    # Tamper with signature
    headers['HTTP_X_SIGNATURE'] = "invalid_signature_hash_123"
    
    response = api_client.get(url, **headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "failed" in response.data['message']

@pytest.mark.django_db
def test_hmac_authentication_replay_attack(api_client, partner, api_key):
    key, raw_secret = api_key
    url = reverse('partner-keys-list')
    
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    
    # First request succeeds
    response1 = api_client.get(url, **headers)
    assert response1.status_code == status.HTTP_200_OK
    
    # Second request with same headers/nonce fails
    response2 = api_client.get(url, **headers)
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
    assert "replay attack" in response2.data['message']

@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_STORE_EAGER_RESULTS=True)
def test_api_usage_logging_creation(api_client, partner, api_key):
    key, raw_secret = api_key
    url = reverse('partner-keys-list')
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    
    # Assert logs are currently empty
    assert APIUsageLog.objects.count() == 0
    
    response = api_client.get(url, **headers)
    assert response.status_code == status.HTTP_200_OK
    
    # Assert usage log is populated
    assert APIUsageLog.objects.count() == 1
    log = APIUsageLog.objects.first()
    assert log.api_key == key
    assert log.endpoint == url
    assert log.method == 'GET'
    assert log.status_code == 200

@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_rate_limiting_tier_basic(api_client, partner, api_key):
    key, raw_secret = api_key
    url = reverse('partner-keys-list')
    
    # BASIC limit is 10/min. Make 11 requests.
    for i in range(10):
        # We need a different nonce for each request to avoid replay block
        headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
        response = api_client.get(url, **headers)
        assert response.status_code == status.HTTP_200_OK
        
    # The 11th request should be throttled
    headers = get_hmac_headers(key.key_id, key.key_secret_hash, 'GET', url)
    response = api_client.get(url, **headers)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "retry_after" in response.headers or "Retry-After" in response.headers
