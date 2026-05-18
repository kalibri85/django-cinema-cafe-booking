from django.shortcuts import render
from django.http import JsonResponse
from .models import Table, Seat, Booking
from .booking_logic import check_isolated_seats, get_discount
from django.utils import timezone
from datetime import timedelta



def hall(request):
    row1 = Table.objects.prefetch_related('seats').filter(row=1).order_by('number')
    row2 = Table.objects.prefetch_related('seats').filter(row=2).order_by('number')
    
    isolated_seat_ids = []
    isolated_discounts = {}
    
    for table in list(row1) + list(row2):
        for item in check_isolated_seats(table):
            isolated_seat_ids.append(item['seat_id'])
            isolated_discounts[item['seat_id']] = item['discount']
    
    return render(request, 'booking/hall.html', {
        'row1': row1,
        'row2': row2,
        'isolated_discounts': isolated_discounts,
        'odd_discount': get_discount('odd'),
    })


def book_seat(request, seat_id):
    if request.method == 'POST':
        seat = Seat.objects.get(id=seat_id)

        if seat.status == 'reserved':
            if seat.reserved_until and seat.reserved_until < timezone.now():
                seat.status = 'available'
                seat.reserved_until = None
                seat.save()
            else:
                return JsonResponse({'success': False, 'message': 'Seat is temporarily reserved'})

        if seat.status != 'available':
            return JsonResponse({'success': False, 'message': 'Seat is not available'})

        seat.status = 'reserved'
        seat.reserved_until = timezone.now() + timedelta(minutes=10)
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