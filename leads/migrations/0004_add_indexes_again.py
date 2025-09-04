from django.db import migrations
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ('leads', '0003_remove_lead_lead_cat_idx_remove_lead_lead_state_idx_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['category'], name='lead_cat_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['state'], name='lead_state_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['city'], name='lead_city_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['quality_score'], name='lead_score_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=GinIndex(fields=['business_name'], name='lead_biz_trgm', opclasses=['gin_trgm_ops']),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=GinIndex(fields=['domain'], name='lead_domain_trgm', opclasses=['gin_trgm_ops']),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=GinIndex(fields=['email'], name='lead_email_trgm', opclasses=['gin_trgm_ops']),
        ),
    ]

