from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_avataritem_useravataritem'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='coins',
            field=models.IntegerField(default=100),
        ),
    ]
