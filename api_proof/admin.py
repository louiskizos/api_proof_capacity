# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import *
# User = get_user_model()



admin.site.register(CardanoWallet)
admin.site.register(CardanoNFT)
admin.site.register(VideoCourse)
admin.site.register(VideoCourseCertificate)
admin.site.register(VideoModule)
admin.site.register(VideoView)