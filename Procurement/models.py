from django.db import models
from Master.models import *
# Create your models here.
from django.db import models

class SupplierType(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Name of the supplier type (e.g., Pharmaceutical)
    description = models.TextField(blank=True, null=True)  # Optional description about the supplier type
    created_at = models.DateTimeField(auto_now_add=True)  # When the  record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the  record was last updated

    def __str__(self):
        return self.name

class Supplier(models.Model):
    # Basic information about the supplier
    name = models.CharField(max_length=255, unique=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)  # Supplier's main contact person
    phone = models.CharField(max_length=15, blank=True, null=True)  # Supplier's phone number
    secondary_phone = models.CharField(max_length=15, blank=True, null=True)  # Supplier's phone number
    email = models.EmailField(blank=True, null=True)  # Supplier's email
    website = models.URLField(blank=True, null=True)  # Supplier's website URL
    address = models.TextField(blank=True, null=True)  # Full address of the supplier
    country = models.ForeignKey(Country, related_name='Country', on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, related_name='State', on_delete=models.SET_NULL, null=True)
    city = models.ForeignKey(City, related_name='City', on_delete=models.SET_NULL, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)  # Supplier's postal/zip code

    # Supplier credentials and certifications
    license_number = models.CharField(max_length=50, blank=True, null=True)  # Business license number
    license_expiry_date = models.DateField(blank=True, null=True)  # Expiration date for the license
    certifications = models.ManyToManyField(Certification, related_name='certifications', blank=True)
    # Supplier financial details
    gst_number = models.CharField(max_length=50, unique=True, blank=True, null=True)  # GST or tax ID
    bank_details = models.TextField(blank=True, null=True)  # Bank details for payments
    payment_terms = models.CharField(max_length=100, blank=True, null=True)  # Payment terms (e.g., 30 days, 60 days)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Supplier's credit limit
    payment_methods = models.CharField(max_length=255, blank=True, null=True)  # Payment methods accepted (e.g., bank transfer, credit card)

    # Supplier performance metrics
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Supplier's average performance score
    reliability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Supplier's reliability score (e.g., on-time delivery rate)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Supplier's quality score (based on product defects or feedback)
    customer_service_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Customer service score

    # Supplier type (e.g., pharmaceutical, medical device, equipment supplier)
    supplier_type = models.ForeignKey(SupplierType, related_name='suppliertype', on_delete=models.SET_NULL, null=True)
    # Contract information
    contract_start_date = models.DateField(blank=True, null=True)  # Contract start date
    contract_end_date = models.DateField(blank=True, null=True)  # Contract end date
    contract_terms = models.TextField(blank=True, null=True)  # Terms and conditions of the contract

    # Additional fields for audit and tracking purposes
    created_at = models.DateTimeField(auto_now_add=True)  # Date when the supplier record was created
    updated_at = models.DateTimeField(auto_now=True)  # Date when the supplier record was last updated
    is_active = models.BooleanField(default=True)  # If the supplier is active or inactive

    def __str__(self):
        return self.name

    def get_full_address(self):
        return f"{self.address}, {self.region}, {self.country}, {self.postal_code}"

    def get_supplier_performance(self):
        """
        Returns a tuple of performance scores
        """
        return {
            'performance_score': self.performance_score,
            'reliability_score': self.reliability_score,
            'quality_score': self.quality_score,
            'customer_service_score': self.customer_service_score
        }


