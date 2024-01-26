from foodgram.settings import DEBUG, MEDIA_URL, MEDIA_ROOT
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

if DEBUG:
    urlpatterns += static(
        MEDIA_URL, document_root=MEDIA_ROOT
    )
