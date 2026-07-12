from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.feed, name='feed'),
    path('<int:job_id>/save/', views.toggle_save, name='toggle_save'),
    path('<int:job_id>/dismiss/', views.dismiss_job, name='dismiss'),
]
