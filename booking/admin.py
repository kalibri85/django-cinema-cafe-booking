from django.contrib import admin
from .models import Table, Seat, Booking


class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'table', 'status']
    list_filter = ['status']


class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'row']
    list_filter = ['row']


admin.site.register(Table, TableAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Booking)