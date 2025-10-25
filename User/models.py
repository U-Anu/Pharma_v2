from django.db import models
from django.contrib.auth.models import User

class CustomerOrder(models.Model):
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    number = models.CharField(max_length=50, null=True, blank=True)
    created_by = models.ForeignKey('UserManagement.User', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.customer_name
    
class OrderItemTemp(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)
    product_name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=10, choices=[('generic','Generic'),('brand','Brand')], default='generic')
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['id']

class OrderItemMain(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=10, choices=[('generic','Generic'),('brand','Brand')], default='generic')
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True, null=True)



