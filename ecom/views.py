import json
from tempfile import template
from threading import Timer

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.contrib.auth.models import Group

from maib_gateway.maib_client import MaibClient
from . import forms, models
from .forms import CustomerUserForm
from .logger import logger
from .models import CartItem


def home_view(request):
    client_ip = request.META.get('REMOTE_ADDR')
    logger.info(f'Client connected from IP: {client_ip}')
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


from django.contrib.auth.models import User


def customer_signup_view(request):
    custom_message = ''
    if request.method == 'POST':
        userForm = forms.CustomerUserForm(request.POST)
        customerForm = forms.CustomerForm(request.POST, request.FILES)

        if userForm.is_valid() and customerForm.is_valid():
            logger.info('dsas 1')
            username = userForm.cleaned_data['username']

            # Check if a user with the same username already exists
            if User.objects.filter(username=username).exists():
                error_message = 'Username is already taken. Please choose a different one.'
                mydict = {'userForm': userForm, 'customerForm': customerForm, 'error_message': error_message}
                return render(request, 'ecom/customersignup.html', context=mydict)

            user = userForm.save(commit=False)
            user.set_password(user.password)
            user.save()

            customer = customerForm.save(commit=False)
            customer.user = user

            if 'profile_pic' in request.FILES:
                customer.profile_pic = request.FILES['profile_pic']
            else:
                customer.profile_pic = 'path/to/def.jpg'

            customer.save()

            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)

            login(request, user)

            return redirect('customer-home')
        custom_message = 'Username is already taken. Please choose a different one.'
    else:
        userForm = forms.CustomerUserForm()
        customerForm = forms.CustomerForm()

    mydict = {'userForm': userForm, 'customerForm': customerForm,
              'custom_message': custom_message}

    return render(request, 'ecom/customersignup.html', context=mydict)


# -----------for checking user customer
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


# TODO✓: Make the sort buttons on main page sort by cattegory or make a category finder type shit.
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

def add_to_cart_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Check if the 'cart' session key exists
    if 'cart' not in request.session:
        request.session['cart'] = {}

    cart = request.session['cart']

    # Increment the quantity for the product in the session cart
    if str(product.pk) in cart:
        cart[str(product.pk)]['quantity'] += 1
    else:
        # Add the product to the session cart
        cart[str(product.pk)] = {
            'product': product.name,
            'quantity': 1,
        }

    # Calculate the total quantity of all products in the cart
    total_quantity = sum(item['quantity'] for item in cart.values())

    request.session['total_quantity'] = total_quantity
    request.session.modified = True  # Save changes to the session

    messages.info(request, product.name + ' added to cart successfully!')

    return redirect('/#')


global total1


# for checkout of cart
def cart_view(request):
    if 'cart' in request.session:
        cart = request.session['cart']
        products = []
        total = 0

        for product_id, item_data in cart.items():
            product = get_object_or_404(Product, pk=int(product_id))
            quantity = item_data['quantity']
            product.quantity = quantity
            product.total = product.price * quantity
            products.append(product)
            total += product.total

        product_count_in_cart = sum(item_data['quantity'] for item_data in cart.values())

        return render(request, 'ecom/cart.html', {
            'products': products,
            'total': total,
            'product_count_in_cart': product_count_in_cart,
        })

    return render(request, 'ecom/cart.html')


def remove_from_cart_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Check if the 'cart' session key exists
    if 'cart' in request.session:
        cart = request.session['cart']

        # Decrement the quantity for the product in the session cart
        if str(product.pk) in cart:
            cart[str(product.pk)]['quantity'] -= 1

            # Remove the product from the session cart if the quantity becomes 0
            if cart[str(product.pk)]['quantity'] <= 0:
                del cart[str(product.pk)]

            # Calculate the total quantity of all products in the cart
            total_quantity = sum(item['quantity'] for item in cart.values())

            request.session['total_quantity'] = total_quantity
            request.session.modified = True  # Save changes to the session

            messages.success(request, product.name + ' quantity reduced by 1 in the cart!')
        else:
            messages.error(request, product.name + ' is not in the cart!')
    else:
        messages.error(request, 'Cart is empty!')

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
    products = Product.objects.all()
    customer = request.user.customer

    # Retrieve the cart items for the customer
    cart_items = CartItem.objects.filter(customer=customer)
    product_count_in_cart = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0

    return render(request, 'ecom/customer_home.html', {
        'products': products,
        'product_count_in_cart': product_count_in_cart
    })


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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product


@login_required(login_url='customerlogin')
@login_required(login_url='customerlogin')
def payment_success_view(request):  # TODO: Look here to payment_succes_view after the payment
    customer = models.Customer.objects.get(user_id=request.user.id)
    products = None
    total_price = 0

    if 'product_ids' in request.COOKIES:
        product_ids = request.COOKIES['product_ids']
        if product_ids != "":
            product_id_in_cart = product_ids.split('|')
            products = models.Product.objects.filter(id__in=product_id_in_cart)
            total_price = products.aggregate(Sum('price'))['price__sum'] or 0

    # Create the order and store it in the database
    orders = []
    for product in products:
        order = models.Orders.objects.create(
            customer=customer,
            product=product,
            status='Pending',
            email=request.COOKIES.get('email'),
            mobile=request.COOKIES.get('mobile'),
            address=request.COOKIES.get('address')
        )
        orders.append(order)

    # Clear the cart cookies
    response = render(request, 'payment_success.html',
                      {'customer': customer, 'orders': orders, 'total_price': total_price})
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


# TODO: make the close day function work , via linux bash script ,or idk.

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
def payment_callback(request):  # TODO: store in database the transaction then go to the payment_succesfull view.
    TRANSACTION_LIFESPAN = 10  # Lifespan of trans_id in minutes
    if request.method == "POST":
        logger.info(f'Request Body: {request.body}')

        if 'error' in request.body.decode('utf-8'):
            logger.error('Error')
            return HttpResponse('Error occured during transaction ask a staff member')

        request_body = request.body.decode('utf-8')

        trans_id = request_body.split('=')[1].split('%')[0]

        logger.info(f'Transaction ID: {trans_id}')  # TODO✓: look get_transaction_id_result must give a return i guess

        transaction_status = MaibClient().get_transaction_result(trans_id)
        transaction_status = transaction_status.status_code

        logger.info(transaction_status)

        if transaction_status == 200:
            logger.info(f'dupa if trebuie sa fie succesful {transaction_status}')
            # Payment success logic
            return HttpResponse('Payment Successful')
        elif transaction_status == '116' or transaction_status == '000':
            # Transaction still pending, check again after additional time
            def check_transaction_status():
                transaction_status = MaibClient().get_transaction_result(trans_id)

                if transaction_status == 200:
                    # Payment success logic
                    return HttpResponse('Payment Successful')

                elif transaction_status in ['FAILED', 'DECLINED']:
                    # Payment failure logic
                    return HttpResponse('Payment Failed')
                else:
                    # Transaction still pending, check again after additional time
                    return HttpResponse('Transaction Pending')

            # Schedule the task to run after 5 minutes
            timer = Timer(5 * 60, check_transaction_status)
            timer.start()
            logger.info(f'dupa if trebuie sa fie pending 2 {transaction_status}')
            return HttpResponse('Transaction Pending')
        else:
            # Payment failure logic
            logger.info(f'dupa if trebuie sa fie failed {transaction_status}')
            return HttpResponse('Payment Failed')


# category Search

def products_by_category(request, category):
    products = Product.objects.filter(category=category)
    context = {
        'products': products,
        'word': category.capitalize(),  # For displaying the selected category as a heading
    }
    return render(request, 'ecom/products.html', context)
