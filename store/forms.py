import json
from django import forms
from store.models import Product  # MongoEngine model
from mongoengine import StringField
import slugify

class ProductForm(forms.Form):
    product_id = forms.CharField(max_length=15)
    name = forms.CharField(max_length=100)
    # price = forms.DecimalField(max_digits=10, decimal_places=2)
    # slug = StringField(required=True, unique=True)
    category = forms.CharField(max_length=100)
    brand = forms.CharField(max_length=20)
    # stock = forms.IntegerField(max_value=100)
    description = forms.CharField(widget=forms.Textarea)
    image_url = forms.URLField()
    specifications = forms.JSONField(
        widget=forms.Textarea,
        help_text="Enter specifications as JSON. E.g., {\"RAM\": \"8GB\", \"Color\": \"Black\"}"
    )
