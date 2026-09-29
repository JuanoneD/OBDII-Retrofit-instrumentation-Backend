from django.contrib import admin

from .models import Refuel


@admin.register(Refuel)
class RefuelAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "created_at", "liters_inserted", "liters_spent_system", "old_factor", "new_factor"]
    list_filter = ["vehicle"]
