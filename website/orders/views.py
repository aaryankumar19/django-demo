# orders/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from supabase import create_client
from django.conf import settings
from django.views.decorators.http import require_http_methods
import uuid

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@csrf_exempt
@require_http_methods(["POST"])
def review_order_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

    try:
        auth_token = request.headers.get("AuthToken")
        body = json.loads(request.body.decode("utf-8"))
        address_id = body.get("address_id")

        if not auth_token or not address_id:
            return JsonResponse({"status": "error", "message": "AuthToken and address_id required"}, status=400)

        response = supabase.rpc(
            "order_summary",
            {"auth_token": auth_token, "p_address_id": int(address_id)}
        ).execute()

        data = response.data

        if data.get("error"):
            return JsonResponse({
                "status": "error",
                "message": str(data.get("error"))
            }, status=500)

        if not response.data:  # no results or cart empty
            return JsonResponse({"status": "error", "message": "No data returned"}, status=404)

        return JsonResponse({"status": "success", "data": data}, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def create_order_view(request):
    try:
        # Parse body
        body = json.loads(request.body.decode("utf-8"))
        address_id = body.get("address_id")
        payment_method_id = body.get("payment_method_id")

        if not address_id or not payment_method_id:
            return JsonResponse({"status": "error", "message": "address_id and payment_method_id are required"}, status=400)

        # Get auth token (e.g. from headers)
        auth_token = request.headers.get("AuthToken")
        if not auth_token:
            return JsonResponse({"status": "error", "message": "Missing Authorization token"}, status=401)

        # Remove Bearer if present
        if auth_token.lower().startswith("bearer "):
            auth_token = auth_token.split(" ", 1)[1]

        # Call Supabase function
        response = supabase.rpc(
            "create_order",
            {
                "auth_token": auth_token,
                "p_address_id": int(address_id),
                "p_payment_method_id": int(payment_method_id)
            }
        ).execute()

        # Handle Supabase errors
        if hasattr(response, "error") and response.error:
            return JsonResponse({"status": "error", "message": str(response.error)}, status=500)

        data = response.data[0] if response.data else None
        if not data:
            return JsonResponse({"status": "error", "message": "Unexpected response from database"}, status=500)

        return JsonResponse(data, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_orders_view(request):
    try:
        auth_token = request.headers.get("AuthToken")

        if not auth_token:
            return JsonResponse({"status": "error", "message": "AuthToken required"}, status=400)

        # Call Supabase RPC
        response = supabase.rpc(
            "get_user_orders",  # name of the Supabase function
            {"auth_token": auth_token}
        ).execute()

        data = response.data

        if not data:
            return JsonResponse({"status": "error", "message": "No orders found"}, status=404)

        if hasattr(data, "error") and data.error:  # handle Supabase RPC error
            return JsonResponse({"status": "error", "message": str(data.error)}, status=500)

        return JsonResponse({"status": "success", "data": data}, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["GET"])
def order_details_view(request, order_id):
    try:
        auth_token = request.headers.get("AuthToken")
        if not auth_token:
            return JsonResponse({"status": "error", "message": "AuthToken required"}, status=400)

        # Call Supabase RPC
        response = supabase.rpc(
            "get_order_details",
            {"auth_token": auth_token, "p_order_id": int(order_id)}
        ).execute()

        # Access data and error correctly
        if hasattr(response, "error") and response.error:
            return JsonResponse({
                "status": "error",
                "message": str(response.error)
            }, status=500)

        data = getattr(response, "data", None)

        if not data:
            return JsonResponse({"status": "error", "message": "Order not found"}, status=404)

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
