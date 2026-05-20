from django.shortcuts import render
from django.http import JsonResponse
from .models import Table, Seat, Booking
from .booking_logic import check_isolated_seats, get_discount
from django.utils import timezone
from datetime import timedelta
from .forms import BookingForm
from django.shortcuts import render, redirect



def hall(request):
    row1 = Table.objects.prefetch_related('seats').filter(row=1).order_by('number')
    row2 = Table.objects.prefetch_related('seats').filter(row=2).order_by('number')
    
    isolated_discounts = {}
    
    for table in list(row1) + list(row2):
        for item in check_isolated_seats(table):
            isolated_discounts[item['seat_id']] = item['discount']

    pending = request.session.get('pending_booking', {})
    pending_seat_ids = [int(sid) for sid in pending.get('seat_ids', [])]        
    
    odd_seat_discounts = {}
    if pending_seat_ids:
        odd_discount = get_discount('odd')
        pending_seats = Seat.objects.filter(id__in=pending_seat_ids).select_related('table')
        pending_table_ids = set(seat.table.id for seat in pending_seats)

        for table in list(row1) + list(row2):
            if table.id in pending_table_ids:
                for seat in table.seats.all():
                    if seat.status == 'available' and seat.id not in pending_seat_ids:
                        odd_seat_discounts[seat.id] = odd_discount

    return render(request, 'booking/hall.html', {
        'row1': row1,
        'row2': row2,
        'isolated_discounts': isolated_discounts,
        'odd_seat_discounts': odd_seat_discounts,
        'odd_discount': get_discount('odd'),
        'pending_seat_ids': pending_seat_ids,
        'pending_name': pending.get('customer_name', ''),
        'pending_email': pending.get('customer_email', ''),
    })

def confirm_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        new_seat_ids = request.POST.get('seat_ids', '').split(',')
        new_seat_ids = [s for s in new_seat_ids if s]

        if form.is_valid():
            existing = request.session.get('pending_booking', {})
            existing_ids = existing.get('seat_ids', [])
            all_seat_ids = list(set(existing_ids + new_seat_ids))

            request.session['pending_booking'] = {
                'seat_ids': all_seat_ids,
                'customer_name': form.cleaned_data['customer_name'],
                'customer_email': form.cleaned_data['customer_email'],
            }
            return JsonResponse({'success': True, 'redirect': '/payment/'})

        return JsonResponse({'success': False, 'errors': form.errors})

    return JsonResponse({'success': False, 'message': 'Invalid request'})

def payment(request):
    booking = request.session.get('pending_booking')
    if not booking:
        return redirect('hall')

    seat_ids = booking['seat_ids']
    seats = Seat.objects.filter(id__in=seat_ids)
    total = len(seat_ids) * 15

    isolated_ids = []
    for seat in seats:
        other_seats = seat.table.seats.all()
        others_taken = all(
            s.status in ['booked', 'reserved']
            for s in other_seats if s.id != seat.id
        )
        if others_taken:
            isolated_ids.append(seat.id)

    non_isolated = [s for s in seats if s.id not in isolated_ids]
    is_odd = len(non_isolated) % 2 != 0
    odd_discount = get_discount('odd') if is_odd else 0

    return render(request, 'booking/payment.html', {
        'seats': seats,
        'booking': booking,
        'total': total,
        'is_odd': is_odd,
        'odd_discount': odd_discount,
    })


def payment_success(request):
    if request.method == 'POST':
        booking = request.session.get('pending_booking')
        if not booking:
            return redirect('hall')

        seat_ids = booking['seat_ids']
        for seat_id in seat_ids:
            seat = Seat.objects.get(id=seat_id)
            if seat.status == 'reserved':
                Booking.objects.create(
                    seat=seat,
                    customer_name=booking['customer_name'],
                )
                seat.status = 'booked'
                seat.reserved_until = None
                seat.save()

        del request.session['pending_booking']
        return redirect('hall')

    return redirect('hall')

def payment_cancel(request):
    if request.method == 'POST':
        booking = request.session.get('pending_booking')
        if booking:
            seat_ids = booking['seat_ids']
            Seat.objects.filter(id__in=seat_ids, status='reserved').update(
                status='available',
                reserved_until=None
            )
            del request.session['pending_booking']
    return redirect('hall')

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