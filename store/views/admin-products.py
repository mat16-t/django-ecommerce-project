from django.contrib.admin.views.decorators import staff_member_required
from products.models import Product
from django.shortcuts import redirect, render

@staff_member_required
def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category_id")
        price = float(request.POST.get("price"))
        specs_input = request.POST.get("specs")  # "color:red,size:M"

        # Convert specs string to dict
        specs = {}
        if specs_input:
            pairs = specs_input.split(",")
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(":")
                    specs[key.strip()] = value.strip()

        # Save to MongoDB
        Product(
            name=name,
            category_id=category_id,
            price=price,
            specs=specs
        ).save()

        return redirect("admin_product_list")  # define this name in urls

    return render(request, "admin/product_form.html")