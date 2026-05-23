from .models import Seat, Discount


def get_discount(discount_type):
    try:
        discount = Discount.objects.get(discount_type=discount_type, is_active=True)
        return discount.percentage
    except Discount.DoesNotExist:
        return 0

def check_odd_seats(seat_count):
    if seat_count % 2 != 0:
        percentage = get_discount('odd')
        return {
            'is_odd': True,
            'discount': percentage,
            'message': f'Add one more seat with {percentage}% discount to ensure your comfort!'
        }
    return {'is_odd': False}

def check_isolated_seats(table, status_map=None):
    seats = table.seats.all()
    isolated = []

    for seat in seats:
        seat_status = status_map.get(seat.id) if status_map else None
        current_status = seat_status.status if seat_status else seat.status

        if current_status == 'available':
            other_seats = [s for s in seats if s.id != seat.id]
            all_others_booked = all(
                (status_map.get(s.id).status if status_map and status_map.get(s.id) else s.status) == 'booked'
                for s in other_seats
            )

            if all_others_booked:
                percentage = get_discount('isolated')
                isolated.append({
                    'seat_id': seat.id,
                    'seat_number': seat.number,
                    'discount': percentage,
                })

    return isolated