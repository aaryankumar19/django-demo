from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from supabase import create_client
import math
import httpx
from django.views.decorators.csrf import csrf_exempt

# Initialize Supabase client once
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@require_http_methods(["GET"])
def get_products_by_category(request):
    category_id = request.GET.get("category_id")
    category_name = request.GET.get("category_name")
    page = request.GET.get("page", "1")

    if not category_id and not category_name:
        return JsonResponse(
            {"status": "error", "message": "Either category_id or category_name is required"},
            status=400,
        )

    try:
        page_int = int(page)
        if page_int < 1:
            return JsonResponse({"status": "error", "message": "page must be >= 1"}, status=400)
    except ValueError:
        return JsonResponse({"status": "error", "message": "page must be an integer"}, status=400)

    try:
        params = {"p_page": page_int, "p_page_size": 20}
        if category_id:
            params["p_category_id"] = int(category_id)
        if category_name:
            params["p_category_name"] = category_name.strip()

        resp = supabase.rpc("get_products_by_category", params).execute()

        if getattr(resp, "error", None):
            # return JsonResponse({"status": "error", "message": resp.error.message}, status=400)  # DEV
            return JsonResponse({"status": "error", "message": "Could not load products. Try again later."}, status=400)

        products = resp.data or []
        total_count = products[0]["total_count"] if products else 0

        cleaned_products = [
            {k: v for k, v in product.items() if k != "total_count"}
            for product in products
        ]

        return JsonResponse(
            {
                "status": "success",
                "page": page_int,
                "page_size": 20,
                "total_count": total_count,
                "total_pages": (total_count + 19) // 20,
                "products": cleaned_products,
            },
            status=200,
        )

    except Exception as e:
        # return JsonResponse({"status": "error", "message": str(e)}, status=500)  # DEV
        return JsonResponse({"status": "error", "message": "Could not load products. Try again later."}, status=500)


@require_http_methods(["GET"])
def get_products_by_search(request):
    query = request.GET.get("query")
    page = request.GET.get("page", "1")
    min_discount = request.GET.get("min_discount")  # optional

    if not query or len(query.strip()) < 3:
        return JsonResponse(
            {"status": "error", "message": "Search query must be at least 3 characters long"},
            status=400
        )

    try:
        page_int = int(page)
        if page_int < 1:
            return JsonResponse({"status": "error", "message": "page must be >= 1"}, status=400)
    except ValueError:
        return JsonResponse({"status": "error", "message": "page must be an integer"}, status=400)

    try:
        params = {
            "p_search": query.strip().lower(),
            "p_page": page_int,
            "p_page_size": 20,
            "p_min_discount": int(min_discount) if min_discount else None
        }

        resp = supabase.rpc("get_products_by_search", params).execute()

        if getattr(resp, "error", None):
            return JsonResponse({"status": "error", "message": resp.error.message}, status=400)

        products = resp.data or []
        if not products:
            return JsonResponse({
                "status": "success",
                "page": page_int,
                "page_size": 20,
                "total_count": 0,
                "total_pages": 0,
                "products": []
            })

        total_count = products[0].pop("total_count", 0)
        total_pages = math.ceil(total_count / 20)

        return JsonResponse({
            "status": "success",
            "page": page_int,
            "page_size": 20,
            "total_count": total_count,
            "total_pages": total_pages,
            "products": products
        }, status=200)

    except ValueError:
        return JsonResponse({"status": "error", "message": "min_discount must be an integer"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)




@require_http_methods(["GET"])
def get_categories(request):
    try:
        response = supabase.rpc("get_categories").execute()
        return JsonResponse(
            {"status": "success", "data": response.data or []},
            status=200
        )
    except Exception as e:
        # return JsonResponse({"status": "error", "message": str(e)}, status=500)  # DEV
        return JsonResponse(
            {"status": "error", "message": "Could not load categories. Try again later."},
            status=500
        )
    
import requests
from django.http import StreamingHttpResponse, HttpResponse
from .models import Product

DRIVE_BASE_URL = "https://drive.google.com/thumbnail?id="  # or uc?id= for full image
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 800

def stream_drive_image(request):
    file_id = request.GET.get("id")
    uuid_val = request.GET.get("uuid")

    # Width and height from query params, fallback to defaults
    width = request.GET.get("w", DEFAULT_WIDTH)
    height = request.GET.get("h", DEFAULT_HEIGHT)

    # If UUID is provided, look up the corresponding product
    if uuid_val:
        try:
            product = Product.objects.get(image_uuid=uuid_val)
            file_id = product.google_file_id
        except Product.DoesNotExist:
            return HttpResponse("Image not found", status=404)

    if not file_id:
        return HttpResponse("Missing id or uuid param", status=400)

    # Build Drive URL with sz parameter
    url = f"{DRIVE_BASE_URL}{file_id}&sz=w{width}-h{height}"

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=20)
    except requests.RequestException as e:
        return HttpResponse(f"Error fetching image: {e}", status=500)

    if resp.status_code != 200:
        return HttpResponse("Image not found", status=resp.status_code)

    content_type = resp.headers.get("Content-Type", "image/jpeg")
    return StreamingHttpResponse(resp.iter_content(chunk_size=1024), content_type=content_type)


@csrf_exempt
@require_http_methods(["GET"])
def best_deals_view(request):
    try:
        # Extract query params
        category_id = request.GET.get("category_id")
        category_name = request.GET.get("category_name")

        # Convert category_id to int if provided
        if category_id is not None:
            try:
                category_id = int(category_id)
            except ValueError:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid category_id"
                }, status=400)

        # Call Supabase RPC
        response = supabase.rpc(
            "get_home_data",
            {
                "p_category_id": category_id,
                "p_category_name": category_name
            }
        ).execute()

        # Handle Supabase errors
        if hasattr(response, "error") and response.error:
            return JsonResponse({
                "status": "error",
                "message": str(response.error)
            }, status=500)

        # Return response data
        return JsonResponse({
            "status": "success",
            "data": response.data
        }, safe=False, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
    

@csrf_exempt
def get_banners(request):
    try:
        response = supabase.rpc("get_banners").execute()

        if hasattr(response, "error") and response.error:
            return JsonResponse({"status": "error", "message": response.error.message}, status=400)

        return JsonResponse({"status": "success", "data": response.data}, safe=False)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)