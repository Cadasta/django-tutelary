from django.conf.urls import url

from .views import (
    IndexView, StatisticsView,
    UserList, UserDetail, UserCreate, UserUpdate, UserDelete, SwitchUser,
    OrganisationList, OrganisationCreate, OrganisationDelete,
    ProjectList, ProjectCreate, ProjectDelete,
    PolicyList, PolicyDetail, PolicyCreate, PolicyUpdate, PolicyDelete,
    PartyList, PartyDetail, PartyCreate, PartyUpdate, PartyDelete,
    ParcelList, ParcelDetail, ParcelCreate, ParcelUpdate, ParcelDelete)

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^statistics/$', StatisticsView.as_view(), name='statistics'),

    url(r'^user/$', UserList.as_view(), name='user-list'),
    url(r'^user/(?P<pk>\d+)/$', UserDetail.as_view(), name='user-detail'),
    url(r'^user/add/', UserCreate.as_view(), name='user-add'),
    url(r'^user/(?P<pk>\d+)/edit/$', UserUpdate.as_view(),
        name='user-update'),
    url(r'^user/(?P<pk>\d+)/delete/$', UserDelete.as_view(),
        name='user-delete'),
    url(r'^switch-user/$', SwitchUser.as_view(), name='user-switch'),

    url(r'^policy/$', PolicyList.as_view(), name='policy-list'),
    url(r'^policy/(?P<pk>\d+)/$', PolicyDetail.as_view(),
        name='policy-detail'),
    url(r'^policy/add/$', PolicyCreate.as_view(), name='policy-add'),
    url(r'^policy/(?P<pk>\d+)/edit/$', PolicyUpdate.as_view(),
        name='policy-update'),
    url(r'^policy/(?P<pk>\d+)/delete/$', PolicyDelete.as_view(),
        name='policy-delete'),

    url(r'^organisation/$', OrganisationList.as_view(),
        name='organisation-list'),
    url(r'^organisation/add/$', OrganisationCreate.as_view(),
        name='organisation-add'),
    url(r'^organisation/(?P<pk>\d+)/delete/$', OrganisationDelete.as_view(),
        name='organisation-delete'),

    url(r'^project/$', ProjectList.as_view(), name='project-list'),
    url(r'^project/add/$', ProjectCreate.as_view(), name='project-add'),
    url(r'^project/(?P<pk>\d+)/delete/$', ProjectDelete.as_view(),
        name='project-delete'),

    url(r'^party/$', PartyList.as_view(), name='party-list'),
    url(r'^party/(?P<pk>\d+)/$', PartyDetail.as_view(), name='party-detail'),
    url(r'^party/add/$', PartyCreate.as_view(), name='party-add'),
    url(r'^party/(?P<pk>\d+)/edit/$', PartyUpdate.as_view(),
        name='party-update'),
    url(r'^party/(?P<pk>\d+)/delete/$', PartyDelete.as_view(),
        name='party-delete'),

    url(r'^parcel/$', ParcelList.as_view(), name='parcel-list'),
    url(r'^parcel/(?P<pk>\d+)/$', ParcelDetail.as_view(),
        name='parcel-detail'),
    url(r'^parcel/add//$', ParcelCreate.as_view(), name='parcel-add'),
    # url(r'^parcel/add/(?P<org>[^/]+)/(?P<project>[^/]+)/$',
    #     ParcelCreate.as_view(), name='parcel-add'),
    url(r'^parcel/(?P<pk>\d+)/edit/$', ParcelUpdate.as_view(),
        name='parcel-update'),
    url(r'^parcel/(?P<pk>\d+)/delete/$', ParcelDelete.as_view(),
        name='parcel-delete'),
]
