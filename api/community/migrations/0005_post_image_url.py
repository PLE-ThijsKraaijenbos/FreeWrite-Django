from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0004_post_author_post_created_at_post_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image_url',
            field=models.TextField(blank=True, null=True),
        ),
    ]
