from django.shortcuts import render
from django.http import JsonResponse
from .models import Table, Seat, Booking


def hall(request):
    tables = Table.objects.prefetch_related('seats').all()
    return render(request, 'booking/hall.html', {'tables': tables})


def book_seat(request, seat_id):
    if request.method == 'POST':
        seat = Seat.objects.get(id=seat_id)

        if seat.status != 'available':
            return JsonResponse({'success': False, 'message': 'Seat is not available'})

        seat.status = 'reserved'
        seat.save()

        return JsonResponse({'success': True, 'message': 'Seat reserved'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def get_seats_status(request):
    seats = Seat.objects.select_related('table').all()
    data = [
        {
            'id': seat.id,
            'number': seat.number,
            'status': seat.status,
            'table_id': seat.table.id,
        }
        for seat in seats
    ]
    return JsonResponse({'seats': data})