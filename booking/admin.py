from django.contrib import admin
from .models import Table, Seat, Booking, Discount


class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'table', 'status']
    list_filter = ['status']


class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'row']
    list_filter = ['row']

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['discount_type', 'percentage', 'is_active']

admin.site.register(Table, TableAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Booking)
admin.site.register(Discount, DiscountAdmin)