from django.contrib import admin # type: ignore
from .models import Customer
# Register your models here.
admin.site.register(Customer) 

from .models import SupportTicket, TicketMessage


class MessageInline(admin.TabularInline):
    model = TicketMessage
    extra = 0


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        'subject',
        'user',
        'category',
        'status',
        'created_at'
    )

    list_filter = ('status', 'category')

    search_fields = ('subject', 'description', 'user__username')

    inlines = [MessageInline]


admin.site.register(TicketMessage)
