from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def api_index(request):
    return JsonResponse(
        {
            "message": "FMCSA Trip Planner API",
            "frontend": "http://localhost:5173",
            "endpoints": {
                "plan_trip": "POST /api/plan-trip",
                "demo_trip": "GET /api/demo-trip",
                "trip_history": "GET /api/trips",
                "admin": "GET /admin/",
            },
        }
    )

urlpatterns = [
    path("", api_index, name="api-index"),
    path("admin/", admin.site.urls),
    path("api/", include("trip_planner.urls")),
]
