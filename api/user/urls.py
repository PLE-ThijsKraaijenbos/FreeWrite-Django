from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view()),
    path('profile/', views.UserProfileView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]
