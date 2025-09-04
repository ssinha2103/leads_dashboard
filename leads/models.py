from __future__ import annotations
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib.postgres.indexes import GinIndex


class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    name = models.CharField(max_length=150)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        unique_together = ('name', 'state')

    def __str__(self) -> str:
        return f"{self.name}, {self.state.name}"


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self) -> str:
        return self.name


class Source(models.Model):
    TYPE_CHOICES = (
        ('local_folder', 'Local Folder'),
        ('google_drive', 'Google Drive'),
    )
    name = models.CharField(max_length=150, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='local_folder')
    root_path = models.TextField(blank=True, null=True)
    drive_folder_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class SourceFile(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='files')
    path = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    hash = models.CharField(max_length=64)
    size = models.BigIntegerField(default=0)
    modified_time = models.DateTimeField(null=True, blank=True)
    row_count = models.IntegerField(default=0)
    last_ingested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('source', 'path')

    def __str__(self) -> str:
        return self.path


class Lead(models.Model):
    business_name = models.CharField(max_length=255)
    website = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads', db_index=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads', db_index=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads', db_index=True)
    domain = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    quality_score = models.IntegerField(default=0, db_index=True)
    extra = models.JSONField(default=dict, blank=True)
    source_file = models.ForeignKey(SourceFile, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'), name='uniq_lead_email_lower',
                condition=Q(email__isnull=False)
            ),
            models.UniqueConstraint(
                Lower('domain'), 'city', 'state',
                name='uniq_lead_domain_city_state',
                condition=Q(domain__isnull=False)
            ),
        ]
        indexes = [
            models.Index(fields=['category'], name='lead_cat_idx'),
            models.Index(fields=['state'], name='lead_state_idx'),
            models.Index(fields=['city'], name='lead_city_idx'),
            models.Index(fields=['quality_score'], name='lead_score_idx'),
            GinIndex(fields=['business_name'], name='lead_biz_trgm', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['domain'], name='lead_domain_trgm', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['email'], name='lead_email_trgm', opclasses=['gin_trgm_ops']),
        ]

    def __str__(self) -> str:
        return self.business_name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class LeadTag(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('lead', 'tag')


class SavedView(models.Model):
    name = models.CharField(max_length=150)
    filters = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
