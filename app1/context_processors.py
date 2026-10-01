from .models import Cart, CartItem, Category
from django.db.models import Sum

def cart_count_processor(request):
    count = 0
    if request.user.is_authenticated:
        if request.session.get('guest_cart') or request.session.get('cart') or request.session.get('buy_now_product'):
            try:
                from .views import merge_cart
                merge_cart(request)
            except Exception:
                pass
        result = CartItem.objects.filter(cart__user=request.user).aggregate(total=Sum('quantity'))
        count = result['total'] or 0
    else:
        # User not logged in - check guest_cart
        guest_cart = request.session.get('guest_cart', [])
        if isinstance(guest_cart, list):
            count = sum(item.get('quantity', 1) for item in guest_cart if isinstance(item, dict))
        elif isinstance(guest_cart, dict):
            count = sum(guest_cart.values())
        else:
            count = 0
        
    return {'global_cart_count': count}


def menu_categories(request):
    categories = Category.objects.prefetch_related('subcategories__product_types').all()
    return {'all_categories': categories}