from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prediction", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="diseaseprediction",
            name="image_analysis",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="diseaseprediction",
            name="uploaded_image",
            field=models.FileField(blank=True, null=True, upload_to="prediction_uploads/"),
        ),
    ]
