import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from maib_gateway.constants import MAIB_TEST_REDIRECT_URL, MAIB_TEST_BASE_URI, MAIB_TEST_CERT_URL, \
    MAIB_TEST_CERT_KEY_URL
from maib_gateway.maib_client import MaibClient
from . import forms, models
from .logger import logger
from .models import Product, OrderItem
from django.shortcuts import get_object_or_404
from .models import Product, CartItem
from maib_gateway.maib_client import MaibClient


def home_view(request):
    products = models.Product.objects.all()
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'ecom/index.html', {'products': products, 'product_count_in_cart': product_count_in_cart})


# for showing login button for admin(by sumit)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


def customer_signup_view(request):
    userForm = forms.CustomerUserForm()
    customerForm = forms.CustomerForm()
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customer = customerForm.save(commit=False)
            customer.user = user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request, 'ecom/customersignup.html', context=mydict)


# -----------for checking user iscustomer
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()


# ---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')


# ---------------------------------------------------------------------------------
# ------------------------ ADMIN RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    # for cards on dashboard
    customercount = models.Customer.objects.all().count()
    productcount = models.Product.objects.all().count()
    ordercount = models.Orders.objects.all().count()

    # for recent order tables
    orders = models.Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)

    mydict = {
        'customercount': customercount,
        'productcount': productcount,
        'ordercount': ordercount,
        'data': zip(ordered_products, ordered_bys, orders),
    }
    return render(request, 'ecom/admin_dashboard.html', context=mydict)


# admin view customer table
@login_required(login_url='adminlogin')
def view_customer_view(request):
    customers = models.Customer.objects.all()
    return render(request, 'ecom/view_customer.html', {'customers': customers})


# admin delete customer
@login_required(login_url='adminlogin')
def delete_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('view-customer')


@login_required(login_url='adminlogin')
def update_customer_view(request, pk):
    customer = models.Customer.objects.get(id=pk)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('view-customer')
    return render(request, 'ecom/admin_update_customer.html', context=mydict)


# admin view the product
@login_required(login_url='adminlogin')
def admin_products_view(request):
    products = models.Product.objects.all()
    return render(request, 'ecom/admin_products.html', {'products': products})


# admin add product by clicking on floating button
@login_required(login_url='adminlogin')
def admin_add_product_view(request):
    productForm = forms.ProductForm()
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request, 'ecom/admin_add_products.html', {'productForm': productForm})


# TODO: Make the sort buttons on main page sort by cattegory or make a category finder type shit.
@login_required(login_url='adminlogin')
def delete_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')


@login_required(login_url='adminlogin')
def update_product_view(request, pk):
    product = models.Product.objects.get(id=pk)
    productForm = forms.ProductForm(instance=product)
    if request.method == 'POST':
        productForm = forms.ProductForm(request.POST, request.FILES, instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request, 'ecom/admin_update_product.html', {'productForm': productForm})


@login_required(login_url='adminlogin')
def admin_view_booking_view(request):
    orders = models.Orders.objects.all()
    ordered_products = []
    ordered_bys = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_by = models.Customer.objects.all().filter(id=order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
    return render(request, 'ecom/admin_view_booking.html', {'data': zip(ordered_products, ordered_bys, orders)})


@login_required(login_url='adminlogin')
def delete_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')


# for changing status of order (pending,delivered...)
@login_required(login_url='adminlogin')
def update_order_view(request, pk):
    order = models.Orders.objects.get(id=pk)
    orderForm = forms.OrderForm(instance=order)
    if request.method == 'POST':
        orderForm = forms.OrderForm(request.POST, instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking')
    return render(request, 'ecom/update_order.html', {'orderForm': orderForm})


# admin view the feedback
@login_required(login_url='adminlogin')
def view_feedback_view(request):
    feedbacks = models.Feedback.objects.all().order_by('-id')
    return render(request, 'ecom/view_feedback.html', {'feedbacks': feedbacks})


# ---------------------------------------------------------------------------------
# ------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
# ---------------------------------------------------------------------------------
def search_view(request):
    # whatever user write in search box we get in query
    query = request.GET['query']
    products = models.Product.objects.all().filter(name__icontains=query)
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        counter = product_ids.split('|')
        product_count_in_cart = len(set(counter))
    else:
        product_count_in_cart = 0

    # word variable will be shown in html when user click on search button
    word = "Searched Result :"

    if request.user.is_authenticated:
        return render(request, 'ecom/customer_home.html',
                      {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart,
                       'search_text': query})
    return render(request, 'ecom/index.html',
                  {'products': products, 'word': word, 'product_count_in_cart': product_count_in_cart,
                   'search_text': query})


# any one can add product to cart, no need of signin

from django.contrib.auth.models import User
from .models import Customer


def add_to_cart_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    customer = request.user.customer  # TODO: anonymus user cant add to cart handle that

    # get all CartItem objects for this customer and product combination
    cart_items = CartItem.objects.filter(customer=customer, product=product)

    if cart_items.exists():
        # if there are existing CartItem objects, add up their quantities
        quantity = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        # increase the total quantity by 1
        quantity += 1
        # update the quantity of the first CartItem object
        cart_item = cart_items.first()
        cart_item.quantity = quantity
        cart_item.save()
    else:
        # if there are no existing CartItem objects, create a new one
        CartItem.objects.create(customer=customer, product=product)

    messages.info(request, product.name + ' added to cart successfully!')

    return redirect('/#')


global total1


# for checkout of cart
def cart_view(request):
    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    products = []
    total = 0

    for cart_item in cart_items:
        product = cart_item.product
        product.quantity = cart_item.quantity
        product.total = product.price * product.quantity
        products.append(product)
        total += product.total

    product_count_in_cart = len(cart_items)

    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    product_count_in_cart = sum(cart_item.quantity for cart_item in cart_items)

    return render(request, 'ecom/cart.html', {
        'products': products,
        'total': total,
        'product_count_in_cart': product_count_in_cart,
    })


def remove_from_cart_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    customer = request.user.customer

    # get the CartItem object for this customer and product combination
    cart_item = CartItem.objects.filter(customer=customer, product=product).first()

    if cart_item:
        # decrease the quantity of the CartItem by 1
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, product.name + ' quantity reduced by 1 in the cart!')
        else:
            # if the quantity is 1, remove the entire CartItem object
            cart_item.delete()
            messages.success(request, product.name + ' removed from cart successfully!')

    return redirect(request.GET.get('next', 'cart'))


def send_feedback_view(request):
    feedbackForm = forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return render(request, 'ecom/feedback_sent.html')
    return render(request, 'ecom/send_feedback.html', {'feedbackForm': feedbackForm})


# ---------------------------------------------------------------------------------
# ------------------------ CUSTOMER RELATED VIEWS START ------------------------------
# ---------------------------------------------------------------------------------
@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_home_view(request):
    products = models.Product.objects.all()
    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    product_count_in_cart = sum(cart_item.quantity for cart_item in cart_items)
    return render(request, 'ecom/customer_home.html',
                  {'products': products, 'product_count_in_cart': product_count_in_cart})


# shipment address before placing order
@login_required(login_url='customerlogin')
def customer_address_view(request):
    products1 = [item.product for item in CartItem.objects.filter(customer=request.user.customer)]
    product_in_cart = False
    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    products = []
    total = 0

    for cart_item in cart_items:
        product = cart_item.product
        product.quantity = cart_item.quantity
        product.total = product.price * product.quantity
        products.append(product)
        total += product.total

    product_count_in_cart = len(cart_items)

    customer = request.user.customer
    cart_items = CartItem.objects.filter(customer=customer)
    product_count_in_cart = sum(cart_item.quantity for cart_item in cart_items)

    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        logger.info('Post received')
        # if addressForm.is_valid(): # TODO: Fix
        logger.info('Adress is valid')
        # email = addressForm.cleaned_data['Email']
        # mobile = addressForm.cleaned_data['Mobile']
        # address = addressForm.cleaned_data['Address']
        # TODO: Redo (nam idee ce sa fac , parca merge asa ca tat ii drept) imi pare ca nu o sa trimita date la admin
        return handle_view(request)
        logger.info('Adress is not valid')

    return render(request, 'ecom/customer_address.html',
                  {'products1': products1, 'addressForm': addressForm, 'total': total,
                   'product_in_cart': product_in_cart, 'product_count_in_cart': product_count_in_cart})


# here we are just directing to this view...actually we have to check whther `payment` is successful or not
# then only this view should be accessed
@login_required(login_url='customerlogin')
def payment_success_view(request):
    # Here we will place order | after successful payment
    # we will fetch customer  mobile, address, Email
    # we will fetch product id from cookies then respective details from db
    # then we will create order objects and store in db
    # after that we will delete cookies because after order placed...cart should be empty
    customer = models.Customer.objects.get(user_id=request.user.id)
    products = None
    email = None
    mobile = None
    address = None
    total_price = 0
    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.all().filter(id__in=product_id_in_cart)
            # Here we get products list that will be ordered by one customer at a time
            for product in products:
                total_price += product.price

    # Do something with the total_price, e.g. save it as the profit
    # ...

    return render(request, 'payment_success.html',
                  {'customer': customer, 'products': products, 'total_price': total_price})

    # these things can be change so accessing at the time of order...
    if 'email' in request.COOKIES:
        email = request.COOKIES['email']
    if 'mobile' in request.COOKIES:
        mobile = request.COOKIES['mobile']
    if 'address' in request.COOKIES:
        address = request.COOKIES['address']

    # here we are placing number of orders as much there is a products
    # suppose if we have 5 items in cart and we place order....so 5 rows will be created in orders table
    # there will be lot of redundant data in orders table...but its become more complicated if we normalize it
    for product in products:
        models.Orders.objects.get_or_create(customer=customer, product=product, status='Pending', email=email,
                                            mobile=mobile, address=address)

    # after order placed cookies should be deleted
    response = render(request, 'ecom/payment_success.html')
    response.delete_cookie('product_ids')
    response.delete_cookie('email')
    response.delete_cookie('mobile')
    response.delete_cookie('address')
    return response


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_order_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    orders = models.Orders.objects.all().filter(customer_id=customer)
    ordered_products = []
    for order in orders:
        ordered_product = models.Product.objects.all().filter(id=order.product.id)
        ordered_products.append(ordered_product)

    return render(request, 'ecom/my_order.html', {'data': zip(ordered_products, orders)})


# @login_required(login_url='customerlogin')
# @user_passes_test(is_customer)
# def my_order_view2(request):

#     products=models.Product.objects.all()
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         counter=product_ids.split('|')
#         product_count_in_cart=len(set(counter))
#     else:
#         product_count_in_cart=0
#     return render(request,'ecom/my_order.html',{'products':products,'product_count_in_cart':product_count_in_cart})    


# --------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def download_invoice_view(request, orderID, productID):
    order = models.Orders.objects.get(id=orderID)
    product = models.Product.objects.get(id=productID)
    mydict = {
        'orderDate': order.order_date,
        'customerName': request.user,
        'customerEmail': order.email,
        'customerMobile': order.mobile,
        'shipmentAddress': order.address,
        'orderStatus': order.status,

        'productName': product.name,
        'productImage': product.product_image,
        'productPrice': product.price,
        'productDescription': product.description,

    }
    return render_to_pdf('ecom/download_invoice.html', mydict)


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def my_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    return render(request, 'ecom/my_profile.html', {'customer': customer})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def edit_profile_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    user = models.User.objects.get(id=customer.user_id)
    userForm = forms.CustomerUserForm(instance=user)
    customerForm = forms.CustomerForm(request.FILES, instance=customer)
    mydict = {'userForm': userForm, 'customerForm': customerForm}
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST, instance=user)
        customerForm = forms.CustomerForm(request.POST, instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return HttpResponseRedirect('my-profile')
    return render(request, 'ecom/edit_profile.html', context=mydict)


# ---------------------------------------------------------------------------------
# ------------------------ ABOUT US AND CONTACT US VIEWS START --------------------
# ---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request, 'ecom/aboutus.html')


def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name = sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name) + ' || ' + str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER,
                      fail_silently=False)
            return render(request, 'ecom/contactussuccess.html')
    return render(request, 'ecom/contactus.html', {'form': sub})


# _---------------------------------------------------------------------------------_
# _------------------------ PAYMENT VIEWS HANDLING STARTS --------------------------_
# _---------------------------------------------------------------------------------_

def date_range(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Make a request to the API with the given start and end dates
        response = requests.post('https://example.com/api', data={'start_date': start_date, 'end_date': end_date})

        # Check if the request was successful and display the response
        if response.status_code == 200:
            try:
                data = response.json()
                context = {'data': data}
                return render(request, 'results.html', context)
            except json.JSONDecodeError as e:
                error_msg = f"Error: Failed to decode JSON response - {str(e)}"
                context = {'error_msg': error_msg}
                return render(request, 'error.html', context)
        else:
            error_msg = f"Error: {response.status_code} - {response.text}"
            context = {'error_msg': error_msg}
            return render(request, 'error.html', context)

    return render(request, 'date_range.html')


def redirect_to_website(request):
    if request.method == "POST":
        return render('ecom/failed.html')


def handle_view(request):
    if request.method == 'POST':
        logger.info('hanlde started')
        # TODO✓: Make this work based on Order ID instead of hardcode amount
        customer = request.user.customer
        cart_items = CartItem.objects.filter(customer=customer)
        products = []
        total = 0
        description = 'testing '

        for cart_item in cart_items:
            product = cart_item.product
            product.quantity = cart_item.quantity
            product.total = product.price * product.quantity
            products.append(product)
            total += product.total
            description += f"{product.name}, "  # TODO✓: Maybe description based on order

        amount = total
        currency = '978'  # EUR PAHODU
        language = request.COOKIES.get('language',
                                       'en')  # Default to English if no cookie is set TODO✓: Get from cookies ?
        logger.info(
            f"language : {language} | description : {description} | amount : {total} | currency : {currency} |sent|")
        redirect_url = MaibClient().register_sms_transaction(amount,
                                                             currency,
                                                             description,
                                                             language=language)
        logger.info(f'redirect to {redirect_url}')

        return redirect(redirect_url)
    return redirect('failed')  # HANDLE


@csrf_exempt
def payment_callback(request):
    TRANSACTION_LIFESPAN = 10  # Lifespan of trans_id in minutes
    if request.method == "POST":
        logger.info(f'Request Body: {request.body}')

        if 'error' in request.body.decode('utf-8'):
            logger.error('Error')
            return HttpResponse('Error occured during transaction ask a staff member')

        request_body = request.body.decode('utf-8')

        trans_id = request_body.split('=')[1].split('%')[0]

        logger.info(f'Transaction ID: {trans_id}')  # TODO: look get_transaction_id_result must give a return i guess

        transaction_status = MaibClient.get_transaction_result(trans_id)

        logger.info(transaction_status)

        if transaction_status == 'SUCCESS':
            # Payment success logic
            return HttpResponse('Payment Successful')
        elif transaction_status == 'PENDING':
            # Transaction still pending, check again after additional time
            return HttpResponse('Transaction Pending')
        else:
            # Payment failure logic
            return HttpResponse('Payment Failed')

    return HttpResponse('Invalid Request')


# category Search

def products_by_category(request, category):
    products = Product.objects.filter(category=category)
    context = {
        'products': products,
        'word': category.capitalize(),  # For displaying the selected category as a heading
    }
    return render(request, 'ecom/products.html', context)
