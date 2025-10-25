from django.db import models
# Create your models here.

class Status(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)  # When the  record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the  record was last updated 
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class CertificationStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Status name, e.g., 'Active', 'Expired', 'Pending'
    description = models.TextField(blank=True, null=True)  # Optional description for the status
    created_at = models.DateTimeField(auto_now_add=True)  # When the  record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the  record was last updated
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Country(models.Model):
    name = models.CharField(max_length=100, )
    code = models.CharField(max_length=100, )  # ISO 3166-1 alpha-3 code (optional)
    created_at = models.DateTimeField(auto_now_add=True)  # When the certification record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the certification record was last updated
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    
    def __str__(self):
        return self.name
    

class State(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name='states', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # When the certification record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the certification record was last updated
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    
    def __str__(self):
        return f"{self.name}, {self.country.name}"
    
class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name='cities', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # When the certification record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the certification record was last updated
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    
    def __str__(self):
        return f"{self.name}, {self.state.name}, {self.state.country.name}"

from django.db import models

class Certification(models.Model):
    name = models.CharField(max_length=255, )  # Name of the certification (e.g., GMP, ISO)
    issued_by = models.CharField(max_length=255)  # Organization that issues the certification
    issue_date = models.DateField(null=True, blank=True)  # Date when the certification was issued
    expiry_date = models.DateField(null=True, blank=True)  # Expiry date (if applicable)
    certification_number = models.CharField(max_length=100, blank=True, null=True)  # Unique number associated with the certification
    status = models.ForeignKey(CertificationStatus, related_name='CertificationStatus', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    certification_document = models.FileField(upload_to='certification_documents/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # When the certification record was created
    updated_at = models.DateTimeField(auto_now=True)  # When the certification record was last updated
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.issued_by}"

    def is_expired(self):
        """
        Check if the certification is expired based on the expiry_date.
        """
        from datetime import date
        if self.expiry_date:
            return self.expiry_date < date.today()
        return False


class ProductCategory(models.Model):
    category_name=models.CharField(max_length=200)
    description=models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.category_name
    
class ScheduleTypes(models.Model):
    schedule_code = models.CharField(max_length=50, unique=True)
    schedule_name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.schedule_code
    
class NewsCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_created_by',null=True,on_delete=models.CASCADE)
    updated_by=models.ForeignKey('UserManagement.User',related_name='%(class)s_updated_by',null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.name