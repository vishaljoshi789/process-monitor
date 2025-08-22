from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
import json
from django.db.models import Sum
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from .auth import ApiKeyAuthentication
from .models import Host, Snapshot, Process, SystemDetails
from .serializers import SnapshotInSerializer, SnapshotOutSerializer


class SmallPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200

class IsAgentWithKey(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return isinstance(request.successful_authenticator, ApiKeyAuthentication)
        return True

class ProcessSnapshotView(APIView):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAgentWithKey]

    @transaction.atomic
    def post(self, request):
        ser = SnapshotInSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        apikey = request.auth
        hostname = data["hostname"]
        if apikey and apikey.host and apikey.host.hostname != hostname:
            return Response(
                {"detail": "API key is not authorized for this host"},
                status=status.HTTP_403_FORBIDDEN,
            )

        host, _ = Host.objects.get_or_create(hostname=hostname)
        if apikey and not apikey.host:
            apikey.host = host
            apikey.save(update_fields=["host"])

        snap = Snapshot.objects.create(host=host, captured_at=data["captured_at"])
        SystemDetails.objects.create(snapshot=snap, **data["system_details"])
        to_create = [
            Process(
                snapshot=snap,
                pid=p["pid"],
                ppid=p["ppid"],
                name=p["name"],
                cpu_percent=p["cpu_percent"],
                memory_rss=p["memory_rss"],
                memory_percent=p["memory_percent"],
            )
            for p in data["processes"]
        ]
        Process.objects.bulk_create(to_create, batch_size=1000)
        processes_data = list(snap.processes.values(
            "pid", "ppid", "name", "cpu_percent", "memory_rss", "memory_percent"
        ))
        try:
            sd = snap.system_details
            system_details_data = {
                "operating_system": sd.operating_system,
                "processor": sd.processor,
                "number_of_cores": sd.number_of_cores,
                "number_of_threads": sd.number_of_threads,
                "ram_total_gb": sd.ram_total_gb,
                "ram_used_gb": sd.ram_used_gb,
                "ram_available_gb": sd.ram_available_gb,
                "storage_total_gb": sd.storage_total_gb,
                "storage_used_gb": sd.storage_used_gb,
                "storage_free_gb": sd.storage_free_gb,
            }
        except SystemDetails.DoesNotExist:
            system_details_data = None

        out = {
            "hostname": host.hostname,
            "snapshot_id": snap.id,
            "captured_at": snap.captured_at,
            "processes": processes_data,
            "system_details": system_details_data,
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"host_{host.hostname}",
            {
                "type": "snapshot.message",
                "text": json.dumps(out, default=str),
            },
        )

        return Response({"snapshot_id": snap.id}, status=status.HTTP_201_CREATED)

class HostsListView(ListAPIView):
    queryset = Host.items = Host.objects.all().order_by("hostname")
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        return Response([h.hostname for h in self.get_queryset()])

class LatestSnapshotView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        hostname = request.query_params.get("hostname")
        if not hostname:
            return Response({"detail": "hostname is required"}, status=400)

        try:
            host = Host.objects.get(hostname=hostname)
        except Host.DoesNotExist:
            return Response({"detail": "host not found"}, status=404)

        snap = host.snapshots.order_by("-captured_at", "-id").first()
        if not snap:
            return Response({"detail": "no snapshots"}, status=404)

        processes = snap.processes.values(
            "pid", "ppid", "name", "cpu_percent", "memory_rss", "memory_percent"
        )
        try:
            system_details = snap.system_details
            system_details_data = {
                "operating_system": system_details.operating_system,
                "processor": system_details.processor,
                "number_of_cores": system_details.number_of_cores,
                "number_of_threads": system_details.number_of_threads,
                "ram_total_gb": system_details.ram_total_gb,
                "ram_used_gb": system_details.ram_used_gb,
                "ram_available_gb": system_details.ram_available_gb,
                "storage_total_gb": system_details.storage_total_gb,
                "storage_used_gb": system_details.storage_used_gb,
                "storage_free_gb": system_details.storage_free_gb,
            }
        except SystemDetails.DoesNotExist:
            system_details_data = None
        
        out = {
            "hostname": host.hostname,
            "snapshot_id": snap.id,
            "captured_at": snap.captured_at,
            "processes": list(processes),
            "system_details": system_details_data
        }
        return Response(SnapshotOutSerializer(out).data)
    
class SnapshotListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = SmallPagination

    def get_queryset(self):
        hostname = self.request.query_params.get("hostname")
        if not hostname:
            return Snapshot.objects.none()
        return Snapshot.objects.filter(host__hostname=hostname).order_by("-captured_at", "-id")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        def row(s):
            return {
                "snapshot_id": s.id,
                "captured_at": s.captured_at,
                "process_count": s.processes.count(),
            }
        data = [row(s) for s in (page or qs)]
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)
    
class SnapshotDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, snapshot_id):
        try:
            snap = Snapshot.objects.select_related("host").get(id=snapshot_id)
        except Snapshot.DoesNotExist:
            return Response({"detail": "snapshot not found"}, status=404)

        processes = snap.processes.values(
            "pid", "ppid", "name", "cpu_percent", "memory_rss", "memory_percent"
        )
        try:
            sd = snap.system_details
            system_details_data = {
                "operating_system": sd.operating_system,
                "processor": sd.processor,
                "number_of_cores": sd.number_of_cores,
                "number_of_threads": sd.number_of_threads,
                "ram_total_gb": sd.ram_total_gb,
                "ram_used_gb": sd.ram_used_gb,
                "ram_available_gb": sd.ram_available_gb,
                "storage_total_gb": sd.storage_total_gb,
                "storage_used_gb": sd.storage_used_gb,
                "storage_free_gb": sd.storage_free_gb,
            }
        except SystemDetails.DoesNotExist:
            system_details_data = None

        out = {
            "hostname": snap.host.hostname,
            "snapshot_id": snap.id,
            "captured_at": snap.captured_at,
            "processes": list(processes),
            "system_details": system_details_data,
        }
        return Response(SnapshotOutSerializer(out).data)
    
class SnapshotSeriesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        hostname = request.query_params.get("hostname")
        limit = int(request.query_params.get("limit", 50))
        if not hostname:
            return Response({"detail": "hostname is required"}, status=400)

        qs = (
            Snapshot.objects.filter(host__hostname=hostname)
            .order_by("-captured_at", "-id")[:limit]
        )
        snapshots = list(qs)[::-1]
        items = []
        for s in snapshots:
            total_cpu = s.processes.aggregate(total=Sum("cpu_percent"))["total"] or 0.0
            ram_used = None
            try:
                ram_used = s.system_details.ram_used_gb
            except SystemDetails.DoesNotExist:
                pass
            items.append({
                "snapshot_id": s.id,
                "captured_at": s.captured_at,
                "total_cpu_percent": total_cpu,
                "ram_used_gb": ram_used,
            })
        return Response(items)