from django import forms
from captcha.fields import CaptchaField

class SubscriptionPageForm(forms.Form):
    email = forms.EmailField(help_text='Inserire un indirizzo e-mail valido')
    opt_in = forms.BooleanField(required=True)
    captcha = CaptchaField()
