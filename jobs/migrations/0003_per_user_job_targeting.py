import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_add_job_preference'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add user FK to JobScrapeLog (nullable — existing rows stay valid)
        migrations.AddField(
            model_name='jobscrapelog',
            name='user',
            field=models.ForeignKey(
                blank=True,
                help_text='Set when this scrape was triggered for a specific user.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='scrape_logs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Create UserJobTarget
        migrations.CreateModel(
            name='UserJobTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('matched_keywords', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('job', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_targets',
                    to='jobs.joblisting',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='job_targets',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'unique_together': {('user', 'job')},
            },
        ),
        migrations.AddIndex(
            model_name='userjobtarget',
            index=models.Index(
                fields=['user', 'created_at'],
                name='jobs_ujt_user_created_idx',
            ),
        ),
    ]
