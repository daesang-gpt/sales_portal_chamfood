from django.db import models

# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    sapCode = models.CharField(max_length=20)
    smCode = models.CharField(max_length=20)
    type = models.CharField(max_length=50)
    industry = models.CharField(max_length=100)
    ceo = models.CharField(max_length=50)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    manager = models.CharField(max_length=50)
    managerPhone = models.CharField(max_length=20)
    establishedDate = models.DateField()
    contractDate = models.DateField()
    paymentTerms = models.CharField(max_length=100)
    customerType = models.CharField(max_length=20)
    website = models.CharField(max_length=100, blank=True)
    monthlySales = models.BigIntegerField()
    lastContact = models.DateField()
    status = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Report(models.Model):
    date = models.DateField()
    company = models.CharField(max_length=100)
    companyCode = models.CharField(max_length=20)
    contactType = models.CharField(max_length=20)
    location = models.CharField(max_length=50)
    product = models.CharField(max_length=100)
    summary = models.TextField()
    tags = models.CharField(max_length=200)  # 콤마로 구분된 문자열로 저장
    status = models.CharField(max_length=20)
    createdAt = models.DateTimeField()

    def __str__(self):
        return f"{self.company} - {self.date}"
