

#!/bin/sh

until nc -z -v -w30 "$POSTGRES_HOST" 5432
do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

echo "PostgreSQL is ready!"
