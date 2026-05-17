import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Distributor, LedgerEntry

User = get_user_model()

# 1. Create or get distributor user
username = 'DIST-2024-001'
email = 'distributor@example.com'
password = 'password123'

user, created = User.objects.get_or_create(username=username)
user.set_password(password)
user.email = email
user.role = 'distributor'
user.save()
print(f"Distributor User created/updated: {username} / password: {password}")

# 2. Create or get distributor profile
dist, dist_created = Distributor.objects.get_or_create(
    code=username,
    defaults={
        'user': user,
        'business_name': 'ABC Surgical Ltd.',
        'owner_name': 'Hardik Shah',
        'email': email,
        'phone': '9876543210',
        'street_address': '101, Medical Zone, Ring Road',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pincode': '400001',
        'credit_limit': Decimal('500000.00'),
    }
)

if dist_created:
    print(f"Distributor Profile created: {dist.business_name} ({dist.code})")
else:
    dist.user = user
    dist.email = email
    dist.business_name = 'ABC Surgical Ltd.'
    dist.save()
    print(f"Distributor Profile updated: {dist.business_name} ({dist.code})")


