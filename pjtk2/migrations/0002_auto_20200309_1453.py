# Generated by Django 2.2.11 on 2020-03-09 18:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pjtk2', '0001_squashed_0027_auto_20190113_1819'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='lake',
            field=models.ManyToManyField(to='common.Lake'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='role',
            field=models.CharField(choices=[('manager', 'Manager'), ('dba', 'DBA'), ('employee', 'Employee')], db_index=True, default='Employee', max_length=30),
        ),
        migrations.AlterField(
            model_name='message',
            name='level',
            field=models.CharField(choices=[('info', 'Info'), ('actionrequired', 'Action Required')], default='info', max_length=30),
        ),
        migrations.AlterField(
            model_name='milestone',
            name='category',
            field=models.CharField(choices=[('Custom', 'custom'), ('Suggested', 'suggested'), ('Core', 'core')], default='Custom', max_length=30),
        ),
        migrations.AlterField(
            model_name='project',
            name='lake',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='common.Lake'),
        ),
        migrations.DeleteModel(
            name='Lake',
        ),
    ]
