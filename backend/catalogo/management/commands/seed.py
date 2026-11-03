from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token
from catalogo.models import Autor, Curso, Orientador, PalavraChave, Trabalho


class Command(BaseCommand):
    help = 'Carrega dados fictícios de demonstração; pode ser executado novamente.'

    @transaction.atomic
    def handle(self, *args, **options):
        usuarios = []
        for i in (1, 2):
            user, _ = get_user_model().objects.get_or_create(username=f'coordenacao{i}')
            user.is_staff = True
            user.set_password(f'CatalogoTCC@{i}2026')
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
            usuarios.append(user)
            self.stdout.write(f'{user.username}: {token.key}')
        cursos = [Curso.objects.get_or_create(sigla=s, defaults={'nome': n})[0] for n, s in [
            ('Sistemas para Internet', 'TSI'), ('Ciência da Computação', 'CC'),
            ('Engenharia Elétrica', 'EE'), ('Administração', 'ADM')]]
        nomes = ['Ana Beatriz Lima', 'Bruno Henrique Costa', 'Carla Mendes Souza', 'Diego Alves Santos',
                 'Elisa Rodrigues Melo', 'Fernando Pereira Silva', 'Gabriela Nunes Rocha', 'Hugo Martins Freitas']
        orientadores = [Orientador.objects.get_or_create(email_institucional=f'docente{i}@exemplo.ifpb.edu.br',
                        defaults={'nome': nome, 'titulacao': 'Doutorado'})[0] for i, nome in enumerate(nomes)]
        termos = ['Django', 'Acessibilidade', 'Educação', 'Inteligência artificial', 'Sustentabilidade',
                  'Saúde', 'Segurança', 'Dados abertos', 'Redes', 'Gestão', 'IoT', 'Usabilidade',
                  'Software livre', 'Inclusão', 'Aprendizado de máquina']
        palavras = [PalavraChave.objects.get_or_create(termo=t)[0] for t in termos]
        temas = ['Plataforma acessível para bibliotecas', 'Monitoramento de energia em salas de aula',
                 'Análise de dados da evasão estudantil', 'Catálogo digital de projetos acadêmicos',
                 'Sistema de agendamento de laboratórios', 'Aplicativo de apoio à saúde estudantil',
                 'Segurança de redes em ambientes educacionais', 'Gestão sustentável de resíduos',
                 'Painel de indicadores de extensão', 'Tecnologia assistiva para leitura']
        for i in range(36):
            ano = timezone.localdate().year - i % 6
            situacao = 'publicado' if i < 30 else ('defendido' if i < 33 else 'em_andamento')
            trabalho, _ = Trabalho.objects.update_or_create(titulo=f'{temas[i % 10]}: estudo {i + 1:02}',
                curso=cursos[i % 4], ano=ano, defaults={
                'resumo': f'Este trabalho investiga {temas[i % 10].lower()} no contexto do IFPB. '
                          'A pesquisa combina revisão bibliográfica, levantamento de requisitos e avaliação '
                          'de um protótipo com usuários. Os resultados discutem viabilidade, limitações e '
                          'contribuições para a comunidade acadêmica.',
                'data_defesa': date(ano, 3, 15) if situacao != 'em_andamento' else None,
                'nota': Decimal('8.50') if situacao != 'em_andamento' else None,
                'situacao': situacao, 'link_pdf': f'https://example.org/tcc/trabalho-{i+1}.pdf',
                'orientador': orientadores[i % 8],
                'coorientador': orientadores[(i+1) % 8] if i % 5 == 0 else None,
                'cadastrado_por': usuarios[i % 2]})
            autores = []
            for j in range(2 if i % 6 == 0 else 1):
                autor, _ = Autor.objects.get_or_create(email=f'estudante{i+1}-{j+1}@example.org',
                            defaults={'nome': f'{["Lucas", "Mariana", "Pedro", "Juliana"][i%4]} {i+1} {"Silva" if j == 0 else "Oliveira"}'})
                autores.append(autor)
            trabalho.autores.set(autores)
            trabalho.palavras_chave.set([palavras[i % 15], palavras[(i+3) % 15]])
        self.stdout.write(self.style.SUCCESS('36 trabalhos carregados: 30 publicados e 6 não publicados.'))
