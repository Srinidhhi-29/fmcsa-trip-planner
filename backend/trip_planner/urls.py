from django.urls import path

from .views import DemoTripView, PlanTripView, TripHistoryView

urlpatterns = [
    path("plan-trip", PlanTripView.as_view(), name="plan-trip"),
    path("demo-trip", DemoTripView.as_view(), name="demo-trip"),
    path("trips", TripHistoryView.as_view(), name="trip-history"),
]
