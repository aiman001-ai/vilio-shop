from .models import Cart, CartItem, Category
from django.db.models import Sum

def cart_count_processor(request):
    count = 0
    if request.user.is_authenticated:
        # 🚀 SPEED FIX: Cart fetch + items loop (2 queries) ki jagah
        # ek hi aggregate query se seedha total quantity nikal rahe hain
        result = CartItem.objects.filter(cart__user=request.user).aggregate(total=Sum('quantity'))
        count = result['total'] or 0
    else:
        # User login nahi hai toh Session se count lo
        session_cart = request.session.get('cart', {})
        count = sum(session_cart.values()) if isinstance(session_cart, dict) else 0
        
    return {'global_cart_count': count}


def menu_categories(request):
    categories = Category.objects.all()
    return {'all_categories': categories}