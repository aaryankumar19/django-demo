from supabase import create_client
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import uuid

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_valid_auth_token(request):
    token = request.headers.get("AuthToken")
    if not token:
        return None, JsonResponse({"status": "error", "message": "AuthToken is required"}, status=400)
    try:
        uuid.UUID(token)
        return token, None
    except ValueError:
        return None, JsonResponse({"status": "error", "message": "Invalid auth token"}, status=400)

def parse_request_body(request):
    try:
        return json.loads(request.body.decode("utf-8")), None
    except json.JSONDecodeError:
        return None, JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)

def handle_supabase_rpc(function_name, params, success_message, error_message, raw=False):
    try:
        resp = supabase.rpc(function_name, params).execute()
        if getattr(resp, "error", None):
            # 👇 TEMP: print to server logs
            print(f"[Supabase RPC Error] {function_name} => {resp.error}")

            return JsonResponse({
                "status": "error",
                "message": resp.error.message if hasattr(resp.error, "message") else str(resp.error)
            }, status=400)
        if raw:
            return JsonResponse(resp.data[0], status=200)
        return JsonResponse({
            "status": "success",
            "message": success_message,
            "data": resp.data
        }, status=200)
    except Exception as e:
        # 👇 TEMP: print to server logs
        print(f"[Exception in RPC] {function_name} => {e}")

        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_address(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    required_fields = ["full_name", "phone_number", "address_line", "city", "pincode"]
    if any(f not in body for f in required_fields):
        return JsonResponse({"status": "error", "message": "All address fields are required"}, status=400)

    return handle_supabase_rpc(
        "add_address",
        {
            "auth_token": auth_token,
            "p_full_name": body["full_name"],
            "p_phone_number": body["phone_number"],
            "p_address_line": body["address_line"],
            "p_city": body["city"],
            "p_pincode": body["pincode"],
            "p_latitude": body.get("latitude"),
            "p_longitude": body.get("longitude"),
        },
        "Address added successfully",
        "Cannot add address, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["GET"])
def get_addresses(request):
    auth_token, error = get_valid_auth_token(request)
    if error: return error
    return handle_supabase_rpc(
        "get_addresses",
        {"auth_token": auth_token},
        "Addresses fetched successfully",
        "Cannot fetch addresses, please try again later"
    )

@csrf_exempt
@require_http_methods(["POST"])
def delete_address(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    address_id = body.get("address_id")
    if not address_id:
        return JsonResponse({"status": "error", "message": "address_id is required"}, status=400)

    return handle_supabase_rpc(
        "delete_address",
        {"auth_token": auth_token, "p_address_id": int(address_id)},
        "Address deleted successfully",
        "Cannot delete address, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["POST"])
def edit_address(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    address_id = body.get("address_id")
    if not address_id:
        return JsonResponse({"status": "error", "message": "address_id is required"}, status=400)

    return handle_supabase_rpc(
        "edit_address",
        {
            "auth_token": auth_token,
            "p_address_id": int(address_id),
            "p_full_name": body.get("full_name"),
            "p_phone_number": body.get("phone_number"),
            "p_address_line": body.get("address_line"),
            "p_city": body.get("city"),
            "p_pincode": body.get("pincode"),
            "p_latitude": body.get("latitude"),
            "p_longitude": body.get("longitude"),
        },
        "Address updated successfully",
        "Cannot edit address, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["POST"])
def add_to_wishlist(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    product_id = body.get("product_id")
    if not product_id:
        return JsonResponse({"status": "error", "message": "product_id is required"}, status=400)

    return handle_supabase_rpc(
        "add_to_wishlist",
        {"auth_token": auth_token, "p_product_id": int(product_id)},
        "Added to wishlist",
        "Cannot add to wishlist, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["POST"])
def remove_from_wishlist(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    product_id = body.get("product_id")
    if not product_id:
        return JsonResponse({"status": "error", "message": "product_id is required"}, status=400)

    return handle_supabase_rpc(
        "remove_from_wishlist",
        {"auth_token": auth_token, "p_product_id": int(product_id)},
        "Removed from wishlist",
        "Cannot remove from wishlist, try again later",
        raw=True
    )

@require_http_methods(["GET"])
def get_wishlist(request):
    auth_token, error = get_valid_auth_token(request)
    if error: return error

    try:
        resp = supabase.rpc("get_wishlist", {"auth_token": auth_token}).execute()
        if getattr(resp, "error", None):
            return JsonResponse({
                # "error": resp.error.message,  # debug
                "error": "Cannot fetch wishlist, please try again later"
            }, status=400)
        return JsonResponse({"wishlist": resp.data}, status=200)
    except Exception as e:
        return JsonResponse({
            # "error": str(e),  # debug
            "error": "Cannot fetch wishlist, please try again later"
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_to_cart(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    product_id = body.get("product_id")
    quantity = body.get("quantity", 1)
    if not product_id:
        return JsonResponse({"status": "error", "message": "product_id is required"}, status=400)

    return handle_supabase_rpc(
        "add_to_cart",
        {"auth_token": auth_token, "p_product_id": int(product_id), "p_quantity": int(quantity)},
        "Added to cart",
        "Cannot add to cart, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["POST"])
def remove_from_cart(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    product_id = body.get("product_id")
    if not product_id:
        return JsonResponse({"status": "error", "message": "product_id is required"}, status=400)

    return handle_supabase_rpc(
        "remove_from_cart",
        {"auth_token": auth_token, "p_product_id": int(product_id)},
        "Removed from cart",
        "Cannot remove from cart, try again later",
        raw=True
    )

@csrf_exempt
@require_http_methods(["GET"])
def get_cart(request):
    auth_token, error = get_valid_auth_token(request)
    if error: return error
    return handle_supabase_rpc(
        "get_cart",
        {"auth_token": auth_token},
        "Cart fetched successfully",
        "Cannot fetch cart, try again later"
    )

@csrf_exempt
@require_http_methods(["POST"])
def update_cart_quantity(request):
    body, error = parse_request_body(request)
    if error: return error

    auth_token, error = get_valid_auth_token(request)
    if error: return error

    product_id = body.get("product_id")
    quantity = body.get("quantity")
    if not product_id or quantity is None:
        return JsonResponse({"status": "error", "message": "product_id and quantity are required"}, status=400)

    return handle_supabase_rpc(
        "update_cart_quantity",
        {"auth_token": auth_token, "p_product_id": int(product_id), "p_quantity": int(quantity)},
        "Cart updated successfully",
        "Cannot update cart, try again later",
        raw=True
    )


@csrf_exempt
def get_user_profile_view(request):
    try:
        # Extract AuthToken
        auth_token = request.headers.get("AuthToken")
        if not auth_token:
            return JsonResponse({
                "status": "error",
                "message": "AuthToken header missing"
            }, status=400)

        # Call Supabase RPC
        response = supabase.rpc("get_user_profile", {"auth_token": auth_token}).execute()

        if hasattr(response, "error") and response.error:
            return JsonResponse({
                "status": "error",
                "message": response.error.message
            }, status=500)

        if not response.data:
            return JsonResponse({
                "status": "error",
                "message": "No profile found"
            }, status=404)

        # Return the JSON profile from Postgres
        return JsonResponse(response.data, safe=False)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "Unexpected error",
            "details": str(e)
        }, status=500)