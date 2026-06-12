from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view()),
    path('complete-profile/', views.CompleteProfileView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('profile/', views.ProfileView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('avatar/items/', views.AvatarItemListView.as_view()),
    path('avatar/items/<uuid:item_id>/unlock/', views.AvatarItemUnlockView.as_view()),
    path('avatar/items/<uuid:item_id>/equip/', views.AvatarItemEquipView.as_view()),
]
