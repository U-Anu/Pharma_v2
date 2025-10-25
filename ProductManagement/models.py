from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=255)
    composition = models.CharField(max_length=255)
    brands = models.CharField(max_length=255)
    schedule = models.ForeignKey('Master.ScheduleTypes', related_name='%(class)s_scheduleType', on_delete=models.CASCADE)
    category = models.ForeignKey('Master.ProductCategory',related_name='%(class)s_Category', on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)
    pack_size = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number=models.CharField(max_length=255)
    requires_prescription = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name