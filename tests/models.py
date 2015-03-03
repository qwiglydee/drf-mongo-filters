from mongoengine import fields, Document, EmbeddedDocument

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
    f_uuid = fields.UUIDField()

class DeepDoc(Document):
    f_list = fields.ListField(fields.IntField())
    f_map = fields.MapField(fields.IntField())
    f_dict = fields.DictField()

    class EmbDoc(EmbeddedDocument):
        foo = fields.IntField()
        bar = fields.IntField()

    f_emb = fields.EmbeddedDocumentField(EmbDoc)
    f_emblist = fields.EmbeddedDocumentField(EmbDoc)
