from django.contrib import admin
from django.utils.html import format_html
from .models import Table, Seat, SeatStatus, Booking, Discount, SeatPrice, Session, Movie
from django import forms
from datetime import date, timedelta
import json


class SeatAdmin(admin.ModelAdmin):
    list_display = ['number', 'table']

class SeatStatusAdmin(admin.ModelAdmin):
    list_display = ['seat', 'session', 'status']
    list_filter = ['status', 'session']

class SessionInline(admin.TabularInline):
    model = Session
    extra = 1
    fields = ['date', 'session_type', 'is_active']    

class MovieSessionForm(forms.Form):
    dates = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Select dates'
    )
    session_type = forms.ChoiceField(
        choices=[('day', 'Day'), ('evening', 'Evening')],
        label='Session type'
    )

    def __init__(self, *args, taken_day=None, taken_evening=None, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        taken_day = taken_day or set()
        taken_evening = taken_evening or set()
        
        self.fields['dates'].choices = [
            (str(today + timedelta(days=i)),
            (today + timedelta(days=i)).strftime('%a, %d %b'))
            for i in range(30)
        ]


class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'poster_preview']
    inlines = [SessionInline]

    def poster_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" height="60" style="border-radius:4px;">', obj.poster.url)
        return 'No poster'
    poster_preview.short_description = 'Poster'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:movie_id>/add-sessions/', 
                 self.admin_site.admin_view(self.add_sessions_view),
                 name='movie-add-sessions'),
        ]
        return custom_urls + urls

    def add_sessions_view(self, request, movie_id):
        from django.shortcuts import get_object_or_404, redirect, render
        from django.contrib import messages
        movie = get_object_or_404(Movie, id=movie_id)

        existing_day = set(
            str(s.date) for s in Session.objects.filter(session_type='day')
        )
        existing_evening = set(
            str(s.date) for s in Session.objects.filter(session_type='evening')
        )

        if request.method == 'POST':
            form = MovieSessionForm(request.POST, taken_day=existing_day, taken_evening=existing_evening)
            if form.is_valid():
                dates = form.cleaned_data['dates']
                session_type = form.cleaned_data['session_type']
                created = 0
                skipped = []
                for d in dates:
                    if session_type in ('day', 'both'):
                        try:
                            _, c = Session.objects.get_or_create(
                                date=d, session_type='day',
                                defaults={'movie': movie, 'is_active': True}
                            )
                            if c: created += 1
                            else: skipped.append(f'{d} (day)')
                        except Exception:
                            skipped.append(f'{d} (day)')
                    if session_type in ('evening', 'both'):
                        try:
                            _, c = Session.objects.get_or_create(
                                date=d, session_type='evening',
                                defaults={'movie': movie, 'is_active': True}
                            )
                            if c: created += 1
                            else: skipped.append(f'{d} (evening)')
                        except Exception:
                            skipped.append(f'{d} (evening)')
                messages.success(request, f'Created {created} new sessions for {movie.title}')
                if skipped:
                    messages.warning(request, f'Skipped (already taken): {", ".join(skipped)}')
                return redirect(f'/admin/booking/movie/{movie_id}/change/')
        else:
            form = MovieSessionForm(taken_day=existing_day, taken_evening=existing_evening)

        return render(request, 'admin/booking/movie/add_sessions.html', {
            'form': form,
            'movie': movie,
            'existing_day': json.dumps(list(existing_day)),
            'existing_evening': json.dumps(list(existing_evening)),
            'opts': self.model._meta,
        })

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['add_sessions_url'] = f'/admin/booking/movie/{object_id}/add-sessions/'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

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