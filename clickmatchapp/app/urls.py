from django.conf.urls import include, url

from .views import *

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^home/$', HomeView.as_view(), name='home'),
    url(r'^login-error/$', LoginFailedView.as_view(), name='login_error'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^match_record/(?P<index>[\w-]+)/$', MatchRecordView.as_view(), name='match_record'),
    url(r'^no_match_record/(?P<index>[\w-]+)/$', NoMatchRecordView.as_view(), name='no_match_record'),
]