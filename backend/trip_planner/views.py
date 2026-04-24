from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TripPlan
from .serializers import TripPlanRequestSerializer
from .services.hos import simulate_trip
from .services.map_service import build_route


class PlanTripView(APIView):
    def post(self, request):
        try:
            #  Validate request
            serializer = TripPlanRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            #  Build route
            route = build_route(
                data["current_location"],
                data["pickup_location"],
                data["dropoff_location"],
            )

            # Safety check
            if not route or "distance_miles" not in route or "path" not in route:
                return Response(
                    {"error": "Invalid route generated"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            #  Run HOS simulation
            simulation = simulate_trip(
                route["distance_miles"],
                data["current_cycle_hours"],
                route_path=route["path"],
                pickup_location=data["pickup_location"],
                dropoff_location=data["dropoff_location"],
            )

            # Safety check
            if not simulation:
                return Response(
                    {"error": "Simulation failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Build response
            response_payload = {
                "route": route,
                "stops": simulation.get("stops", []),
                "logs": simulation.get("logs", []),
                "summary": simulation.get("summary", {}),
                "compliance": simulation.get("compliance", {}),
                "decisions": simulation.get("decisions", []),
            }

            #  Save to DB
            try:
                trip_plan = TripPlan.objects.create(
                    current_location=data["current_location"],
                    pickup_location=data["pickup_location"],
                    dropoff_location=data["dropoff_location"],
                    current_cycle_hours=data["current_cycle_hours"],
                    response=response_payload,
                )
                response_payload["trip_id"] = trip_plan.id
            except Exception as db_error:
                # DB failure shouldn't break API
                response_payload["trip_id"] = None
                response_payload["warning"] = f"DB save failed: {str(db_error)}"

            return Response(response_payload, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TripHistoryView(APIView):
    def get(self, request):
        try:
            trips = TripPlan.objects.all().order_by("-created_at")[:10]

            return Response([
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
            ])

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DemoTripView(APIView):
    def get(self, request):
        try:
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
                    "stops": simulation.get("stops", []),
                    "logs": simulation.get("logs", []),
                    "summary": simulation.get("summary", {}),
                    "compliance": simulation.get("compliance", {}),
                    "decisions": simulation.get("decisions", []),
                }
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )