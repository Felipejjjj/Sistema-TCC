from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers
from .models import Autor, Curso, Orientador, PalavraChave, Trabalho


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'nome', 'sigla']


class OrientadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orientador
        fields = ['id', 'nome', 'titulacao', 'email_institucional']


class AutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nome', 'email']


class PalavraChaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalavraChave
        fields = ['id', 'termo']


class TrabalhoPublicoSerializer(serializers.ModelSerializer):
    curso = serializers.StringRelatedField()
    orientador = serializers.StringRelatedField()
    coorientador = serializers.StringRelatedField()
    autores = serializers.StringRelatedField(many=True)
    palavras_chave = serializers.StringRelatedField(many=True)

    class Meta:
        model = Trabalho
        fields = ['id', 'titulo', 'resumo', 'ano', 'data_defesa', 'link_pdf',
                  'curso', 'orientador', 'coorientador', 'autores', 'palavras_chave']


class TrabalhoGestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trabalho
        fields = ['id', 'titulo', 'resumo', 'ano', 'data_defesa', 'nota', 'situacao',
                  'link_pdf', 'curso', 'orientador', 'coorientador', 'autores',
                  'palavras_chave', 'cadastrado_por']
        read_only_fields = ['cadastrado_por']
        validators = []

    def validate_autores(self, autores):
        if not 1 <= len({a.pk for a in autores}) <= 2:
            raise serializers.ValidationError('Informe um ou dois autores distintos.')
        return autores

    def validate(self, attrs):
        instance = self.instance
        if not instance and not attrs.get('autores'):
            raise serializers.ValidationError({'autores': 'Informe um ou dois autores.'})
        # Mescla o estado persistido ao PATCH antes de validar regras cruzadas.
        candidato = Trabalho()
        if instance:
            for field in Trabalho._meta.concrete_fields:
                setattr(candidato, field.attname, getattr(instance, field.attname))
        for name, value in attrs.items():
            if name not in ['autores', 'palavras_chave']:
                setattr(candidato, name, value)
        try:
            candidato.clean()
        except ModelValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        duplicados = Trabalho.objects.filter(titulo=candidato.titulo, curso=candidato.curso, ano=candidato.ano)
        if instance:
            duplicados = duplicados.exclude(pk=instance.pk)
        if duplicados.exists():
            raise serializers.ValidationError({'titulo': 'Já existe um trabalho com este título, curso e ano.'})
        return attrs


class ContagemAnoSerializer(serializers.Serializer):
    ano = serializers.IntegerField()
    total = serializers.IntegerField()


class ContagemCursoSerializer(serializers.Serializer):
    curso = serializers.CharField()
    total = serializers.IntegerField()


class ContagemOrientadorSerializer(serializers.Serializer):
    orientador = serializers.CharField()
    total = serializers.IntegerField()


class EstatisticasSerializer(serializers.Serializer):
    por_ano = ContagemAnoSerializer(many=True)
    por_curso = ContagemCursoSerializer(many=True)
    orientadores = ContagemOrientadorSerializer(many=True)
