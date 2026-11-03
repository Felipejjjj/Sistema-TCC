from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


def validar_ano(valor):
    if valor > timezone.localdate().year:
        raise ValidationError('O ano não pode ser maior que o ano corrente.')


class Curso(models.Model):
    nome = models.CharField(max_length=150)
    sigla = models.CharField(max_length=15, unique=True)

    class Meta:
        verbose_name = 'curso'
        verbose_name_plural = 'cursos'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.sigla})'


class Orientador(models.Model):
    nome = models.CharField(max_length=150)
    titulacao = models.CharField('titulação', max_length=100)
    email_institucional = models.EmailField('e-mail institucional', unique=True)

    class Meta:
        verbose_name = 'orientador'
        verbose_name_plural = 'orientadores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Autor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField('e-mail', unique=True)

    class Meta:
        verbose_name = 'autor'
        verbose_name_plural = 'autores'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class PalavraChave(models.Model):
    termo = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = 'palavra-chave'
        verbose_name_plural = 'palavras-chave'
        ordering = ['termo']

    def __str__(self):
        return self.termo


class Trabalho(models.Model):
    class Situacao(models.TextChoices):
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        DEFENDIDO = 'defendido', 'Defendido'
        PUBLICADO = 'publicado', 'Publicado'

    titulo = models.CharField('título', max_length=250)
    resumo = models.TextField()
    ano = models.PositiveIntegerField(validators=[validar_ano])
    data_defesa = models.DateField('data da defesa', null=True, blank=True)
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                               validators=[MinValueValidator(0), MaxValueValidator(10)])
    situacao = models.CharField('situação', max_length=20, choices=Situacao.choices, default=Situacao.EM_ANDAMENTO)
    link_pdf = models.URLField('link do PDF', max_length=500)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name='trabalhos')
    orientador = models.ForeignKey(Orientador, on_delete=models.PROTECT, related_name='trabalhos')
    coorientador = models.ForeignKey(Orientador, on_delete=models.PROTECT, related_name='coorientacoes', null=True, blank=True)
    autores = models.ManyToManyField(Autor, related_name='trabalhos')
    palavras_chave = models.ManyToManyField(PalavraChave, related_name='trabalhos', blank=True)
    cadastrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='trabalhos_cadastrados')

    class Meta:
        verbose_name = 'trabalho'
        verbose_name_plural = 'trabalhos'
        ordering = ['-ano', 'titulo', 'id']
        constraints = [models.UniqueConstraint(fields=['titulo', 'curso', 'ano'], name='titulo_curso_ano_unicos')]

    def clean(self):
        super().clean()
        if self.situacao in [self.Situacao.DEFENDIDO, self.Situacao.PUBLICADO]:
            erros = {}
            if self.nota is None:
                erros['nota'] = 'Trabalho defendido ou publicado precisa de nota.'
            if self.situacao == self.Situacao.PUBLICADO and not self.data_defesa:
                erros['data_defesa'] = 'Para publicar, informe a data da defesa.'
            if erros:
                raise ValidationError(erros)

    def __str__(self):
        return self.titulo
