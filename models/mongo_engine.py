import mongoengine as me

class MongoProduct(me.Document):
    name = me.StringField(required=True)
    category = me.StringField()
    brand = me.StringField()
    price = me.FloatField()
    description = me.StringField()
    tags = me.ListField(me.StringField())
    in_stock = me.BooleanField(default=True)

    meta = {'collection': 'products'}
