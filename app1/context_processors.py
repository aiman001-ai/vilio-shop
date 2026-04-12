# context_processors.py
from .models import Cart, CartItem, Category

def cart_count_processor(request):
    count = 0
    if request.user.is_authenticated:
        # User login hai toh Database se count lo
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            # Saare items ki total quantity count karne ke liye
            count = sum(item.quantity for item in cart.items.all())
    else:
        # User login nahi hai toh Session se count lo
        session_cart = request.session.get('cart', {})
        # session_cart ek dictionary hai {'product_id': quantity}
        count = sum(session_cart.values()) if isinstance(session_cart, dict) else 0
        
    return {'global_cart_count': count}


def menu_categories(request):
    # हम सिर्फ वो कैटेगरीज लेंगे जिनके 'parent' नहीं हैं (Main Categories)
    categories = Category.objects.all()
    return {'all_categories': categories}    