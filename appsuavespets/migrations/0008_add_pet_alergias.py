from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appsuavespets', '0007_add_pet_fecha_nacimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='alergias',
            field=models.TextField(blank=True, null=True),
        ),
    ]

