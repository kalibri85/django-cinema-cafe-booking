from django.contrib import admin
from .models import Table, Seat, Booking, Discount, SeatPrice


class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'table', 'status']
    list_filter = ['status']


class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'row']
    list_filter = ['row']

class SeatPriceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SeatPrice.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['discount_type', 'percentage', 'is_active']

admin.site.register(Table, TableAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(SeatPrice, SeatPriceAdmin)
admin.site.register(Booking)
admin.site.register(Discount, DiscountAdmin)