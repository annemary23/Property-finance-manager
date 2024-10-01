from django import forms
from .models import Property, Room, Tenant, ServiceProvider, Complaint


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ["name", "address", "vat_applicable", "withholding_tax_applicable"]


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_number", "currency", "rent_amount"]


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "contact_info", "tenancy_start", "tenancy_end", "rent_paid"]


class ServiceProviderForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ["name", "service_type", "contact_info"]


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["title", "description", "property", "room", "status"]
