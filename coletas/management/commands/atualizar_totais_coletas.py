from django.core.management.base import BaseCommand
from coletas.models import Coleta


class Command(BaseCommand):
    help = 'Atualiza os totais de todas as coletas'

    def handle(self, *args, **options):
        coletas = Coleta.objects.all()
        total = coletas.count()
        
        self.stdout.write(f'Atualizando totais de {total} coletas...')
        
        for i, coleta in enumerate(coletas, 1):
            coleta.atualizar_totais()
            if i % 10 == 0 or i == total:
                self.stdout.write(f'  Processadas: {i}/{total}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Totais atualizados para {total} coletas!'))
