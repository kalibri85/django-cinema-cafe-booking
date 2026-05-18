from django.db import models


class Table(models.Model):
    row = models.IntegerField()
    # table number in the row
    number = models.IntegerField()
    # The methods for showing object as a text
    def __str__(self):
        return f"Row {self.row}, Table {self.number}"


class Seat(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('reserved', 'Reserved'),
    ]

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='seats')
    number = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"Seat {self.number} - {self.status}"


class Booking(models.Model):
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.seat}"
    
class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('odd', 'Odd number of seats'),
        ('isolated', 'Isolated seat'),
    ]

    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, unique=True)
    percentage = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.discount_type} - {self.percentage}%"    