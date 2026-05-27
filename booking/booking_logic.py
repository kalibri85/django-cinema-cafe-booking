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

    def get_status(seat):
        if status_map:
            ss = status_map.get(seat.id)
            return ss.status if ss else 'available'
        return 'available'

    for seat in seats:
        if get_status(seat) == 'available':
            other_seats = [s for s in seats if s.id != seat.id]
            all_others_booked = all(
                get_status(s) == 'booked'
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