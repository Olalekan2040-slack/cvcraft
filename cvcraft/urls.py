from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from resumes.views import public_view, public_pdf_download, public_print_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('resumes.urls')),
    path('billing/', include('billing.urls')),
    # Short public resume links
    path('r/<uuid:token>/', public_view, name='resume_public_short'),
    path('r/<uuid:token>/pdf/', public_pdf_download, name='resume_public_pdf'),
    path('r/<uuid:token>/print/', public_print_view, name='resume_public_print'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
