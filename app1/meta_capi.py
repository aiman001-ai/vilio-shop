import hashlib
import time
import json
import logging
import threading
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

META_PIXEL_ID = getattr(settings, 'META_PIXEL_ID', '27446769361621989')
META_GRAPH_API_VERSION = "v19.0"

def _hash_val(val):
    if not val:
        return None
    val_str = str(val).strip().lower()
    return hashlib.sha256(val_str.encode('utf-8')).hexdigest()

def _clean_phone(phone_str):
    if not phone_str:
        return None
    digits = ''.join(filter(str.isdigit, str(phone_str)))
    if len(digits) == 10:
        digits = "91" + digits  # Default India country code
    elif digits.startswith("0") and len(digits) == 11:
        digits = "91" + digits[1:]
    return digits

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def _post_event_to_meta(payload, access_token):
    try:
        url = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}/{META_PIXEL_ID}/events"
        params = {"access_token": access_token}
        response = requests.post(url, params=params, json=payload, timeout=5)
        res_json = response.json()
        if response.status_code == 200:
            logger.info(f"Meta CAPI Success: {res_json}")
        else:
            logger.warning(f"Meta CAPI Warning ({response.status_code}): {res_json}")
    except Exception as e:
        logger.error(f"Meta CAPI Exception: {str(e)}")

def send_meta_capi_purchase(request, order):
    """
    Sends a Server-Side Purchase event to Meta Conversions API (CAPI).
    Deduplicated with browser pixel via event_id: 'order_{order.id}'.
    Runs asynchronously in a background thread to prevent slowing down checkout.
    """
    access_token = getattr(settings, 'META_ACCESS_TOKEN', '')
    if not access_token:
        # Access token is optional until user adds it to .env / settings
        logger.info(f"Meta CAPI skipped: META_ACCESS_TOKEN not set in settings/env.")
        return

    try:
        # Parse customer info
        full_name = ""
        first_name = ""
        last_name = ""
        phone = ""
        email = ""
        city = ""
        state = ""
        pincode = ""

        if hasattr(order, 'user') and order.user:
            first_name = order.user.first_name or ""
            last_name = order.user.last_name or ""
            email = order.user.email or ""

        # Check address string or Address object
        address_parts = str(order.address).split(',')
        if len(address_parts) >= 2:
            full_name = address_parts[0].strip()
            phone = address_parts[1].strip()

        if not first_name and full_name:
            name_split = full_name.split()
            first_name = name_split[0]
            if len(name_split) > 1:
                last_name = " ".join(name_split[1:])

        # Extract pincode, city, state if possible
        if "-" in str(order.address):
            try:
                pin_part = str(order.address).split("-")[-1].strip().split()[0]
                if pin_part.isdigit() and len(pin_part) == 6:
                    pincode = pin_part
            except Exception:
                pass

        clean_ph = _clean_phone(phone)
        ph_hash = _hash_val(clean_ph) if clean_ph else None
        em_hash = _hash_val(email) if email and "@" in email else None
        fn_hash = _hash_val(first_name) if first_name else None
        ln_hash = _hash_val(last_name) if last_name else None
        ct_hash = _hash_val(city) if city else None
        st_hash = _hash_val(state) if state else None
        zp_hash = _hash_val(pincode) if pincode else None
        country_hash = _hash_val("in")

        user_data = {
            "client_ip_address": get_client_ip(request),
            "client_user_agent": request.META.get('HTTP_USER_AGENT', ''),
            "country": [country_hash] if country_hash else [],
        }

        if ph_hash: user_data["ph"] = [ph_hash]
        if em_hash: user_data["em"] = [em_hash]
        if fn_hash: user_data["fn"] = [fn_hash]
        if ln_hash: user_data["ln"] = [ln_hash]
        if ct_hash: user_data["ct"] = [ct_hash]
        if st_hash: user_data["st"] = [st_hash]
        if zp_hash: user_data["zp"] = [zp_hash]

        # fbp and fbc cookies
        fbp = request.COOKIES.get('_fbp')
        if fbp:
            user_data["fbp"] = fbp

        fbc = request.COOKIES.get('_fbc')
        if not fbc:
            fbclid = request.session.get('fbclid') or request.GET.get('fbclid')
            if fbclid:
                fbc = f"fb.1.{int(time.time())}.{fbclid}"
        if fbc:
            user_data["fbc"] = fbc

        # Contents
        contents = []
        for item in order.items.all():
            contents.append({
                "id": str(item.product.id),
                "quantity": int(item.quantity),
                "item_price": float(item.price)
            })

        event_data = {
            "event_name": "Purchase",
            "event_time": int(time.time()),
            "event_id": f"order_{order.id}",
            "event_source_url": request.build_absolute_uri(),
            "action_source": "website",
            "user_data": user_data,
            "custom_data": {
                "currency": "INR",
                "value": float(order.total_amount),
                "content_type": "product",
                "contents": contents,
                "num_items": len(contents),
                "order_id": str(order.id)
            }
        }

        payload = {"data": [event_data]}

        # Execute in non-blocking thread
        t = threading.Thread(target=_post_event_to_meta, args=(payload, access_token), daemon=True)
        t.start()
    except Exception as e:
        logger.error(f"Error preparing Meta CAPI event: {str(e)}")
