from django.db import models

class Host(models.Model):
    hostname = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hostname
    
class ApiKey(models.Model):
    key = models.CharField(max_length=64, unique=True)
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="api_keys", null=True, blank=True)
    active = models.BooleanField(default=True)
    note = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.key[:6]}... ({'active' if self.active else 'inactive'})"

class Snapshot(models.Model):
    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="snapshots")
    captured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["host", "-captured_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.host.hostname} @ {self.captured_at.isoformat()}"

class Process(models.Model):
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE, related_name="processes")
    pid = models.IntegerField()
    ppid = models.IntegerField()
    name = models.CharField(max_length=255)
    cpu_percent = models.FloatField()
    memory_rss = models.BigIntegerField()
    memory_percent = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=["snapshot", "pid"]),
            models.Index(fields=["snapshot", "ppid"]),
        ]

class SystemDetails(models.Model):
    snapshot = models.OneToOneField(Snapshot, on_delete=models.CASCADE, related_name="system_details")
    operating_system = models.CharField(max_length=255)
    processor = models.CharField(max_length=255)
    number_of_cores = models.IntegerField()
    number_of_threads = models.IntegerField()
    ram_total_gb = models.FloatField()
    ram_used_gb = models.FloatField()
    ram_available_gb = models.FloatField()
    storage_total_gb = models.FloatField()
    storage_used_gb = models.FloatField()
    storage_free_gb = models.FloatField()

    def __str__(self):
        return f"System details for {self.snapshot.host.hostname}"