from django.db.models.functions import ExtractDay, ExtractYear, ExtractMonth
from .models import *


def report_invoice(month, year=None, day=None):
    tong = 0
    if day:
        invoices = Invoice.objects.annotate(day=ExtractDay('created_date'), month=ExtractMonth('created_date'),
                                            year=ExtractYear('created_date')).values('id', 'total_amount', 'tour_id',
                                                                                     'payer_id', 'day', 'month',
                                                                                     'year', 'status_payment').filter(
            day=day,
            month=month,
            year=year, status_payment=1)
    else:
        invoices = Invoice.objects.annotate(month=ExtractMonth('created_date'),
                                            year=ExtractYear('created_date')).values('id', 'total_amount', 'tour_id',
                                                                                     'payer_id', 'month',
                                                                                     'year', 'status_payment').filter(
            month=month,
            year=year, status_payment=1)

    for i in invoices:
        tong = tong + float(i['total_amount'])

    return tong
