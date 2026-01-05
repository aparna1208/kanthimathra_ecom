from django.urls import path,reverse_lazy
from . import views
from django.contrib.auth import views as auth_views


app_name = 'web' 


urlpatterns = [
    # web
    path('', views.index, name='index'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('shop/', views.shop, name='shop'),
    path('gallery/', views.gallery, name='gallery'),
    path('blog/', views.blog, name='blog'),
    path('contactus/', views.contactus, name='contactus'),
    path('blog-single/', views.blog_single, name='blog_single'),
    # path("cart/", views.cart, name="cart"),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path("cart/", views.cart_view, name="cart_view"),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-qty/', views.update_cart_qty, name='update_cart_qty'),
    path('checkout/',views.check_out,name='check_out'),
    # path('place-order/', views.place_order, name='place_order'),
    path('payment/', views.payment, name='payment'),
    path("razorpay/create/", views.create_razorpay_order, name="razorpay_create"),
    # path("razorpay/verify/", views.verify_razorpay_payment, name="razorpay_verify"),
    # path('payment-success/', views.payment_success, name='payment_success'),
    # path('order-success/', views.order_success, name='order_success'),.
    path('api/payment-success/', views.payment_success, name='payment_success'),
    path('api/order-success/', views.order_success, name='order_success'),
    path("invoice/<int:order_id>/", views.invoice_view, name="invoice"),
    path("invoice/pdf/<int:order_id>/", views.invoice_pdf, name="invoice_pdf"),


    path("wishlist/", views.wishlist_view, name="wishlist"),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path("account/", views.account, name="account"),
    path("orders/", views.orders, name="orders"), 
    path("address/", views.address, name="address"),
    path("settings/", views.account_settings, name="settings"),
    path('product-detail/<slug:slug>/', views.product_details_view, name='product_details_view'),

    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # path('forgot-password/', views.forgot_password, name='forgot_password'),

    # path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgot-password/', views.forgotPassword, name='forgot_password'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/',views.resetPassword,name='resetPassword'),

    path("register/",views.register, name="register"),
    path("otp/", views.otp_verify, name="otp"),



    # ----------- admin panel ---------


    # path('adminpanel/', views.adminpanel, name='adminpanel'),
    path('adminpanel/', views.admin_dashboard, name='admin_dashboard'),
    # path('adminpanel/products/', views.all_products, name='all_products'),
    path('adminpanel/add-new-product/', views.add_product, name='add_product'),
    path('adminpanel/products/', views.product_list, name='product_list'),
    path('adminpanel/products/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('adminpanel/products/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # Category
    path('adminpanel/category/', views.category_list, name='category_list'),
    path('adminpanel/category/add/', views.add_category, name='add_category'),
    path("adminpanel/category/delete/<int:id>/",views.delete_category,name="delete_category"),
    path("adminpanel/category/edit/<int:id>/", views.edit_category, name="edit_category"),




]