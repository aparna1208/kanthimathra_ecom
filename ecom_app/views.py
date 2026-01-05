from django.shortcuts import render, get_object_or_404,redirect
from .models import *
from django.utils.text import slugify
from django.contrib import messages

from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib.auth import authenticate,login as auth_login,logout as auth_logout
from django.contrib.auth.models import User

# OTP
import random
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Payment Gateway
import razorpay
from django.http import JsonResponse


#verification email
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# For download pdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .utils import send_invoice_email

User = get_user_model()



def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    subject = "Your OTP Verification Code"
    message = f"""
    Hello,

    Your OTP code is: {otp}

    This OTP is valid for 5 minutes.
    Do not share it with anyone.

    – Kanthi Mantra
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("web:register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("web:register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_active=True,
        )

        otp_code = generate_otp()

        OTP.objects.create(
            user=user,
            otp=otp_code
        )

        send_otp_email(email, otp_code)

        request.session["otp_user_id"] = user.id

        messages.success(request, "OTP sent to your registered email.")
        return redirect("web:otp")

    return render(request, "web/register.html")


# OTP Verification

def otp_verify(request):
    user_id = request.session.get("otp_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please register again.")
        return redirect("web:register")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        otp_input = request.POST.get("otp")

        try:
            otp_obj = OTP.objects.filter(
                user=user,
                otp=otp_input,
                is_verified=False
            ).latest("created_at")
        except OTP.DoesNotExist:
            messages.error(request, "Invalid OTP.")
            return redirect("web:otp")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired.")
            return redirect("web:otp")

        otp_obj.is_verified = True
        otp_obj.save()

        user.is_verified = True
        user.save()

        del request.session["otp_user_id"]

        messages.success(request, "OTP verified successfully!")
        return redirect("web:login")

    return render(request, "web/otp.html", {"user": user})




def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect("web:login")

        # Authenticate (email is used as username)
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)  

            #  ADMIN LOGIN
            if user.is_superuser or user.is_staff:
                return redirect("/adminpanel/")

            #  NORMAL USER LOGIN
            return redirect("web:index")

        else:
            messages.error(request, "Invalid email or password.")
            return redirect("web:login")

    return render(request, "web/login.html")


def forgotPassword(request):
    if request.method =="POST":
        email = request.POST['email']
        if User.objects.filter(email = email).exists():
            user = User.objects.get(email__exact= email)

            # RESET PASSWORD EMAIL
            current_site = get_current_site(request)
            mail_subject = 'Reset your Password'

            message = render_to_string('web/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request,"Password reset email has been sent to your email address.")
            return redirect('web:login')

        else:
            messages.error(request, "Accounts doesnot exist!")
            return redirect('web:forgotPassword')

    return render(request,'web/forgot_password.html')

def resetpassword_validate(request,uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request,'Plaese reset your password')
        return redirect("web:resetPassword")
    else:
        messages.error(request,"This link has been expired!")
        return redirect("web:login")
    
def resetPassword(request):
    if request.method == "POST":
        password = request.POST['newpassword']
        confirm_password = request.POST['confirmpassword']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()

            messages.success(request, "Password reset successful!")
            return redirect('web:login')
        else:
            messages.error(request, "Passwords do not match!")
            return redirect("web:resetPassword")

    return render(request,'web/password_reset_confirm.html')

    
@login_required(login_url="web:login")
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("web:login")

def index(request):
    products = Product.objects.prefetch_related("images")[:8]  # show latest 8

    return render(request, "web/index.html", {
        "products": products
    })

@login_required(login_url="web:login")
def account(request):
    user = request.user

    context = {
        "user": user,
        
    }
    return render(request, "web/account.html", context)


def aboutus(request):
    return render(request, 'web/about.html')


def gallery(request):
    return render(request, 'web/gallery.html')


def blog(request):
    return render(request, 'web/blog.html')


def blog_single(request):
    return render(request, 'web/blog-single.html')


def contactus(request):
    return render(request, 'web/contact.html')

@login_required
def orders(request):
    return render(request, "web/orders.html")

@login_required
def address(request):
    return render(request, "web/address.html")

@login_required
def account_settings(request):
    return render(request, "web/settings.html")

@login_required
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")  # get from form
        product = get_object_or_404(Product, id=product_id)

        cart = request.session.get("cart", {})

        if product_id in cart:
            cart[product_id]["qty"] += 1
        else:
            cart[product_id] = {
                "product_id": product.id,
                "name": product.name,
                "price": float(product.price),
                "qty": 1,
                "image": product.thumbnail.url if product.thumbnail else ""
            }

        request.session["cart"] = cart
        request.session.modified = True

        # optional: show a success message
        # messages.success(request, f"{product.name} added to cart!")

        # redirect to cart page
        return redirect("web:cart_view")

    # if GET request or invalid, redirect to home or product page
    return redirect("web:check_out")



@login_required(login_url="web:login")
def check_out(request):
    session_cart = request.session.get("cart", {})

    if not session_cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("web:cart_view")

    cart_items = []
    subtotal = Decimal("0.00")

    for product_id, item in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)
            qty = item["qty"]
            price = Decimal(product.price)
            item_total = price * qty

            subtotal += item_total

            cart_items.append({
                "product": product,
                "qty": qty,
                "price": price,
                "total": item_total,
                "image": item.get("image", "")
            })

        except Product.DoesNotExist:
            continue

    delivery_charge = Decimal("0.00")
    total = subtotal + delivery_charge

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "total": total,
    }

    return render(request, "web/checkout.html", context)



# @login_required
# def place_order(request):
#     if request.method == "POST":
#         session_cart = request.session.get("cart")

#         if not session_cart:
#             messages.error(request, "Your cart is empty.")
#             return redirect("web:cart_view")

#         subtotal = Decimal("0.00")

#         order = Order.objects.create(
#             user=request.user,
#             total_amount=0,
#             payment_status="PAID",
#             payment_method="MANUAL"
#         )

#         for product_id, item in session_cart.items():
#             product = Product.objects.get(id=int(product_id))
#             qty = item["qty"]
#             price = Decimal(product.price)

#             subtotal += price * qty

#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=qty,
#                 price=price
#             )

#         order.total_amount = subtotal
#         order.save()

#         # ✅ CLEAR CART PROPERLY
#         if "cart" in request.session:
#             del request.session["cart"]
#         request.session.modified = True

#         return redirect("web:invoice", order_id=order.id)

#     return redirect("web:payment")



@login_required
def payment(request):
    session_cart = request.session.get("cart", {})

    if not session_cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("web:cart_view")

    cart_items = []
    subtotal = Decimal("0.00")

    for product_id, item in session_cart.items():
        product = Product.objects.get(id=product_id)
        qty = item["qty"]
        price = Decimal(product.price)
        total = price * qty

        subtotal += total

        cart_items.append({
            "product": product,
            "qty": qty,
            "price": price,
            "total": total
        })

    delivery_charge = Decimal("0.00")
    grand_total = subtotal + delivery_charge

    return render(request, "web/payment.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "delivery_charge": delivery_charge,
        "grand_total": grand_total
    })


@login_required
def create_razorpay_order(request):
    session_cart = request.session.get("cart", {})

    if not session_cart:
        return JsonResponse({"error": "Cart empty"}, status=400)

    subtotal = Decimal("0.00")
    for product_id, item in session_cart.items():
        price = Decimal(item["price"])
        qty = item["qty"]
        subtotal += price * qty

    amount_paise = int(subtotal * 100)  # Razorpay uses paise

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    return JsonResponse({
        "order_id": razorpay_order["id"],
        "amount": amount_paise,
        "key": settings.RAZORPAY_KEY_ID
    })




# @csrf_exempt
# @login_required
# def verify_razorpay_payment(request):
#     if request.method == "POST":
#         client = razorpay.Client(
#             auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
#         )

#         try:
#             params = {
#                 "razorpay_order_id": request.POST.get("razorpay_order_id"),
#                 "razorpay_payment_id": request.POST.get("razorpay_payment_id"),
#                 "razorpay_signature": request.POST.get("razorpay_signature"),
#             }

#             client.utility.verify_payment_signature(params)

#             #  Payment success - create order
#             # place_order_from_session(request)

#             return JsonResponse({"status": "success"})

#         except razorpay.errors.SignatureVerificationError:
#             return JsonResponse({"status": "failed"}, status=400)



# @csrf_exempt
# def payment_success(request):
#     data = json.loads(request.body)
#     payment_id = data.get("razorpay_payment_id")

#     cart_items = request.user.cart_items.all()  # adjust if needed
#     total = sum(item.qty * item.product.price for item in cart_items)

#     order = Order.objects.create(
#         user=request.user,
#         payment_id=payment_id,
#         total_amount=total
#     )

#     for item in cart_items:
#         OrderItem.objects.create(
#             order=order,
#             product_name=item.product.name,
#             quantity=item.qty,
#             price=item.product.price
#         )

#     cart_items.delete()
#     send_invoice_email(order)

#     return JsonResponse({"order_id": order.id})


# @csrf_exempt
# @login_required
# def payment_success(request):
#     try:
#         data = json.loads(request.body)
#         payment_id = data.get("razorpay_payment_id")

#         session_cart = request.session.get("cart", {})
#         if not session_cart:
#             return JsonResponse({"error": "Cart empty"}, status=400)

#         subtotal = Decimal("0.00")

#         order = Order.objects.create(
#             user=request.user,
#             payment_id=payment_id,
#             payment_method="RAZORPAY",
#             status="paid",
#             total_amount=0
#         )

#         for product_id, item in session_cart.items():
#             product = Product.objects.get(id=product_id)
#             price = Decimal(item["price"])
#             qty = item["qty"]

#             subtotal += price * qty

#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 quantity=qty,
#                 price=price
#             )

#         order.total_amount = subtotal
#         order.save()

#         # Clear cart
#         request.session["cart"] = {}
#         request.session.modified = True

#         send_invoice_email(order)

#         return JsonResponse({"order_id": order.id})

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from decimal import Decimal
import json

@csrf_exempt
@login_required
def payment_success(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)
    payment_id = data.get("razorpay_payment_id")

    session_cart = request.session.get("cart", {})

    if not session_cart:
        return JsonResponse({"error": "Cart is empty"}, status=400)

    with transaction.atomic():

        total = Decimal("0.00")

        # Create Order
        order = Order.objects.create(
            user=request.user,
            payment_id=payment_id,
            payment_method="RAZORPAY",
            status="paid",
            total_amount=0
        )

        # Create OrderItems + Reduce Product Quantity
        for product_id, item in session_cart.items():
            product = Product.objects.select_for_update().get(id=product_id)

            qty = int(item["qty"])
            price = Decimal(product.price)

            if product.quantity < qty:
                return JsonResponse({
                    "error": f"Insufficient stock for {product.name}"
                }, status=400)

            # 🔻 Reduce stock
            product.quantity -= qty
            product.save()

            total += price * qty

            OrderItem.objects.create(
                order=order,
                product=product,
                price=price,
                quantity=qty
            )

        #  Update total
        order.total_amount = total
        order.save()

        # CLEAR SESSION CART
        del request.session["cart"]
        request.session.modified = True

    return JsonResponse({
        "message": "Payment successful",
        "order_id": order.id
    })


@login_required
def invoice_view(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        payment_status="PAID"
    )

    return render(request, "web/invoice.html", {
        "order": order
    })


@login_required
def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{order.id}.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>KANTHI MANTRA</b>", styles["Title"]))
    elements.append(Paragraph(f"Invoice ID: {order.id}", styles["Normal"]))
    elements.append(Paragraph(f"Payment ID: {order.payment_id}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {order.created_at.strftime('%d-%m-%Y %I:%M %p')}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    data = [["Product", "Qty", "Price", "Total"]]

    for item in order.orderitem_set.all():
        data.append([
            item.product.name,
            item.quantity,
            f"₹{item.price}",
            f"₹{item.price * item.quantity}"
        ])

    data.append(["", "", "Grand Total", f"₹{order.total_amount}"])

    table = Table(data)
    elements.append(table)

    doc.build(elements)
    return response



@login_required
def order_success(request):
    order = Order.objects.filter(
        user=request.user,
        payment_status="PAID",
        is_completed=False
    ).last()

    if not order:
        return redirect("home")

    with transaction.atomic():
        for item in order.items.all():
            product = item.product

            # 1️⃣ Reduce product stock
            if product.quantity >= item.quantity:
                product.quantity -= item.quantity
                product.save()
            else:
                raise Exception("Insufficient stock")

        # 2️⃣ Remove cart items
        CartItem.objects.filter(
            cart__user=request.user
        ).delete()

        # 3️⃣ Mark order completed
        order.is_completed = True
        order.save()

    return render(request, "web/order_success.html", {"order": order})

# @login_required
# def invoice(request, order_id):
#     order = Order.objects.get(id=order_id, user=request.user)
#     items = order.items.all()

#     return render(request, "web/invoice.html", {
#         "order": order,
#         "items": items
#     })



@login_required
def cart_view(request):
    session_cart = request.session.get("cart", {})  # {"1": {"qty": 2}}

    cart = {}
    total_amount = Decimal("0.00")

    for product_id, item in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)

            qty = item.get("qty", 1)
            price = Decimal(product.price)
            sub_total = price * qty
            total_amount += sub_total

            # Get first related image (if exists)
            first_image = product.images.first()
            image_url = first_image.image.url if first_image else ""

            cart[product_id] = {
                "id": product.id,
                "name": product.name,
                "price": price,
                "qty": qty,
                "sub_total": sub_total,
                "image": image_url,
            }

        except Product.DoesNotExist:
            continue

    context = {
        "cart": cart,
        "total_amount": total_amount,
    }

    return render(request, "web/cart.html", context)

@login_required
def remove_from_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")  # get product ID from form
        cart = request.session.get("cart", {})

        if product_id in cart:
            del cart[product_id]  # remove item from cart
            request.session["cart"] = cart
            request.session.modified = True  # mark session as modified

        # redirect back to cart page
        return redirect("web:cart_view")

    # fallback if GET request, redirect to cart page
    return redirect("web:cart_view")

@login_required
def update_cart_qty(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        action = request.POST.get("action")
        cart = request.session.get("cart", {})

        if product_id in cart:
            if action == "increase":
                cart[product_id]["qty"] += 1
            elif action == "decrease":
                cart[product_id]["qty"] -= 1
                # Optional: Remove item if qty goes to 0
                if cart[product_id]["qty"] <= 0:
                    del cart[product_id]

            request.session["cart"] = cart
            request.session.modified = True

        return redirect("web:cart_view")  # refresh cart page

    return redirect("web:cart_view")

def shop(request):
    products = Product.objects.prefetch_related("images").all()

    # CATEGORY FILTER
    category_ids = request.GET.getlist('category')
    if category_ids:
        products = products.filter(category_id__in=category_ids)

    # AVAILABILITY FILTER (FIXED)
    availability = request.GET.getlist('availability')
    if availability:
        products = products.filter(stock_status__in=availability)

    # PRICE FILTER
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # SORTING
    sort = request.GET.get('sort')
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'alpha':
        products = products.order_by('name')
    else:
        products = products.order_by('-id')

    # PAGINATION
    paginator = Paginator(products, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'web/shop.html', {
        'products': page_obj,
        'categories': Category.objects.all(),
        'selected_categories': category_ids,
        'selected_availability': availability,
        'min_price': min_price,
        'max_price': max_price,
    })



def product_details_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    images = ProductImage.objects.filter(product=product)

    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(
            user=request.user, product=product
        ).exists()

    context = {
        'product': product,
        'images': images,
        'is_wishlisted': is_wishlisted,
    }
    return render(request, 'web/product_details.html', context)

def toggle_wishlist(request):
    product_id = request.POST.get('product_id')
    product = Product.objects.get(id=product_id)

    obj, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        obj.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})

def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'web/wishlist.html', {'items': items})










# --------- ADMIN PANEL-------------




# admin panel views
def admin_dashboard(request):
    return render(request, 'adminpanel/index.html')

# Category--------------------------------

# Category List
def category_list(request):
    categories = Category.objects.all().order_by("-created_at")
    return render(request, "adminpanel/category.html", {
        "categories": categories
    })

# Delete Category
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    return redirect("web:category_list")

# Edit category
def add_category(request, id=None):
    category = None

    if id:
        category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        name = request.POST.get("name")
        image = request.FILES.get("image")

        base_slug = slugify(name)
        slug = base_slug
        counter = 1

        # Ensure unique slug
        while Category.objects.filter(slug=slug).exclude(id=getattr(category, "id", None)).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        if category:
            category.name = name
            category.slug = slug
            if image:
                category.image = image
            category.save()
        else:
            Category.objects.create(
                name=name,
                slug=slug,
                image=image
            )

        return redirect("web:category_list")

    return render(request, "adminpanel/add_category.html")

# Edit Category
def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        name = request.POST.get('name')
        slug = slugify(name)

        if Category.objects.filter(slug=slug).exclude(id=category.id).exists():
            return render(request, 'adminpanel/add_category.html', {
                'category': category,
                'error': 'Category with this name already exists'
            })

        category.name = name
        category.slug = slug

        if request.FILES.get('image'):
            category.image = request.FILES.get('image')

        category.save()

        return redirect('web:category_list')

    return render(request, 'adminpanel/add_category.html', {
        'category': category
    })



# Product -------------------------

# Add Product
# ========================= ADD PRODUCT =========================
@require_http_methods(["GET", "POST"])
def add_product(request):
    categories = Category.objects.all()

    if request.method == "POST":
        try:
            name = request.POST.get('name')
            category_id = request.POST.get('category')
            brand = request.POST.get('brand')
            description = request.POST.get('description')
            price = request.POST.get('price')
            state = request.POST.get('state')
            quantity = request.POST.get('quantity')
            thumbnail = request.FILES.get('thumbnail')
            video = request.FILES.get('product_video')
            images = request.FILES.getlist('product_images')

            if state == "Out Of Stock":
                quantity = 0
            else:
                quantity = int(quantity) if quantity else 0

            if not all([name, category_id, brand, price, thumbnail, state]):
                messages.error(request, "All required fields must be filled.")
                return redirect('web:add_product')

            category = Category.objects.get(id=category_id)

            product = Product.objects.create(
                name=name,
                category=category,
                brand=brand,
                description=description,
                price=price,
                stock_status=state,
                quantity=quantity,
                thumbnail=thumbnail,
                video=video
            )

            for image in images:
                ProductImage.objects.create(product=product, image=image)

            messages.success(request, "Product added successfully!")
            return redirect('web:product_list')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('web:add_product')

    return render(request, 'adminpanel/add_product.html', {
        'categories': categories
    })

# Product List
def product_list(request):
    products = Product.objects.prefetch_related("images").all()
    return render(request, 'adminpanel/products.html', {
        'products': products
    })


# Edit Product
# ========================= EDIT PRODUCT =========================
@require_http_methods(["GET", "POST"])
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)
    categories = Category.objects.all()

    if request.method == "POST":
        try:
            product.name = request.POST.get("name")
            product.description = request.POST.get("description")
            product.price = request.POST.get("price")
            product.brand = request.POST.get("brand")
            product.category_id = request.POST.get("category")
            product.stock_status = request.POST.get("state")

            quantity = request.POST.get("quantity")
            if product.stock_status == "Out Of Stock":
                product.quantity = 0
            else:
                product.quantity = int(quantity) if quantity else 0

            if request.FILES.get("thumbnail"):
                product.thumbnail = request.FILES["thumbnail"]

            if request.FILES.get("product_video"):
                product.video = request.FILES["product_video"]

            # Handle deletion of existing images
            delete_image_ids = request.POST.get('delete_images', '')
            if delete_image_ids:
                ids = [int(x) for x in delete_image_ids.split(',') if x.isdigit()]
                ProductImage.objects.filter(id__in=ids, product=product).delete()

            # Handle new images
            new_images = request.FILES.getlist("product_images")
            for img in new_images:
                ProductImage.objects.create(product=product, image=img)

            product.save()
            messages.success(request, "Product updated successfully!")
            return redirect('web:product_list')

        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")

    return render(request, "adminpanel/add_product.html", {
        "product": product,
        "categories": categories
    })


# Delete Product
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('web:product_list')




def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'adminpanel/product_detail.html', {'product': product})






