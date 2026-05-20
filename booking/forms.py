from django import forms


class BookingForm(forms.Form):
    customer_name = forms.CharField(
        max_length=100,
        label='Your name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter your name'})
    )
    customer_email = forms.EmailField(
        label='Your email',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )