"""Andalus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic.base import TemplateView
# from django.views.i18n import render_javascript_catalog

urlpatterns = [
    path('', include('authentication.urls')),
    path('admin/', admin.site.urls),
    path('problem/', include('problem.urls')),
    path('contest/', include('contest.urls')),
    path('competitive/', include('competitive.urls')),
    path('clarification/', include('clarification.urls')),
    path('jury/', include('jury.urls')),
    # path(r'^/admin/jsi18n/$', include('django.views.i18n')),
    # path('andalus/', TemplateView.as_view(template_name='overview.html'), name='andalus_homepage'),

]

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)