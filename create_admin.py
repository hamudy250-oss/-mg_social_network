import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.contrib.auth.models import User

username = 'muhammed250'
password = 'MUHAMMEDganim250-'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, password=password, email='')
else:
    print('Existing')
