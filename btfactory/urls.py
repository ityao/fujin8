from django.conf.urls.defaults import patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'btfactory.views.index'),
    (r'^moviethumbcron/$', 'btfactory.views.moviethumbcron'),
    (r'^dailycron/$', 'btfactory.views.dailycron'),
    (r'^actresscron/$', 'btfactory.views.actresscron'),
    (r'^(?P<daily_id>\d+)/daily/$', 'btfactory.views.dailymovie'),
    (r'^movie/(?P<movie_id>\d+)/confirm/$', 'btfactory.views.confirmMovie'),
    (r'^actress_search/$', 'btfactory.views.search_actress'),
    (r'^actress/(?P<actress_id>\d+)/$', 'btfactory.views.actressinfo'),
    (r'^actresssubscribe/(?P<actress_id>\d+)/$', 'btfactory.views.actresssubscribe'),
    (r'^daily/$', 'btfactory.views.daily'),

)

