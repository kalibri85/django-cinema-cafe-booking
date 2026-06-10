from django.shortcuts import render, redirect
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Table, Seat, Booking, Discount, SeatPrice, Session, Movie, SeatStatus
from .booking_logic import check_isolated_seats, get_discount
from django.utils import timezone
from .forms import BookingForm


def home(request):
    today = date.today()
    sessions = Session.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=6),
        is_active=True
    ).select_related('movie').order_by('date', 'session_type')[:6]

    return render(request, 'booking/home.html', {
        'sessions': sessions,
    })

def repertoire(request):
    today = date.today()
    month_days = [today + timedelta(days=i) for i in range(30)]

    selected_date = request.GET.get('date', str(today))
    selected_type = request.GET.get('type', '')

    sessions = Session.objects.filter(
        date__gte=today,
        date__lte=today + timedelta(days=29),
        is_active=True
    ).select_related('movie')

    if selected_date:
        sessions = sessions.filter(date=selected_date)
    if selected_type:
        sessions = sessions.filter(session_type=selected_type)

    return render(request, 'booking/repertoire.html', {
        'sessions': sessions,
        'week_days': month_days,
        'selected_date': selected_date,
        'selected_type': selected_type,
        'today': today,
    })


def hall(request):
    session_id = request.GET.get('session_id') or request.session.get('current_session_id')

    if not session_id:
        return redirect('repertoire')

    try:
        current_session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return redirect('repertoire')

    request.session['current_session_id'] = int(session_id)

    row1 = Table.objects.prefetch_related('seats').filter(row=1).order_by('number')
    row2 = Table.objects.prefetch_related('seats').filter(row=2).order_by('number')

    seat_statuses = SeatStatus.objects.filter(session=current_session)
    status_map = {ss.seat_id: ss for ss in seat_statuses}

    pending = request.session.get('pending_booking', {})
    pending_seat_ids = [int(sid) for sid in pending.get('seat_ids', [])]

    if pending_seat_ids:
        actual_reserved = list(SeatStatus.objects.filter(
            seat_id__in=pending_seat_ids,
            session=current_session,
            status='reserved'
        ).values_list('seat_id', flat=True))

        if not actual_reserved:
            del request.session['pending_booking']
            pending_seat_ids = []
        elif len(actual_reserved) != len(pending_seat_ids):
            request.session['pending_booking']['seat_ids'] = [str(sid) for sid in actual_reserved]
            request.session.modified = True
            pending_seat_ids = actual_reserved

    isolated_discounts = {}
    for table in list(row1) + list(row2):
        for item in check_isolated_seats(table, status_map):
            isolated_discounts[item['seat_id']] = item['discount']

    odd_seat_discounts = {}
    if pending_seat_ids:
        odd_discount = get_discount('odd')
        pending_seats = Seat.objects.filter(id__in=pending_seat_ids).select_related('table')
        pending_table_ids = set(seat.table.id for seat in pending_seats)

        for table in list(row1) + list(row2):
            if table.id in pending_table_ids:
                for seat in table.seats.all():
                    seat_status = status_map.get(seat.id)
                    current_status = seat_status.status if seat_status else 'available'
                    if current_status == 'available' and seat.id not in pending_seat_ids:
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
        'status_map': status_map,
        'current_session': current_session,
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

    session_id = request.session.get('current_session_id')
    current_session = Session.objects.get(id=session_id) if session_id else None

    seat_ids = booking['seat_ids']
    seats = Seat.objects.filter(id__in=seat_ids).select_related('table')

    seat_price_obj = SeatPrice.objects.first()
    SEAT_PRICE = float(seat_price_obj.price) if seat_price_obj else 15.00
    TAX = float(seat_price_obj.tax) if seat_price_obj else 20.00

    odd_discount = get_discount('odd')
    isolated_discount = get_discount('isolated')

    seat_status_map = {
        ss.seat_id: ss.status
        for ss in SeatStatus.objects.filter(session=current_session)
    } if current_session else {}

    isolated_ids = {
        seat.id
        for seat in seats
        if all(
            seat_status_map.get(s.id, 'available') == 'booked'
            for s in seat.table.seats.all() if s.id != seat.id
        )
    }

    pending_seats_by_table = {}
    for seat in seats:
        pending_seats_by_table.setdefault(seat.table.id, []).append(seat)

    odd_ids = {
        table_seats[1].id
        for table_seats in pending_seats_by_table.values()
        if len(table_seats) == 2
    }

    discount_map = {
        seat.id: isolated_discount if seat.id in isolated_ids else odd_discount if seat.id in odd_ids else 0
        for seat in seats
    }

    seat_details = []
    for seat in seats:
        discount = discount_map[seat.id]
        price_after_discount = round(SEAT_PRICE * (1 - discount / 100), 2)
        tax_amount = round(price_after_discount * TAX / 100, 2)
        final_price = round(price_after_discount + tax_amount, 2)
        seat_details.append({
            'seat': seat,
            'original_price': SEAT_PRICE,
            'discount': discount,
            'price_after_discount': price_after_discount,
            'tax_amount': tax_amount,
            'final_price': final_price,
        })

    subtotal = round(sum(item['price_after_discount'] for item in seat_details), 2)
    total_tax = round(sum(item['tax_amount'] for item in seat_details), 2)
    total = round(sum(item['final_price'] for item in seat_details), 2)

    is_odd = len([s for s in seats if s.id not in isolated_ids]) % 2 != 0

    return render(request, 'booking/payment.html', {
        'seat_details': seat_details,
        'booking': booking,
        'subtotal': subtotal,
        'total_tax': total_tax,
        'total': total,
        'tax': TAX,
        'is_odd': is_odd,
        'odd_discount': odd_discount,
        'current_session': current_session,
    })


def payment_success(request):
    if request.method == 'POST':
        booking = request.session.get('pending_booking')
        if not booking:
            return redirect('hall')

        session_id = request.session.get('current_session_id')
        if not session_id:
            return redirect('repertoire')

        current_session = Session.objects.get(id=session_id)
        seat_ids = booking['seat_ids']
        seats = []

        for seat_id in seat_ids:
            seat = Seat.objects.get(id=seat_id)
            try:
                seat_status = SeatStatus.objects.get(seat=seat, session=current_session)
                if seat_status.status == 'reserved':
                    Booking.objects.create(
                        seat=seat,
                        session=current_session,
                        customer_name=booking['customer_name'],
                    )
                    seat_status.status = 'booked'
                    seat_status.reserved_until = None
                    seat_status.save()
                    seats.append(seat)
            except SeatStatus.DoesNotExist:
                pass

        seat_price_obj = SeatPrice.objects.first()
        SEAT_PRICE = float(seat_price_obj.price) if seat_price_obj else 15.00
        TAX = float(seat_price_obj.tax) if seat_price_obj else 20.00
        total = round(SEAT_PRICE * len(seats) * (1 + TAX / 100), 2)

        customer_name = booking['customer_name']
        customer_email = booking['customer_email']
        del request.session['pending_booking']

        return render(request, 'booking/booking_success.html', {
            'customer_name': customer_name,
            'customer_email': customer_email,
            'seats': seats,
            'total': total,
            'current_session': current_session,
        })

    return redirect('hall')


def payment_cancel(request):
    if request.method == 'POST':
        booking = request.session.get('pending_booking')
        if booking:
            session_id = request.session.get('current_session_id')
            if session_id:
                current_session = Session.objects.get(id=session_id)
                seat_ids = booking['seat_ids']
                SeatStatus.objects.filter(
                    seat_id__in=seat_ids,
                    session=current_session,
                    status='reserved'
                ).update(status='available', reserved_until=None)
            del request.session['pending_booking']
    session_id = request.session.get('current_session_id')
    if session_id:
        return redirect(f'/book/?session_id={session_id}')        
    return redirect('hall')


def book_seat(request, seat_id):
    if request.method == 'POST':
        seat = Seat.objects.get(id=seat_id)
        session_id = request.session.get('current_session_id')

        if not session_id:
            return JsonResponse({'success': False, 'message': 'No session selected'})

        current_session = Session.objects.get(id=session_id)

        seat_status, created = SeatStatus.objects.get_or_create(
            seat=seat,
            session=current_session,
            defaults={'status': 'available'}
        )

        if seat_status.status == 'reserved':
            if seat_status.reserved_until and seat_status.reserved_until < timezone.now():
                seat_status.status = 'available'
                seat_status.reserved_until = None
                seat_status.save()
            else:
                return JsonResponse({'success': False, 'message': 'Seat is temporarily reserved'})

        if seat_status.status != 'available':
            return JsonResponse({'success': False, 'message': 'Seat is not available'})

        seat_status.status = 'reserved'
        seat_status.reserved_until = timezone.now() + timedelta(minutes=10)
        seat_status.save()

        return JsonResponse({'success': True, 'message': 'Seat reserved'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def get_seats_status(request):
    session_id = request.session.get('current_session_id')
    seats = Seat.objects.select_related('table').all()

    status_map = {}
    if session_id:
        statuses = SeatStatus.objects.filter(session_id=session_id)
        status_map = {ss.seat_id: ss.status for ss in statuses}

    data = [
        {
            'id': seat.id,
            'number': seat.number,
            'status': status_map.get(seat.id, 'available'),
            'table_id': seat.table.id,
        }
        for seat in seats
    ]
    return JsonResponse({'seats': data})

def about(request):
    return render(request, 'booking/about.html')

def contacts(request):
    return render(request, 'booking/contacts.html')