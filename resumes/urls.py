from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('new/', views.create_resume, name='create'),
    path('<int:pk>/', views.builder, name='builder'),
    path('<int:pk>/save/', views.save_resume, name='save'),
    path('<int:pk>/preview/', views.preview_resume, name='preview'),
    path('<int:pk>/duplicate/', views.duplicate_resume, name='duplicate'),
    path('<int:pk>/delete/', views.delete_resume, name='delete'),
    path('<int:pk>/rename/', views.rename_resume, name='rename'),
    path('<int:pk>/toggle-public/', views.toggle_public, name='toggle_public'),
    path('<int:pk>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('<int:pk>/print/', views.print_resume, name='print_resume'),
    path('<int:pk>/export/json/', views.export_json, name='export_json'),
    path('<int:pk>/ats-score/', views.ats_score, name='ats_score'),
    path('ai/generate/', views.ai_generate, name='ai_generate'),
    path('upload/', views.upload_cv, name='upload_cv'),
    path('public/<uuid:token>/', views.public_view, name='public_view'),
]
