from django.shortcuts import render, redirect, get_object_or_404
from .forms import PropertyForm, RoomForm, ServiceProviderForm, ComplaintForm
from .models import Property, Room, Tenant, ServiceProvider, Complaint, Payment
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from datetime import date
from decimal import Decimal
from django.http import HttpResponse
from dateutil.relativedelta import relativedelta
from django.core.paginator import Paginator
from datetime import timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import Q
import csv
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# login view
class ManagerLoginView(LoginView):
    template_name = "login.html"


# dashboard view
@login_required
def dashboard_view(request):

    properties = Property.objects.all()

    tenants_per_property = []
    for property in properties:
        tenants_count = Tenant.objects.filter(room__property=property).count()
        tenants_per_property.append(
            {"property": property, "tenant_count": tenants_count}
        )

    overdue_rent = []
    for tenant in Tenant.objects.all():
        if tenant.room:
            current_month_start = tenant.tenancy_start + relativedelta(
                months=(date.today().month - tenant.tenancy_start.month)
            )
            next_due_date = current_month_start + relativedelta(months=1)

            rent_due = tenant.room.rent_amount
            rent_paid = tenant.rent_paid
            overdue_amount = 0

            if rent_paid < rent_due:
                overdue_amount = rent_due - rent_paid

            if date.today() > next_due_date and overdue_amount > 0:
                overdue_rent.append(
                    {
                        "room_number": tenant.room.room_number,
                        "property_name": tenant.room.property.name,
                        "tenant_name": tenant.name,
                        "amount_overdue": f"{tenant.room.currency} {overdue_amount:,.2f}",
                    }
                )

    upcoming_rent = []
    today = timezone.now().date()
    two_weeks_from_now = today + timedelta(weeks=2)

    for tenant in Tenant.objects.all():
        if tenant.room and tenant.tenancy_start:
            current_month_start = tenant.tenancy_start + relativedelta(
                months=(date.today().month - tenant.tenancy_start.month)
            )
            next_due_date = current_month_start + relativedelta(months=1)

            rent_due = tenant.room.rent_amount
            rent_paid = tenant.rent_paid

            if next_due_date - today <= timedelta(weeks=2) and rent_paid < rent_due:
                upcoming_rent.append(
                    {
                        "room_number": tenant.room.room_number,
                        "property_name": tenant.room.property.name,
                        "tenant_name": tenant.name,
                        "rent_due": f"{tenant.room.currency} {rent_due - rent_paid:,.2f}",
                        "due_date": next_due_date,
                    }
                )

    search_query = request.GET.get("search_tenant", "")

    if search_query:
        payment_history = (
            Payment.objects.select_related("tenant")
            .filter(Q(tenant__name__icontains=search_query))
            .order_by("-date_paid")
        )
    else:
        payment_history = Payment.objects.select_related("tenant").order_by(
            "-date_paid"
        )

    complaints_pending = Complaint.objects.filter(status="Pending")
    complaints_in_progress = Complaint.objects.filter(status="In Progress")
    complaints_complete = Complaint.objects.filter(status="Complete")

    complaints_pending_count = complaints_pending.count()
    complaints_in_progress_count = complaints_in_progress.count()
    complaints_complete_count = complaints_complete.count()

    payment_dates = [
        payment.date_paid.strftime("%Y-%m-%d") for payment in payment_history
    ]
    payment_amounts = [payment.amount_paid for payment in payment_history]

    complaints_combined = complaints_pending | complaints_in_progress

    items_per_page = 4
    overdue_rent_paginator = Paginator(overdue_rent, items_per_page)
    upcoming_rent_paginator = Paginator(upcoming_rent, items_per_page)
    payment_history_paginator = Paginator(payment_history, items_per_page)
    complaints_paginator = Paginator(complaints_combined, items_per_page)

    overdue_rent_page = request.GET.get("overdue_rent_page", 1)
    upcoming_rent_page = request.GET.get("upcoming_rent_page", 1)
    payment_history_page = request.GET.get("payment_history_page", 1)
    complaints_page = request.GET.get("complaints_page", 1)

    context = {
        "properties": properties,
        "tenants_per_property": tenants_per_property,
        "overdue_rent": overdue_rent_paginator.get_page(overdue_rent_page),
        "upcoming_rent": upcoming_rent_paginator.get_page(upcoming_rent_page),
        "payment_history": payment_history_paginator.get_page(payment_history_page),
        "complaints": complaints_paginator.get_page(complaints_page),
        "complaints_pending_count": complaints_pending_count,
        "complaints_in_progress_count": complaints_in_progress_count,
        "complaints_complete_count": complaints_complete_count,
        "payment_dates": payment_dates,
        "payment_amounts": payment_amounts,
        "search_query": search_query,
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        html = render_to_string("dashboard.html", context, request=request)

        table_html = html.split('<div id="paymentHistoryTable"')[1].split("</div>")[0]
        return JsonResponse(
            {"table_html": f'<div id="paymentHistoryTable"{table_html}</div>'}
        )

    return render(request, "dashboard.html", context)


# Tenant Management Views
@login_required
def tenant_list(request):
    tenants = Tenant.objects.all()
    tenant_data = []

    for tenant in tenants:

        if tenant.room:

            current_month_start = tenant.tenancy_start + relativedelta(
                months=(date.today().month - tenant.tenancy_start.month)
            )
            next_due_date = current_month_start + relativedelta(months=1)

            rent_due = tenant.room.rent_amount
            rent_paid = tenant.rent_paid
            overdue = False
            overdue_amount = 0

            if rent_paid > rent_due:

                next_month_balance = rent_paid - rent_due
                rent_due = 0
            else:

                rent_due = rent_due - rent_paid

            if date.today() > next_due_date and rent_due > 0:
                overdue = True
                overdue_amount = rent_due

            tenant_data.append(
                {
                    "id": tenant.id,
                    "name": tenant.name,
                    "property_name": (
                        tenant.room.property.name
                        if tenant.room.property
                        else "No Property Assigned"
                    ),
                    "room_number": (
                        tenant.room.room_number if tenant.room else "No Room Assigned"
                    ),
                    "contact_info": tenant.contact_info,
                    "rent_paid": rent_paid,
                    "rent_due": rent_due,
                    "currency": tenant.room.currency if tenant.room else "",
                    "overdue": overdue,
                    "overdue_amount": overdue_amount,
                }
            )
        else:

            tenant_data.append(
                {
                    "id": tenant.id,
                    "name": tenant.name,
                    "property_name": "No Property Assigned",
                    "room_number": "No Room Assigned",
                    "contact_info": tenant.contact_info,
                    "rent_paid": 0,
                    "rent_due": 0,
                    "currency": "",
                    "overdue": False,
                    "overdue_amount": 0,
                }
            )

    query = request.GET.get("q")
    if query:
        tenant_data = [
            tenant
            for tenant in tenant_data
            if query.lower() in tenant["name"].lower()
            or query.lower() in tenant["property_name"].lower()
            or str(tenant["room_number"]).lower() in query.lower()
        ]

    return render(request, "tenant_list.html", {"tenants": tenant_data})


@login_required
def add_tenant(request):
    if request.method == "POST":
        name = request.POST.get("name")
        contact_info = request.POST.get("contact_info")
        room_id = request.POST.get("room")
        tenancy_start = request.POST.get("tenancy_start")
        tenancy_end = request.POST.get("tenancy_end")
        rent_paid = request.POST.get("rent_paid")
        date_paid = request.POST.get("date_paid")

        room = Room.objects.get(id=room_id) if room_id else None

        # Create the tenant
        tenant = Tenant.objects.create(
            name=name,
            contact_info=contact_info,
            room=room,
            rent_paid=rent_paid if rent_paid else 0,
            tenancy_start=tenancy_start if tenancy_start else None,
            tenancy_end=tenancy_end if tenancy_end else None,
        )

        if rent_paid and date_paid:
            Payment.objects.create(
                tenant=tenant, amount_paid=rent_paid, date_paid=date_paid
            )

        return redirect("tenant_list")

    properties = Property.objects.all()

    rooms = Room.objects.none()

    return render(
        request, "add_tenant.html", {"properties": properties, "available_rooms": rooms}
    )


# Service Provider Management Views
@login_required
def service_provider_list(request):
    service_providers = ServiceProvider.objects.all()
    return render(
        request, "service_provider_list.html", {"service_providers": service_providers}
    )


@login_required
def add_service_provider(request):
    if request.method == "POST":
        form = ServiceProviderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_provider_list")
    else:
        form = ServiceProviderForm()
    return render(request, "add_service_provider.html", {"form": form})


# Complaint Management Views
@login_required
def complaint_list(request):
    complaints = Complaint.objects.all()
    return render(request, "complaint_list.html", {"complaints": complaints})


@login_required
def add_complaint(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("complaint_list")
    else:
        form = ComplaintForm()
    return render(request, "add_complaint.html", {"form": form})


@login_required
def property_detail(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    rooms = property.rooms.all()
    room_data = []

    for room in rooms:
        if hasattr(room, "tenant"):
            rent_due = room.rent_amount - room.tenant.rent_paid
            overdue = False
            if date.today().month != room.tenant.tenancy_start.month and rent_due > 0:
                overdue = True

            room_data.append(
                {
                    "id": room.id,
                    "room_number": room.room_number,
                    "rent_amount": room.rent_amount,
                    "tenant_name": room.tenant.name,
                    "tenant_contact": room.tenant.contact_info,
                    "rent_paid": room.tenant.rent_paid,
                    "rent_due": rent_due,
                    "overdue": overdue,
                }
            )
        else:
            room_data.append(
                {
                    "id": room.id,
                    "room_number": room.room_number,
                    "rent_amount": room.rent_amount,
                    "tenant_name": "Available",
                    "tenant_contact": "N/A",
                    "rent_paid": 0,
                    "rent_due": 0,
                    "overdue": False,
                }
            )

    return render(
        request,
        "property_detail.html",
        {
            "property": property,
            "rooms": room_data,
        },
    )


@login_required
def available_rooms(request, property_id):
    rooms = Room.objects.filter(property_id=property_id, tenant__isnull=True)
    room_data = [{"id": room.id, "room_number": room.room_number} for room in rooms]
    return JsonResponse({"rooms": room_data})


@login_required
def delete_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if request.method == "POST":
        property.delete()
        return redirect("property_list")


@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        room.delete()
        return redirect("property_detail", property_id=room.property.id)


@login_required
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)

    if request.method == "POST":
        tenant.delete()
        return redirect("tenant_list")


@login_required
def update_payment(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)

    if request.method == "POST":
        # Convert the amount_paid to Decimal
        amount_paid = Decimal(request.POST.get("amount_paid"))
        date_paid = request.POST.get("date_paid")

        # Add the Decimal amount_paid to tenant's rent_paid
        tenant.rent_paid += amount_paid
        tenant.save()

        # Log the payment history
        Payment.objects.create(
            tenant=tenant, amount_paid=amount_paid, date_paid=date_paid
        )

    # Fetch payment history (limit to 4 records)
    payment_history = Payment.objects.filter(tenant=tenant).order_by("-date_paid")[:4]

    return render(
        request,
        "update_payment.html",
        {
            "tenant": tenant,
            "payment_history": payment_history,
        },
    )


@login_required
def delete_service_provider(request, service_provider_id):
    service_provider = get_object_or_404(ServiceProvider, id=service_provider_id)
    service_provider.delete()
    return redirect("service_provider_list")


@login_required
def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)

    rooms = Room.objects.none()

    if request.method == "POST":
        tenant.name = request.POST.get("name")
        tenant.contact_info = request.POST.get("contact_info")
        property_id = request.POST.get("property")
        room_id = request.POST.get("room")

        if room_id:
            new_room = Room.objects.get(id=room_id)
            if tenant.room != new_room:
                tenant.room = new_room
                tenant.rent_paid = 0

        tenant.tenancy_start = request.POST.get("tenancy_start")
        tenant.tenancy_end = request.POST.get("tenancy_end")
        tenant.save()

        return redirect("tenant_list")

    property_id = request.GET.get("property")

    if tenant.room:

        rooms = Room.objects.filter(
            property=tenant.room.property, tenant__isnull=True
        ) | Room.objects.filter(id=tenant.room.id)
    elif property_id:

        try:
            selected_property = Property.objects.get(id=property_id)
            rooms = Room.objects.filter(property=selected_property, tenant__isnull=True)
        except Property.DoesNotExist:
            rooms = Room.objects.none()

    return render(
        request,
        "edit_tenant.html",
        {
            "tenant": tenant,
            "properties": Property.objects.all(),
            "rooms": rooms,
        },
    )


@login_required
def available_rooms(request, property_id):
    rooms = Room.objects.filter(property_id=property_id, tenant__isnull=True)
    room_list = [{"id": room.id, "room_number": room.room_number} for room in rooms]
    return JsonResponse(room_list, safe=False)


@login_required
def property_list(request):
    properties = Property.objects.all()
    return render(request, "property_list.html", {"properties": properties})


# View to list properties
@login_required
def property_list(request):
    properties = Property.objects.all()
    property_data = []

    for prop in properties:
        rooms = Room.objects.filter(property=prop)
        rooms_available = rooms.filter(tenant__isnull=True).count()
        rooms_taken = rooms.filter(tenant__isnull=False).count()

        property_data.append(
            {
                "property": prop,
                "rooms_available": rooms_available,
                "rooms_taken": rooms_taken,
            }
        )

    return render(request, "property_list.html", {"property_data": property_data})


# View to add a new property
@login_required
def add_property(request):
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("property_list")
    else:
        form = PropertyForm()

    return render(request, "add_property.html", {"form": form})


# View to delete a property
@login_required
def delete_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        property.delete()
        return redirect("property_list")
    return HttpResponse("Method not allowed", status=405)


# View to display property details
@login_required
def property_detail(request, property_id):
    property = get_object_or_404(Property, pk=property_id)
    rooms = Room.objects.filter(property=property)

    return render(
        request, "property_detail.html", {"property": property, "rooms": rooms}
    )


# View to add a new room to a property
@login_required
def add_room(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.property = property
            room.save()
            return redirect("property_detail", property_id=property_id)
    else:
        form = RoomForm()

    return render(request, "add_room.html", {"form": form, "property": property})


@login_required
def edit_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        complaint.title = request.POST.get("title")
        complaint.property_id = request.POST.get("property")
        complaint.room_id = request.POST.get("room")
        complaint.status = request.POST.get("status")
        complaint.save()

        return redirect("complaint_list")

    properties = Property.objects.all()
    rooms = Room.objects.filter(property=complaint.property)
    return render(
        request,
        "edit_complaint.html",
        {
            "complaint": complaint,
            "properties": properties,
            "rooms": rooms,
        },
    )


@login_required
def export_payment_history_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="payment_history.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["Tenant Name", "Room Number", "Property Name", "Amount Paid", "Date Paid"]
    )

    for payment in Payment.objects.select_related("tenant").all():
        writer.writerow(
            [
                payment.tenant.name,
                payment.tenant.room.room_number,
                payment.tenant.room.property.name,
                payment.amount_paid,
                payment.date_paid,
            ]
        )

    return response


@login_required
def export_overdue_rent_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="overdue_rent.csv"'

    writer = csv.writer(response)
    writer.writerow(["Room Number", "Property Name", "Tenant Name", "Amount Overdue"])

    for tenant in Tenant.objects.all():
        if tenant.room:
            rent_due = tenant.room.rent_amount - tenant.rent_paid
            if rent_due > 0:
                writer.writerow(
                    [
                        tenant.room.room_number,
                        tenant.room.property.name,
                        tenant.name,
                        rent_due,
                    ]
                )

    return response


@login_required
def export_complaints_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="complaints.csv"'

    writer = csv.writer(response)
    writer.writerow(["Title", "Property Name", "Room Number", "Status"])

    for complaint in Complaint.objects.all():
        writer.writerow(
            [
                complaint.title,
                complaint.room.property.name if complaint.room else "N/A",
                complaint.room.room_number if complaint.room else "N/A",
                complaint.status,
            ]
        )

    return response

def delete_complaint(request, complaint_id):
    
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, id=complaint_id)
        complaint.delete()
        messages.success(request, 'Complaint has been deleted successfully.')
        return redirect('complaint_list')
    else:
        return redirect('complaint_list')
