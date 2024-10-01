from django.urls import path
from django.contrib.auth import views as auth_views
from .views import ManagerLoginView
from django.contrib.auth.views import LogoutView
from . import views
from .views import edit_complaint
from .views import (
    dashboard_view,
    export_payment_history_csv,
    export_overdue_rent_csv,
    export_complaints_csv,
)

urlpatterns = [
    path("login/", ManagerLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("properties/", views.property_list, name="property_list"),
    path("property/add/", views.add_property, name="add_property"),
    path("property/<int:property_id>/room/add/", views.add_room, name="add_room"),
    path("tenants/", views.tenant_list, name="tenant_list"),
    path("tenant/add/", views.add_tenant, name="add_tenant"),
    path(
        "service_providers/", views.service_provider_list, name="service_provider_list"
    ),
    path(
        "service_provider/add/", views.add_service_provider, name="add_service_provider"
    ),
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("complaint/add/", views.add_complaint, name="add_complaint"),
    path("property/<int:property_id>/", views.property_detail, name="property_detail"),
    path(
        "api/available-rooms/<int:property_id>/",
        views.available_rooms,
        name="available_rooms",
    ),
    path(
    "property/delete/<int:pk>/",  
    views.delete_property,
    name="delete_property",
),
    path("room/delete/<int:room_id>/", views.delete_room, name="delete_room"),
    path("tenant/delete/<int:tenant_id>/", views.delete_tenant, name="delete_tenant"),
    path(
        "tenant/update_payment/<int:tenant_id>/",
        views.update_payment,
        name="update_payment",
    ),
    path(
        "service_provider/delete/<int:service_provider_id>/",
        views.delete_service_provider,
        name="delete_service_provider",
    ),
    path("tenant/edit/<int:tenant_id>/", views.edit_tenant, name="edit_tenant"),
    path(
        "api/available-rooms/<int:property_id>/",
        views.available_rooms,
        name="available_rooms",
    ),
    path("complaint/edit/<int:complaint_id>/", edit_complaint, name="edit_complaint"),
    path(
        "export-payment-history/",
        export_payment_history_csv,
        name="export_payment_history_csv",
    ),
    path(
        "export-overdue-rent/", export_overdue_rent_csv, name="export_overdue_rent_csv"
    ),
    path("export-complaints/", export_complaints_csv, name="export_complaints_csv"),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('complaint/delete/<int:complaint_id>/', views.delete_complaint, name='delete_complaint'),
]
