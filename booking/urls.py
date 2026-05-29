from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('repertoire/', views.repertoire, name='repertoire'),
    path('book/', views.hall, name='hall'),
    path('book/<int:seat_id>/', views.book_seat, name='book_seat'),
    path('confirm/', views.confirm_booking, name='confirm_booking'),
    path('payment/', views.payment, name='payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('seats/status/', views.get_seats_status, name='seats_status'),
    path('contacts/', views.contacts, name='contacts'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)