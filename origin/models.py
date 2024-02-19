from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError
# Create your models here.

from django.contrib.auth.models import User
from django.db import models

class Company(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=1000)
    company_address = models.CharField(max_length=1000)
    owner_number = models.CharField(max_length=20)
    manager_number = models.CharField(max_length=20, blank=True, null=True)

    def clean(self):
        if not self.owner_number and not self.manager_number:
            raise ValidationError("At least one of owner number or manager number must be provided.")
        
    def __str__(self):
        return f"{self.company_name} - {self.company_address} - {self.user.username}"

class UserWithCompanyCount(User):
    class Meta:
        proxy = True
    
    def company_count(self):
        return self.company_set.count()


        
class SalesProcess(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    interest = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    date_created = models.DateField(auto_now_add=True)
    def __str__(self) -> str:
        return f"{self.interest}"
    
class Product(models.Model):
    product_name = models.CharField(max_length=255)
    
    def __str__(self) -> str:
        return f"{self.product_name}"

class SalesPerformance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    closed_deals_count = models.IntegerField(default=0)



class ProductInterest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    average_interest = models.DecimalField(max_digits=5, decimal_places=2)
    count = models.IntegerField(default=0)
    
    def __str__(self) -> str:
        return f"{self.product.product_name}"

class ProductStatus(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('closed', 'Closed'),
        ('denied', 'Denied'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    description = models.TextField()
    date_updated = models.DateField(auto_now=True)
    
    def __str__(self) -> str:
        return f"{self.company} _ {self.status}"