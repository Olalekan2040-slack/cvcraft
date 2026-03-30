from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('pricing/', views.pricing, name='pricing'),
    path('about/', views.about, name='about'),
]
