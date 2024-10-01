from django.db import models


class Property(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    vat_applicable = models.BooleanField(default=False)
    withholding_tax_applicable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Room(models.Model):
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="rooms"
    )
    room_number = models.CharField(max_length=50)
    currency = models.CharField(max_length=3, choices=(("UGX", "UGX"), ("USD", "USD")))
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.room_number} - {self.property.name}"


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    room = models.ForeignKey("Room", on_delete=models.SET_NULL, null=True, blank=True)
    contact_info = models.CharField(max_length=100)
    rent_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, null=True, blank=True
    )
    tenancy_start = models.DateField(null=True, blank=True)
    tenancy_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Complaint(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=(
            ("Pending", "Pending"),
            ("In Progress", "In Progress"),
            ("Complete", "Complete"),
        ),
        default="Pending",
    )

    def __str__(self):
        return self.title


class Payment(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="payments"
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()

    def __str__(self):
        return (
            f"Payment of {self.amount_paid} on {self.date_paid} for {self.tenant.name}"
        )
