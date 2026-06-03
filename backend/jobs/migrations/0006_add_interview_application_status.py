from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_application_offer_letter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('REVIEWING', 'Reviewing'),
                    ('SHORTLISTED', 'Shortlisted'),
                    ('INTERVIEW', 'Interview'),
                    ('REJECTED', 'Rejected'),
                ],
                default='PENDING',
                max_length=20,
            ),
        ),
    ]
