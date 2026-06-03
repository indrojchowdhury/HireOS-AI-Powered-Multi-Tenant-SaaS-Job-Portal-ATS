from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0006_add_interview_application_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='ai_score',
            field=models.IntegerField(blank=True, null=True, help_text='Matching score out of 100 calculated by Gemini LLM.'),
        ),
    ]
