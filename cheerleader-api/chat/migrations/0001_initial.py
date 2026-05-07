import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("session_key", models.CharField(max_length=40, unique=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="users.user")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("messages", models.JSONField(default=list)),
                ("meeting_scheduled", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RunSQL(
            sql="""
                CREATE TRIGGER set_chat_chatsession_created_at
                AFTER INSERT ON chat_chatsession
                WHEN NEW.created_at IS NULL
                BEGIN
                    UPDATE chat_chatsession
                    SET created_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
                    WHERE id = NEW.id;
                END;

                CREATE TRIGGER update_chat_chatsession_updated_at
                AFTER UPDATE ON chat_chatsession
                WHEN NEW.updated_at = OLD.updated_at
                BEGIN
                    UPDATE chat_chatsession
                    SET updated_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
                    WHERE id = NEW.id;
                END;
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS set_chat_chatsession_created_at;
                DROP TRIGGER IF EXISTS update_chat_chatsession_updated_at;
            """,
        ),
    ]
