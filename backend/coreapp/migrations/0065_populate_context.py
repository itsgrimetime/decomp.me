# Generated manually for issue #1739 - Deduplicate Scratch.context
# Data migration to populate Context table from existing scratch contexts

import hashlib
import logging
from typing import Any

from django.apps.registry import Apps
from django.db import migrations, transaction
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


logger = logging.getLogger(__name__)


def populate_contexts(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Migrate existing scratch.context values to the deduplicated Context table.

    This migration:
    1. Iterates through all scratches with non-empty context
    2. Creates Context records for unique contexts (using SHA256 hash as PK)
    3. Links scratches to their corresponding Context records
    """
    Context = apps.get_model("coreapp", "Context")
    Scratch = apps.get_model("coreapp", "Scratch")

    chunk_size = 1000
    processed = 0
    contexts_created = 0

    # Process scratches in chunks
    qs = Scratch.objects.exclude(context="").only("slug", "context", "context_obj_id")

    def commit_batch(
        contexts_to_create: dict[str, str], updates: list[Any]
    ) -> int:
        created = 0
        if contexts_to_create:
            # bulk_create with ignore_conflicts handles duplicates from concurrent runs
            objs = [
                Context(hash=h, data=data) for h, data in contexts_to_create.items()
            ]
            Context.objects.bulk_create(objs, ignore_conflicts=True)
            created = len(objs)

        if updates:
            with transaction.atomic():
                Scratch.objects.bulk_update(updates, ["context_obj_id"])

        return created

    contexts_to_create: dict[str, str] = {}
    updates: list[Any] = []

    for scratch in qs.iterator(chunk_size=chunk_size):
        processed += 1

        # Skip if already migrated
        if scratch.context_obj_id:
            continue

        # Compute hash and prepare for deduplication
        context_hash = hashlib.sha256(scratch.context.encode()).hexdigest()

        # Track unique contexts to create
        if context_hash not in contexts_to_create:
            # Check if context already exists in DB (from previous batch or migration run)
            if not Context.objects.filter(hash=context_hash).exists():
                contexts_to_create[context_hash] = scratch.context

        # Update scratch to point to context
        scratch.context_obj_id = context_hash
        updates.append(scratch)

        # Commit in chunks
        if processed % chunk_size == 0:
            contexts_created += commit_batch(contexts_to_create, updates)
            contexts_to_create.clear()
            updates.clear()
            logger.info(f"Processed {processed:,} scratches, created {contexts_created:,} contexts...")

    # Final batch
    contexts_created += commit_batch(contexts_to_create, updates)

    logger.info(
        f"Finished: processed {processed:,} scratches, "
        f"created {contexts_created:,} unique contexts"
    )


def reverse_populate(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Reverse migration: clear context_obj references.
    Note: Context records are left in place as they may be referenced by new scratches.
    """
    Scratch = apps.get_model("coreapp", "Scratch")
    Scratch.objects.exclude(context_obj_id=None).update(context_obj_id=None)
    logger.info("Cleared all context_obj references")


class Migration(migrations.Migration):
    dependencies = [
        ("coreapp", "0064_add_context_model"),
    ]

    operations = [
        migrations.RunPython(populate_contexts, reverse_populate),
    ]
