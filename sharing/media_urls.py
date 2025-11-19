from django.urls import path
from sharing.media_views import MediaUploadView, MediaDeleteView, MediaListView

urlpatterns = [
    path('upload/', MediaUploadView.as_view(), name='media-upload'),
    path('delete/', MediaDeleteView.as_view(), name='media-delete'),
    path('list/', MediaListView.as_view(), name='media-list'),
]
