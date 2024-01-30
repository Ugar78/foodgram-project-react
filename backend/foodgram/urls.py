from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

handler404 = 'api.views.page_not_found'

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    re_path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
