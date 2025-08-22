from rest_framework import serializers

class ProcessInSerializer(serializers.Serializer):
    pid = serializers.IntegerField()
    ppid = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    cpu_percent = serializers.FloatField()
    memory_rss = serializers.IntegerField()
    memory_percent = serializers.FloatField()

class SystemDetailsInSerializer(serializers.Serializer):
    operating_system = serializers.CharField(max_length=255)
    processor = serializers.CharField(max_length=255)
    number_of_cores = serializers.IntegerField()
    number_of_threads = serializers.IntegerField()
    ram_total_gb = serializers.FloatField()
    ram_used_gb = serializers.FloatField()
    ram_available_gb = serializers.FloatField()
    storage_total_gb = serializers.FloatField()
    storage_used_gb = serializers.FloatField()
    storage_free_gb = serializers.FloatField()

class SnapshotInSerializer(serializers.Serializer):
    hostname = serializers.CharField(max_length=255)
    captured_at = serializers.DateTimeField()
    processes = ProcessInSerializer(many=True)
    system_details = SystemDetailsInSerializer()

class ProcessOutSerializer(serializers.Serializer):
    pid = serializers.IntegerField()
    ppid = serializers.IntegerField()
    name = serializers.CharField()
    cpu_percent = serializers.FloatField()
    memory_rss = serializers.IntegerField()
    memory_percent = serializers.FloatField()

class SystemDetailsOutSerializer(serializers.Serializer):
    operating_system = serializers.CharField()
    processor = serializers.CharField()
    number_of_cores = serializers.IntegerField()
    number_of_threads = serializers.IntegerField()
    ram_total_gb = serializers.FloatField()
    ram_used_gb = serializers.FloatField()
    ram_available_gb = serializers.FloatField()
    storage_total_gb = serializers.FloatField()
    storage_used_gb = serializers.FloatField()
    storage_free_gb = serializers.FloatField()

class SnapshotOutSerializer(serializers.Serializer):
    hostname = serializers.CharField()
    snapshot_id = serializers.IntegerField()
    captured_at = serializers.DateTimeField()
    processes = ProcessOutSerializer(many=True)
    system_details = SystemDetailsOutSerializer()