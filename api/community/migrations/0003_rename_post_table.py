from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_postlike'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='post',
            table='post',
        ),
    ]
