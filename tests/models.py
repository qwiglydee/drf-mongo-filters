from mongoengine import fields, Document, EmbeddedDocument

class RefDoc(Document):
    pass

class SimpleDoc(Document):
    f_str = fields.StringField()
    f_url = fields.URLField()
    f_eml = fields.EmailField()
    f_int = fields.IntField()
    f_lng = fields.LongField()
    f_flt = fields.FloatField()
    f_dec = fields.DecimalField()
    f_bool = fields.BooleanField()
    f_dt = fields.DateTimeField()
    f_oid = fields.ObjectIdField()
    f_ref = fields.ReferenceField(RefDoc)
    f_uuid = fields.UUIDField()
    f_rng_beg = fields.IntField()
    f_rng_end = fields.IntField()

class EmbDoc(EmbeddedDocument):
    foo = fields.StringField()
    bar = fields.StringField()

class DeepDoc(Document):
    f_list = fields.ListField(fields.IntField())
    f_map = fields.MapField(fields.IntField())
    f_dict = fields.DictField()

    f_emb = fields.EmbeddedDocumentField(EmbDoc)
    f_emblist = fields.ListField(fields.EmbeddedDocumentField(EmbDoc))

class GeoDoc(Document):
    location = fields.PointField()
