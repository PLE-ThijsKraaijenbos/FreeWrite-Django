from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from . import views

urlpatterns = [
    path('health/', views.health),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('user/', include('user.urls')),
    path('journey/', include('journey.urls')),
    path('community/', include('community.urls')),
]
