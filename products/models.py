from django.db import models
from django.utils import timezone
from UserManagement.models import *  # Adjust the import based on your project structure

# Create your models here.


class Composition(models.Model):
    product_name = models.CharField(max_length=255,blank=True, null=True)  # PARACETAMOL, IBUPROFEN, etc.
    composition_name = models.CharField(max_length=255,blank=True, null=True) # Example: "Paracetamol"
    product_type = models.CharField(max_length=50,blank=True, null=True)  # Example: "Tablet", "Syrup", etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return f"({self.product_name})"

class UserCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    markup_range = models.DecimalField(max_digits=5, decimal_places=2, default=15.00) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    

class UserCategoryMarkup(models.Model):
    category = models.ForeignKey(UserCategory, on_delete=models.CASCADE)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated',null=True,on_delete=models.CASCADE)

    class Meta:
        unique_together = ('category', 'product_type')

    def __str__(self):
        return f"{self.category.name} - {self.product_type.name} - {self.markup_percentage}%"



from decimal import Decimal  # Import Decimal
class Product(models.Model):
    product_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    form=models.CharField(max_length=255,blank=True, null=True)
    category=models.CharField(max_length=255,blank=True, null=True)
    company = models.CharField(max_length=100,blank=True, null=True)
    batch=models.CharField(max_length=255,blank=True, null=True)
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE,blank=True, null=True)
    product_image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    composition_name = models.CharField(max_length=255,blank=True, null=True) 
    expiry_date = models.DateField(default=timezone.now)
    MRP = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    pack_size = models.IntegerField(blank=True, null=True)
    user_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    GST = models.IntegerField(blank=True, null=True)
    free = models.CharField(max_length=25,blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    scheme = models.CharField(max_length=50,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated',null=True,on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Generate product_id ONLY on creation
        if self.pk is None and not self.product_id:
            last_product = Product.objects.filter(
                product_id__startswith='PRD'
            ).order_by('-id').first()

            if last_product and last_product.product_id:
                last_number = int(last_product.product_id.replace('PRD', ''))
                new_number = last_number + 1
            else:
                new_number = 1

            self.product_id = f"PRD{new_number:04d}"  # PRD0001

        super().save(*args, **kwargs)


    def __str__(self):
        return self.name



class ProductPricingDetail(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='pricing_detail')
    owner_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    owner_margin_amount = models.DecimalField(max_digits=10, decimal_places=2)
    owner_selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    retailer_margin = models.DecimalField(max_digits=10, decimal_places=2)
    retailer_margin_percent = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)
    override_margin_block = models.BooleanField(default=False)

    def clean(self):
        if not self.override_margin_block:
            if self.owner_selling_price > self.product.MRP:
                raise ValidationError("Owner Selling Price exceeds MRP and override is not allowed.")


class UserCategoryProductMarkup(models.Model):
    user_category = models.ForeignKey(UserCategory, on_delete=models.CASCADE, related_name='product_markups')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='user_category_markups')

    # Editable field by user
    owner_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    owner_margin_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    owner_selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    retailer_margin = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    retailer_margin_percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    scheme = models.CharField(max_length=20, null=True, blank=True)
    override_margin_block = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.product and self.owner_margin_percent is not None:
            product_price = self.product.price or 0
            self.owner_margin_amount = (self.owner_margin_percent / 100) * product_price
            self.owner_selling_price = product_price + self.owner_margin_amount
        super().save(*args, **kwargs)
    class Meta:
        unique_together = ('user_category', 'product')  # Ensure only 1 entry per user category + product

    def __str__(self):
        return f"{self.user_category.name} - {self.product.name}"


    # def get_customer_price(self, user):
    #     """Return price based on the user's category markup."""
    #     if not user.user_category:
    #         return self.price  # No category, return base price

    #     # Try to fetch the markup from UserCategoryMarkup
    #     markup = UserCategoryMarkup.objects.filter(
    #         category=user.user_category,
    #         product_type=self.product_type
    #     ).first()

    #     markup_percentage = Decimal(markup.markup_percentage) if markup else Decimal(0)
    #     customer_price = self.price * (Decimal(1) + markup_percentage / Decimal(100))
    #     return round(customer_price, 2)


    # def get_customer_price(self, user):
    #     """Get the product price after applying user-specific markup."""
    #     user_markup = UserProductMarkup.objects.filter(user=user, product_type=self.product_type).first()
    #     if user_markup:
    #         markup_percentage = Decimal(user_markup.markup_percentage)  # Convert to Decimal
    #     else:
    #         markup_percentage = Decimal(0)  # No markup if not set for user

    #     # Apply markup calculation using Decimal
    #     customer_price = self.price * (Decimal(1) + (markup_percentage / Decimal(100)))
        
    #     return round(customer_price, 2) 





# class UserProductMarkup(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)
#     markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Custom Markup %

#     class Meta:
#         unique_together = ('user','product_type')  # Ensure each user has only one markup per product type

#     def __str__(self):
#         return f"{self.user.first_name} - {self.product_type.name} - {self.markup_percentage}%"

class ProductMarkupByCategory(models.Model):
    category = models.ForeignKey(UserCategory, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    owner_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # %
    owner_selling_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    retailer_margin = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_by = models.ForeignKey('UserManagement.User', related_name='%(class)s_created', null=True, on_delete=models.CASCADE)
    updated_by = models.ForeignKey('UserManagement.User', related_name='%(class)s_updated', null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.product and self.owner_margin:
            buy_price = self.product.price or 0
            self.owner_selling_price = buy_price + (buy_price * self.owner_margin / 100)
            if self.product.MRP:
                self.retailer_margin = self.product.MRP - self.owner_selling_price
        super().save(*args, **kwargs)



# class Order(models.Model):
#     total_quantity = models.IntegerField()
#     order_no=models.CharField(unique=True,max_length=10)
#     total_price = models.DecimalField(max_digits=10, decimal_places=2)
#     net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     status = models.CharField(max_length=20, choices=[
#         ('ordered', 'Ordered'),
#         ('approved', 'Approved'),
#         ('packed', 'Packed'),
#         ('delivered', 'Delivered'),
#     ], default='ordered')
#     created_at = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey('UserManagement.User', related_name='orders_created_by', null=True, on_delete=models.SET_NULL)
#     updated_by = models.ForeignKey('UserManagement.User', related_name='orders_updated_by', null=True, on_delete=models.SET_NULL)
    
#     def __str__(self):
#         return f"Order #{self.id} - {self.total_amount}"

from django.utils import timezone

class Order(models.Model):
    total_quantity = models.IntegerField()
    order_no = models.CharField(unique=True, max_length=20,null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('ordered', 'Ordered'),
        ('billed', 'Billed'),
        ('packed', 'Packed'),
        ('delivered', 'Delivered'),
    ], default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('UserManagement.User', related_name='orders_created_by', null=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey('UserManagement.User', related_name='orders_updated_by', null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if not self.order_no:
            today = timezone.now().date()
            date_str = today.strftime('%Y%m%d')
            prefix = f'ORD{date_str}'

            # Count today's orders to generate next sequence
            count_today = Order.objects.filter(
                created_at__date=today
            ).count() + 1

            self.order_no = f'{prefix}{count_today:03d}'

            # Double check uniqueness in case of a race condition
            while Order.objects.filter(order_no=self.order_no).exists():
                count_today += 1
                self.order_no = f'{prefix}{count_today:03d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_no} - {self.total_amount}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255,blank=True,null=True)
    product_no = models.CharField(max_length=255,blank=True,null=True)
    expiry_date = models.DateField(default=timezone.now)
    batch=models.CharField(max_length=255,blank=True, null=True)
    MRP = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    GST = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    user_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey('UserManagement.User', related_name='order_items_created_by', null=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey('UserManagement.User', related_name='order_items_updated_by', null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=[
        ('ordered', 'Ordered'),
        ('billed', 'Billed'),
        ('packed', 'Packed'),
        ('delivered', 'Delivered'),
    ], default='ordered')
    def __str__(self):
        return f"{self.quantity} x {self.product_name} - {self.total_price}"

class OrderBilling(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="billing")
    total_gst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    actual_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    retailer_sale_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # what retailer sells for
    retailer_purchase_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # what retailer pays
    retailer_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    admin_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    outstanding_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('UserManagement.User', null=True, on_delete=models.SET_NULL, related_name='billings_created')

    def __str__(self):
        return f"Billing for Order #{self.order.order_no}"


class Query(models.Model):
    order = models.ForeignKey(
        'Order',              # same file-la irukkura Order model
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queries'
    )
    description = models.TextField()
    Business_name = models.CharField(max_length=100,null=True,blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)
    def __str__(self):
        return f"Query {self.created_by}"


class TempCartItem(models.Model):
    user = models.ForeignKey(
        'UserManagement.User',
        on_delete=models.CASCADE,
        related_name='temp_cart_items'
    )
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')

    def save(self, *args, **kwargs):
        self.total_price = (self.unit_price or Decimal('0')) * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.product} x {self.quantity}"



class QueryItem(models.Model):
    """
    Final saved missed-product items linked to Query.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('partial', 'Partially Issued'),
        ('cancelled', 'Cancelled'),
    ]

    query = models.ForeignKey(
        Query,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    product_name = models.CharField(max_length=255)

    requested_qty = models.PositiveIntegerField(default=0)
    issued_qty = models.PositiveIntegerField(default=0)
    pending_qty = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pending_qty = max(0, self.requested_qty - self.issued_qty)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} - {self.status} ({self.pending_qty} pending)"
    
    
    
class TempQueryItem(models.Model):
    """
    Missed products per user (temp table).
    """
    user = models.ForeignKey(
        'UserManagement.User',
        on_delete=models.CASCADE,
        related_name='temp_query_items'
    )
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    requested_qty = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True, null=True)  # OUT_OF_STOCK, PARTIAL_STOCK, QTY_ZERO
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user} - {self.product_name} ({self.requested_qty})"
    
    
class TempQueryHeader(models.Model):
    """
    Temp header for queries: Business name, contact, description; one per user.
    """
    user = models.OneToOneField(
        'UserManagement.User',
        on_delete=models.CASCADE,
        related_name='temp_query_header'
    )
    business_name = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TempQueryHeader for {self.user}"   
    
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=100)  # e.g., "500mg", "100ml", etc.
    pack_size = models.IntegerField(blank=True, null=True)
    MRP = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    user_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    batch = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey('UserManagement.User', related_name='variant_created', null=True, on_delete=models.CASCADE)
    updated_by = models.ForeignKey('UserManagement.User', related_name='variant_updated', null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.variant_name}"

