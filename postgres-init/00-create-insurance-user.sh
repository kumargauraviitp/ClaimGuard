#!/bin/bash
# Create insurance_user role to prevent auth failure log spam
# from external tools/IDEs that attempt to connect with this username
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'insurance_user') THEN
            CREATE ROLE insurance_user WITH LOGIN PASSWORD 'insurance_user';
            GRANT CONNECT ON DATABASE $POSTGRES_DB TO insurance_user;
            GRANT USAGE ON SCHEMA public TO insurance_user;
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO insurance_user;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO insurance_user;
        END IF;
    END
    \$\$;
EOSQL
