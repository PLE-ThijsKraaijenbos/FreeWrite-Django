from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_userprofile_coins'),
    ]

    operations = [
        migrations.AddField(
            model_name='avataritem',
            name='price',
            field=models.IntegerField(default=0),
        ),
    ]
