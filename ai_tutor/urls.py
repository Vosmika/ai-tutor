from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('accounts/', include('allauth.urls')),

    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('subjects/', include('subjects.urls', namespace='subjects')),
    path('assessments/', include('assessments.urls', namespace='assessments')),
    path('learning/', include('learning.urls', namespace='learning')),
    path('chatbot/', include('chatbot.urls', namespace='chatbot')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),

    path('', lambda request: redirect('dashboard/')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)