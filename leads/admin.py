from django.contrib import admin
from .models import State, City, Category, Source, SourceFile, Lead, Tag, LeadTag, SavedView

admin.site.register(State)
admin.site.register(City)
admin.site.register(Category)
admin.site.register(Source)
admin.site.register(SourceFile)
admin.site.register(Lead)
admin.site.register(Tag)
admin.site.register(LeadTag)
admin.site.register(SavedView)

