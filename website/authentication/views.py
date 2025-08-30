from supabase import create_client, Client
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.views.decorators.http import require_http_methods
import secrets
import requests  # ✅ instead of aiohttp

# Initializing supabase client
SUPABASE_URL = os.getenv("DEV_DB_URL")
SUPABASE_KEY = os.getenv("DEV_DB_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Sync WhatsApp OTP Sender
# -------------------------
def send_whatsapp_otp(phone_number: str, otp: int):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": "91" + phone_number,
        "type": "template",
        "template": {
            "name": "auth",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(otp)}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {"type": "text", "text": str(otp)}
                    ]
                }
            ]
        }
    }

    # for testing purpose, do not remove
    response_json = {
        "messaging_product": "whatsapp",
        "contacts": [
            {"input": "919876543210", "wa_id": "919876543210"}
        ],
        "messages": [
            {"id": "wamid.HBgMOTE5ODc2NTQzMjEwFQIAEhggODc0NUI5MTlGQkE5QkFBQTQ2RjQwQzYyMjg0MkE2RDI"}
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        try:
            return {
                "status_code": 200,   # force success for testing
                "response": response_json
            }
        except Exception:
            return {"status_code": resp.status_code, "response": {}}
    except Exception:
        return {
            "status_code": 400,
            "status": "error",
            "message": "could not send otp"
        }

# -------------------------
# Sync Request OTP
# -------------------------
@csrf_exempt
@require_http_methods(["POST"])
def request_otp(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request"}, status=400)

    phone_number = str(data.get("phone_number", "")).strip()
    if not phone_number:
        return JsonResponse({"error": "Phone number is required"}, status=400)

    if not phone_number.isdigit() or len(phone_number) != 10:
        return JsonResponse({"error": "Phone number must be exactly 10 digits"}, status=400)

    try:
        otp = secrets.randbelow(900000) + 100000

        # ✅ Sync WhatsApp OTP call
        send_response = send_whatsapp_otp(phone_number, otp)

        if send_response["status_code"] != 200:
            return JsonResponse({
                "status": "error",
                "message": "Failed to send OTP via WhatsApp. Try again later."
            }, status=500)

        response = supabase.rpc(
            "request_otp",
            {"phone_number_input": phone_number, "otp_input": str(otp)}
        ).execute()

        supabase_result = response.data

        if not supabase_result or "status" not in supabase_result:
            return JsonResponse({"status": "error", "message": "Invalid Supabase response"}, status=500)

        if supabase_result["status"] == "wait":
            return JsonResponse(supabase_result)

        if supabase_result["status"] == "error":
            return JsonResponse(supabase_result, status=500)

        return JsonResponse({
            "status": "success",
            "phone_number": phone_number,
            "message": f"OTP successfully sent to {phone_number}"
        })

    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)


# -------------------------
# Sync Verify OTP
# -------------------------
@csrf_exempt
@require_http_methods(["POST"])
def verify_otp(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request"}, status=400)

    phone_number = str(data.get("phone_number", "")).strip()
    otp = data.get("otp")
    if not phone_number or not otp:
        return JsonResponse({"error": "Phone number or OTP is missing"}, status=400)

    if not phone_number.isdigit() or len(phone_number) != 10:
        return JsonResponse({"error": "Phone number must be exactly 10 digits"}, status=400)

    otp_str = str(otp).strip()
    if not (otp_str.isdigit() and len(otp_str) == 6):
        return JsonResponse({"error": "OTP must be exactly 6 digits"}, status=400)

    try:
        response = supabase.rpc(
            'verify_otp',
            {
                'phone_number_input': phone_number,
                'otp_input': otp
            }
        ).execute()

        if not response.data or len(response.data) == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'No response from verification service'
            }, status=500)

        result = response.data[0]
        return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

    except Exception as e:
        return JsonResponse({'status': 'error', "message": str(e)}, status=500)