from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TripPlan
from .serializers import TripPlanRequestSerializer
from .services.hos import simulate_trip
from .services.map_service import build_route


class PlanTripView(APIView):
    def post(self, request):
        serializer = TripPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        route = build_route(
            data["current_location"],
            data["pickup_location"],
            data["dropoff_location"],
        )
        simulation = simulate_trip(
            route["distance_miles"],
            data["current_cycle_hours"],
            route_path=route["path"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
        )

        response_payload = {
            "route": route,
            "stops": simulation["stops"],
            "logs": simulation["logs"],
            "summary": simulation["summary"],
            "compliance": simulation["compliance"],
            "decisions": simulation["decisions"],
        }
        trip_plan = TripPlan.objects.create(
            current_location=data["current_location"],
            pickup_location=data["pickup_location"],
            dropoff_location=data["dropoff_location"],
            current_cycle_hours=data["current_cycle_hours"],
            response=response_payload,
        )
        response_payload["trip_id"] = trip_plan.id

        return Response(response_payload, status=status.HTTP_200_OK)


class TripHistoryView(APIView):
    def get(self, request):
        trips = TripPlan.objects.all()[:10]
        return Response(
            [
                {
                    "id": trip.id,
                    "created_at": trip.created_at.isoformat(),
                    "current_location": trip.current_location,
                    "pickup_location": trip.pickup_location,
                    "dropoff_location": trip.dropoff_location,
                    "current_cycle_hours": trip.current_cycle_hours,
                    "summary": trip.response.get("summary", {}),
                    "compliance": trip.response.get("compliance", {}),
                }
                for trip in trips
            ]
        )


class DemoTripView(APIView):
    def get(self, request):
        route = build_route("Chicago, IL", "St. Louis, MO", "Los Angeles, CA")
        simulation = simulate_trip(
            route["distance_miles"],
            18,
            route_path=route["path"],
            pickup_location="St. Louis, MO",
            dropoff_location="Los Angeles, CA",
        )
        return Response(
            {
                "route": route,
                "stops": simulation["stops"],
                "logs": simulation["logs"],
                "summary": simulation["summary"],
                "compliance": simulation["compliance"],
                "decisions": simulation["decisions"],
            }
        )
