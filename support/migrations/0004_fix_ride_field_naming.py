# Generated manually to fix ride field naming issue

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_add_missing_ride_id_field'),
    ]

    operations = [
        # Since the column is already named 'ride_id' in the database,
        # we just need to update Django's understanding of the field name
        # The model field 'ride' will map to database column 'ride_id'
        migrations.RunSQL(
            # Forward - No actual SQL needed, just update Django metadata
            "SELECT 1;",  # Dummy SQL that does nothing
            # Reverse - No actual SQL needed
            "SELECT 1;"   # Dummy SQL that does nothing
        ),
    ]
