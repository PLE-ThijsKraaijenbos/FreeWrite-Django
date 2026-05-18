from django.urls import path, include
from . import views

urlpatterns = [
    path('health/', views.health),
    path('user/', include('user.urls')),
]
