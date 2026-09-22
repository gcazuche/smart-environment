from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                ("key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("expires_at", models.FloatField()),
            ],
        )
    ]
