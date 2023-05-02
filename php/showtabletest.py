from ecom.models import cart_total

items = cart_total.objects.all()

for item in items:
    print(item)
