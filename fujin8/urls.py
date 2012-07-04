from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.conf.urls.static import static
from django.contrib import admin
import settings

admin.autodiscover()

urlpatterns = patterns('',

    url(r'^$', 'fujin8.views.home', name='home'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^lovecast/', include('btfactory.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


