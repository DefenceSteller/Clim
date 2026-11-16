
from django import forms
from .models import SupportTicket, TicketMessage


class SupportForm(forms.ModelForm):

    class Meta:
        model = SupportTicket

        fields = [
            'subject',
            'category',
            'description'
        ]

        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subject'
            }),

            'category': forms.Select(attrs={
                'class': 'form-select'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your issue or feedback'
            }),
        }


class MessageForm(forms.ModelForm):

    class Meta:
        model = TicketMessage

        fields = ['message']

        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your message...'
            })
        }
