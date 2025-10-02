from django.urls import path
from . import views
from .myforms import CustomLoginForm, CustomSignupForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import admin



app_name="lainaamo"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),  # Front page
    path("work<int:pk>", views.DetailView.as_view(), name="detail"),  # Work detail page
    path("signup/", views.CustomSignUpView.as_view(form_class=CustomSignupForm), name="signup"),
    path("my_loans", views.MyLoansView.as_view(), name="my_loans"),  # Works borrowed by the user page
    path("login/", LoginView.as_view(authentication_form=CustomLoginForm), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
]