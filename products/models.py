# products/models.py

from django.db import models
from django import forms
from uuid import uuid4
from django.utils.text import slugify
from mongoengine import Document, StringField, FloatField, IntField, DictField, ListField, EmbeddedDocumentField, EmbeddedDocument, DateTimeField


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class ProductVariant(EmbeddedDocument):
    variant_id = StringField(required=True, unique=True, default=lambda: str(uuid4()))
    color = StringField()        
    price = FloatField(required=True)
    stock = IntField()
    image_url = StringField()
    storage = IntField()

class Product(Document):
    product_id = StringField(unique=True)
    name = StringField(required=True)
    description = StringField(widget=forms.Textarea, required=False)
    slug = StringField(required=True, unique=True)
    category = StringField()
    brand = StringField()
    specifications = DictField(required=False)
    variants = ListField(EmbeddedDocumentField(ProductVariant))

    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.slug:
            self.slug = slugify(self.name)


class Review(Document):
    product_id = StringField(required=True)
    user_id = StringField(required=True)
    rating = IntField(min_value=1, max_value=5)
    review_text = StringField()
    created_at = DateTimeField()

    meta = {'collection':'reviews'}