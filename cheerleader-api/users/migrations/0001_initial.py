import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("email", models.EmailField(unique=True)),
                ("phone_number", models.CharField(blank=True, max_length=50)),
                ("timezone", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER set_users_user_created_at
                AFTER INSERT ON users_user
                WHEN NEW.created_at IS NULL
                BEGIN
                    UPDATE users_user
                    SET created_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
                    WHERE id = NEW.id;
                END;

                CREATE TRIGGER update_users_user_updated_at
                AFTER UPDATE ON users_user
                WHEN NEW.updated_at = OLD.updated_at
                BEGIN
                    UPDATE users_user
                    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
                    WHERE id = NEW.id;
                END;
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS set_users_user_created_at;
                DROP TRIGGER IF EXISTS update_users_user_updated_at;
            """,
        ),
    ]
