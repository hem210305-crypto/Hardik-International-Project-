import os
import django
import sys

# Setup django
sys.path.append(r"c:\Users\hemka\OneDrive\Desktop\Internation Project")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.test import Client

client = Client()

# Since role_required('admin') is on admin_announcements, I need to login as admin first
from django.contrib.auth import get_user_model
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
client.force_login(admin_user)

response = client.post('/admin-portal/announcements/', {
    'title': 'Test Announcement',
    'category': 'general',
    'content': 'This is a test.',
    'submit_mode': 'publish'
})

print(response.status_code)
print(response.url if hasattr(response, 'url') else 'No redirect')
