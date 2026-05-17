from django.urls import path
from . import views

urlpatterns = [
    path('', views.hall, name='hall'),
    path('book/<int:seat_id>/', views.book_seat, name='book_seat'),
    path('seats/status/', views.get_seats_status, name='seats_status'),
]