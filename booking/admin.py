from django.contrib import admin
from .models import Table, Seat, SeatStatus, Booking, Discount, SeatPrice, Session, Movie


class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'table']

class SeatStatusAdmin(admin.ModelAdmin):
    list_display = ['seat', 'session', 'status']
    list_filter = ['status', 'session']

class MovieAdmin(admin.ModelAdmin):
    list_display = ['title']    

class SessionAdmin(admin.ModelAdmin):
    list_display = ['date', 'session_type', 'is_active']
    list_filter = ['session_type', 'is_active']

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
admin.site.register(SeatStatus, SeatStatusAdmin)
admin.site.register(SeatPrice, SeatPriceAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(Session, SessionAdmin)
admin.site.register(Booking)
admin.site.register(Discount, DiscountAdmin)