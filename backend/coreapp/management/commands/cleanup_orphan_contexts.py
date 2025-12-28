"""
Management command to clean up orphaned Context records.

Orphaned contexts are those that are no longer referenced by any Scratch.
This can happen when scratches are deleted or when context_obj is updated.

Usage:
    python manage.py cleanup_orphan_contexts
    python manage.py cleanup_orphan_contexts --dry-run
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from coreapp.models.scratch import Context


class Command(BaseCommand):
    help = "Delete Context records that are not referenced by any Scratch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find contexts with no scratches referencing them
        orphans = Context.objects.annotate(
            scratch_count=Count("scratch")
        ).filter(scratch_count=0)

        count = orphans.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orphaned contexts found."))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Would delete {count:,} orphaned context(s). "
                    "Run without --dry-run to delete."
                )
            )
            # Show first few hashes for verification
            sample = orphans[:10]
            for ctx in sample:
                self.stdout.write(f"  - {ctx.hash[:16]}...")
            if count > 10:
                self.stdout.write(f"  ... and {count - 10} more")
        else:
            orphans.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count:,} orphaned context(s).")
            )
