from django.urls import path
from .views import (
    ProcessSnapshotView, HostsListView, LatestSnapshotView,
    SnapshotListView, SnapshotDetailView, SnapshotSeriesView
)

urlpatterns = [
    path("process-snapshots/", ProcessSnapshotView.as_view(), name="process-snapshots"),
    path("hosts/", HostsListView.as_view(), name="hosts"),
    path("process-snapshots/latest/", LatestSnapshotView.as_view(), name="latest-snapshot"),
    path("process-snapshots/list/", SnapshotListView.as_view(), name="snapshot-list"),
    path("process-snapshots/<int:snapshot_id>/", SnapshotDetailView.as_view(), name="snapshot-detail"),
    path("process-snapshots/series/", SnapshotSeriesView.as_view(), name="snapshot-series"),
]