from django.contrib import admin

from .models import Reading, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["name", "device_id", "plate", "gasoline_level", "fuel_consumption_factor", "last_seen_at", "is_active"]
    search_fields = ["name", "device_id", "plate", "owner_name"]
    list_filter = ["is_active"]


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "sent_at", "rpm", "speed", "coolant_temp", "engine_load", "ltft", "fuel_percent"]
    list_filter = ["vehicle"]
    date_hierarchy = "sent_at"
