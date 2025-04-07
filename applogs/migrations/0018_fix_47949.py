# Generated by Django 3.2.25 on 2025-04-07 19:57

from datetime import datetime
from django.db import migrations, models


now = datetime.now()
current_quarter = (now.month-1) // 3 + 1
new_table_name = f"applogs_serverrecord_{now.year}_{current_quarter}"
year = now.year
month = 3 * current_quarter + 1
if month > 12:
    year += 1
    month = 1
last_date = datetime(year, month, 1)


class Migration(migrations.Migration):

    dependencies = [
        ('applogs', '0017_JSONField_fix'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serverrecord',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='дата создания'),
        ),
        # migrations.RunSQL(
        #     sql=[f"ALTER TABLE applogs_serverrecord RENAME TO {new_table_name};"],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
        # migrations.RunSQL(
        #     sql=[f"CREATE TABLE applogs_serverrecord (LIKE {new_table_name} INCLUDING ALL);"],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
        # migrations.RunSQL(
        #     sql=[f"""ALTER TABLE ONLY {new_table_name} ADD CONSTRAINT {new_table_name} CHECK (created_at < '{last_date.strftime("%Y-%m-%d")}');"""],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
        # migrations.RunSQL(
        #     sql=[f"ALTER TABLE ONLY {new_table_name} INHERIT applogs_serverrecord;"],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
        # migrations.RunSQL(
        #     sql=[f"""
        #     CREATE OR REPLACE FUNCTION applogs_serverrecord_insert_trigger()
        #     RETURNS TRIGGER AS $$
        #     DECLARE
        #       current_year TEXT;
        #       current_quarter TEXT;
        #       partition_table_name TEXT;
        #       first_day_of_quarter DATE;
        #       last_day_of_quarter DATE;
        #     BEGIN
        #       current_year := EXTRACT(year FROM NEW.created_at);
        #       current_quarter := EXTRACT(quarter FROM NEW.created_at);
        #       partition_table_name := FORMAT('applogs_serverrecord_%s_%s', current_year, current_quarter);
        #       IF (TO_REGCLASS(partition_table_name::TEXT) ISNULL) THEN
        #         first_day_of_quarter := CAST(DATE_TRUNC('quarter', NEW.created_at) AS date);
        #         last_day_of_quarter := first_day_of_quarter + interval '3 months';
        #         EXECUTE FORMAT('CREATE TABLE %I (LIKE applogs_serverrecord INCLUDING ALL);', partition_table_name);
        #         EXECUTE FORMAT(
        #             'ALTER TABLE ONLY %1$I ADD CONSTRAINT %1$I'
        #             '  CHECK (created_at >= %L AND created_at < %L);'
        #           , partition_table_name, first_day_of_quarter, last_day_of_quarter);
        #         EXECUTE FORMAT('ALTER TABLE ONLY %1$I INHERIT applogs_serverrecord;', partition_table_name);
        #       END IF;
        #       EXECUTE FORMAT('INSERT INTO %I VALUES ($1.*)', partition_table_name) USING NEW;
        #
        #       RETURN NULL;
        #     END;
        #     $$ LANGUAGE plpgsql;
        # """], reverse_sql=migrations.RunSQL.noop,),
        # migrations.RunSQL(
        #     sql=[
        #         "CREATE TRIGGER insert_applogs_serverrecord BEFORE INSERT ON applogs_serverrecord FOR EACH ROW EXECUTE PROCEDURE applogs_serverrecord_insert_trigger();"],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
        # migrations.RunSQL(
        #     sql=[f"DELETE FROM ONLY applogs_serverrecord;"],
        #     reverse_sql=migrations.RunSQL.noop,
        # ),
    ]
