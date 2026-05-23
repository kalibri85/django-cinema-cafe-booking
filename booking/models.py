from django.db import models
from django.utils import timezone


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
    # null=True - field can be null in the database; blank=True - field can be empty in the form
    reserved_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Seat {self.number} - {self.status}"
    
class SeatPrice(models.Model):
    price = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Seat price: £{self.price} (tax: {self.tax}%)"

    class Meta:
        verbose_name = 'Seat price'
        verbose_name_plural = 'Seat price'
class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)

    def __str__(self):
        return self.title   
    
class Session(models.Model):
    SESSION_CHOICES = [
        ('day', 'Day'),
        ('evening', 'Evening'),
    ]
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    session_type = models.CharField(max_length=10, choices=SESSION_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['date', 'session_type']
        ordering = ['date', 'session_type']

    def __str__(self):
        return f"{self.date} — {self.session_type}"         

class SeatStatus(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('reserved', 'Reserved'),
    ]
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='statuses')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='seat_statuses')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    reserved_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['seat', 'session']

    def __str__(self):
        return f"{self.seat} — {self.session} — {self.status}"
        

class Booking(models.Model):
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True, blank=True)
    customer_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['seat', 'session']

    def __str__(self):
        return f"{self.customer_name} - {self.seat} - {self.session}"
    
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
     