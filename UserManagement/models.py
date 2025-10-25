from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import *



# Custom manager for User model
class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        """
        Create and return a superuser with the given email and password.
        Sets is_superuser, is_active, and is_staff to True by default.
        """
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)
        other_fields.setdefault("is_staff", True)
        return self.create_user(email, password, **other_fields)

    def create_admin(self, email, password, **other_fields):
        """
        Create and return an admin user with the given email and password.
        Sets is_admin, is_staff, and is_active to True by default.
        """
        other_fields.setdefault("is_admin", True)
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_active", True)
        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        """
        Create and return a regular user with the given email and password.
        Raises ValueError if no email is provided.
        """
        if not email:
            raise ValueError(("You must provide a valid email address"))

        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user

class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)
        other_fields.setdefault("is_staff", True)
        return self.create_user(email, password, **other_fields)


    def create_admin(self, email, password, **other_fields):
        other_fields.setdefault("is_admin", True)
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_active", True)

        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        if not email:
            raise ValueError(("You must provide a valid email address"))

        email = self.normalize_email(email)
        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user


class Permissiontype(models.Model):
    active = models.BooleanField(default=False)
    type_name = models.CharField(max_length=200)
    description = models.TextField(max_length=800, blank=True, null=True)
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="permissiontype_created_by")
    update_by = models.ForeignKey("User", on_delete=models.CASCADE, blank=True, null=True,
                                  related_name="permissiontype_update_by")
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.type_name

class Usergroupmaster(models.Model):
    active = models.BooleanField(default=False)
    permission_type_id = models.ForeignKey('Permissiontype', on_delete=models.CASCADE)
    group_name = models.CharField(max_length=250)
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="usergroup_created_by",
                                   blank=True, null=True)
    update_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="usergroupmaster_update_by",
                                  blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group_name

class TempUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=False)
    phone_number = models.IntegerField(null=True, blank=True)
    alternate_phone_number = models.IntegerField(null=True, blank=True)
    email = models.EmailField("email address", unique=True)
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    )
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, null=True, blank=True)
    profile_image = models.ImageField(upload_to='temp_user_profile/', null=True, blank=True)
    password = models.CharField(max_length=128)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name


class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=False)
    phone_number = models.IntegerField(null=True, blank=True)
    alternate_phone_number = models.IntegerField(null=True, blank=True)
    email = models.EmailField("email address", unique=True)
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    )
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, null=True, blank=True)
    profile_image = models.ImageField(upload_to='user_profile/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    points=models.IntegerField(default=0)
    user_category = models.ForeignKey(UserCategory, null=True, blank=True, on_delete=models.SET_NULL)
    groups = models.ManyToManyField(
        'auth.Group', 
        related_name='custom_user_set',  # Custom related_name to avoid conflict
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', 
        related_name='custom_user_permissions_set',  # Custom related_name to avoid conflict
        blank=True
    )

    objects = CustomUserManager()

    REQUIRED_FIELDS = ["first_name"]
    USERNAME_FIELD = "email"

    def __str__(self):
        return self.first_name




class Function(models.Model):
    heading = models.CharField(max_length=250)  # Heading of the function
    function_name = models.CharField(max_length=100)  # Name of the function
    function_id = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Unique identifier for the function
    description = models.TextField(max_length=800, blank=True, null=True)  # Description of the function
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="function_created_by", blank=True, null=True)  # User who created the function
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the function was created
    updated_by = models.ForeignKey("User", on_delete=models.CASCADE, blank=True, null=True, related_name="function_updated_by")  # User who last updated the function
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when the function was last updated    
    
class Permission(models.Model):
    role = models.ForeignKey('Usergroupmaster', on_delete=models.CASCADE, blank=True, null=True)  # Related user group
    permissions = models.ForeignKey(Function, on_delete=models.CASCADE, blank=True, null=True, related_name="permission_connect_function")  # Related function
    create = models.BooleanField(default=False)  # Permission to create
    view = models.BooleanField(default=False)  # Permission to view
    update = models.BooleanField(default=False)  # Permission to update
    deleted = models.BooleanField(default=False)  # Permission to delete
    created_by = models.ForeignKey("User", on_delete=models.CASCADE, related_name="permission_created_by", blank=True, null=True)  # User who created the permission
    updated_by = models.ForeignKey("User", on_delete=models.CASCADE, blank=True, null=True, related_name="permission_updated_by")  # User who last updated the permission
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the permission was created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp when the permission was last updated



class PointAllocation(models.Model):
    min_amount = models.IntegerField()  
    max_amount = models.IntegerField(null=True, blank=True) 
    points = models.IntegerField()  
    def __str__(self):
        return f"{self.min_amount} - {self.max_amount or 'Above'}: {self.points} Points"
    


