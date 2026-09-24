# Generated manually to fix missing ride_id field on production server
# This migration adds the ride_id field that was missed during --fake migration

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0001_initial'),
        ('support', '0002_alter_supportticket_ride_id'),
    ]

    operations = [
        # Check if the field exists before adding it
        migrations.RunSQL(
            # Forward SQL - Add column if it doesn't exist
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'support_supportticket' 
                    AND column_name = 'ride_id'
                ) THEN
                    ALTER TABLE support_supportticket 
                    ADD COLUMN ride_id uuid NULL;
                    
                    -- Add foreign key constraint
                    ALTER TABLE support_supportticket 
                    ADD CONSTRAINT support_supportticket_ride_id_fkey 
                    FOREIGN KEY (ride_id) REFERENCES rides_rides(id) 
                    ON DELETE SET NULL;
                    
                    -- Add index for performance
                    CREATE INDEX support_supportticket_ride_id_idx 
                    ON support_supportticket(ride_id);
                END IF;
            END $$;
            """,
            # Reverse SQL - Remove column if migration is reversed
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'support_supportticket' 
                    AND column_name = 'ride_id'
                ) THEN
                    ALTER TABLE support_supportticket DROP COLUMN ride_id CASCADE;
                END IF;
            END $$;
            """
        ),
    ]
