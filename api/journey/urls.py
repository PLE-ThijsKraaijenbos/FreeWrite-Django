from django.urls import path
from . import views

app_name = 'journey'

urlpatterns = [
    path('', views.JourneyView.as_view(), name='journey'),
    path('progress/<uuid:progress_id>/start/', views.JourneyStepProgressStartView.as_view(), name='progress-start'),
    path('progress/<uuid:progress_id>/complete/', views.JourneyStepProgressCompleteView.as_view(), name='progress-complete'),
]
