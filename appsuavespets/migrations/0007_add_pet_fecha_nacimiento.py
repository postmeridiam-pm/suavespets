from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appsuavespets', '0006_alter_pet_options_remove_pet_alergias_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='fecha_nacimiento',
            field=models.DateField(blank=True, null=True),
        ),
    ]

