from django.contrib import admin
from .models import *



# Register your models here.
admin.site.register(Product)
admin.site.register(ProductType)
admin.site.register(Composition)
admin.site.register(Order)
admin.site.register(TempCartItem)
admin.site.register(TempQueryItem)
admin.site.register(TempQueryHeader)


