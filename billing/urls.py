from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.pricing, name='pricing'),
    path('pricing/', views.pricing, name='pricing'),
    path('checkout/<str:plan>/', views.checkout, name='checkout'),
    path('manage/', views.manage_subscription, name='manage'),
    path('cancel/', views.cancel_subscription, name='cancel'),
]
