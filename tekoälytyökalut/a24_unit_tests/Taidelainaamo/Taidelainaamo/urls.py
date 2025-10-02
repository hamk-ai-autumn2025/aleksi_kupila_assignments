"""
URL configuration for Taidelainaamo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

from django.urls import path, include
from lainaamo import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    path('lainaamo/gigasecretadmin/', admin.site.urls),
    path('lainaamo/', include("lainaamo.urls", namespace="lainaamo")),
    # path("accounts/", include("django.contrib.auth.urls")),
    # path("accounts/signup/", views.SignUpView.as_view(), name="signup"),  # Unused Django's default login and sign-up pages, custom pages in lainaamo/
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
