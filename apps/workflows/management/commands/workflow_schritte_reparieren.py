"""
Management Command: Repariert Workflows ohne Schritt-Instanzen.

Workflows, die manuell über das Admin-Interface erstellt wurden,
haben möglicherweise keine WorkflowSchrittInstanzen. Dieser Command
erstellt die fehlenden Instanzen basierend auf dem WorkflowTyp.
"""
from django.core.management.base import BaseCommand
from apps.workflows.models import WorkflowInstanz, WorkflowSchrittInstanz


class Command(BaseCommand):
    help = 'Repariert Workflows ohne Schritt-Instanzen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeigt nur was gemacht werden würde, ohne Änderungen vorzunehmen'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - Keine Änderungen werden gespeichert')
            )

        # Finde alle Workflows ohne Schritt-Instanzen
        workflows_ohne_schritte = []
        alle_workflows = WorkflowInstanz.objects.all()

        for workflow in alle_workflows:
            schritt_count = workflow.schritt_instanzen.count()
            if schritt_count == 0:
                workflows_ohne_schritte.append(workflow)

        if not workflows_ohne_schritte:
            self.stdout.write(
                self.style.SUCCESS('Alle Workflows haben Schritt-Instanzen. Nichts zu reparieren.')
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f'Gefunden: {len(workflows_ohne_schritte)} Workflow(s) ohne Schritt-Instanzen'
            )
        )

        # Repariere jeden Workflow
        repariert_count = 0
        for workflow in workflows_ohne_schritte:
            workflow_typ = workflow.workflow_typ
            schritte_im_typ = workflow_typ.schritte.all().order_by('reihenfolge')

            if not schritte_im_typ.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Workflow "{workflow.name}" (ID: {workflow.id}): '
                        f'WorkflowTyp "{workflow_typ.name}" hat keine Schritte definiert!'
                    )
                )
                continue

            self.stdout.write(
                f'  Repariere: {workflow.name} (ID: {workflow.id})'
            )
            self.stdout.write(
                f'    → Erstelle {schritte_im_typ.count()} Schritt-Instanzen...'
            )

            if not dry_run:
                # Erstelle WorkflowSchrittInstanzen
                for schritt in schritte_im_typ:
                    WorkflowSchrittInstanz.objects.create(
                        workflow_instanz=workflow,
                        workflow_schritt=schritt,
                        status='pending'
                    )

            repariert_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: {repariert_count} Workflow(s) würden repariert werden.'
                )
            )
            self.stdout.write('Führen Sie den Command ohne --dry-run aus, um die Änderungen zu speichern.')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Erfolgreich {repariert_count} Workflow(s) repariert!'
                )
            )
