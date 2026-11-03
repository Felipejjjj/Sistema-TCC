from django.db.models import Count, F
from django_filters.rest_framework import FilterSet, CharFilter
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.authtoken.views import ObtainAuthToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from .models import Autor, Curso, Orientador, PalavraChave, Trabalho
from .serializers import (AutorSerializer, CursoSerializer, OrientadorSerializer,
                          PalavraChaveSerializer, TrabalhoPublicoSerializer,
                          TrabalhoGestaoSerializer, EstatisticasSerializer)


class TrabalhoFilter(FilterSet):
    palavra_chave = CharFilter(field_name='palavras_chave__termo', lookup_expr='iexact')

    class Meta:
        model = Trabalho
        fields = ['ano', 'curso', 'palavra_chave']


def acervo_publico():
    return Trabalho.objects.filter(situacao=Trabalho.Situacao.PUBLICADO)


def com_relacoes(qs):
    return qs.select_related('curso', 'orientador', 'coorientador').prefetch_related('autores', 'palavras_chave')


@extend_schema_view(
    list=extend_schema(description='Lista somente trabalhos publicados. Sem nota, e-mails ou usuário cadastrador. Busca em título, resumo, autores e orientador; filtros combináveis por ano, ID de curso e termo exato de palavra-chave. Paginação de seis itens. Ordene com ordering=ano, -ano, titulo ou -titulo. Limite compartilhado de 20 requisições/minuto por IP; exceder retorna 429 e Retry-After.'),
    retrieve=extend_schema(description='Resumo integral e palavras-chave de um trabalho publicado. IDs de trabalhos em andamento ou defendidos retornam 404, assim como IDs inexistentes.'),
)
class TrabalhoPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrabalhoPublicoSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]
    queryset = com_relacoes(acervo_publico())
    filterset_class = TrabalhoFilter
    search_fields = ['titulo', 'resumo', 'autores__nome', 'orientador__nome']
    ordering_fields = ['ano', 'titulo']
    ordering = ['-ano', 'titulo', 'id']

    def get_queryset(self):
        return super().get_queryset().distinct()


class EstatisticasView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    @extend_schema(responses=EstatisticasSerializer, description='Contagens de trabalhos publicados por ano e curso e ranking de orientadores. Agregação SQL em tempo de consulta; trabalhos não publicados ficam de fora. Mesmo limite de 20 chamadas/minuto por IP do catálogo.')
    def get(self, request):
        qs = acervo_publico()
        return Response({
            'por_ano': list(qs.values('ano').annotate(total=Count('id')).order_by('-ano')),
            'por_curso': list(qs.values(curso_nome=F('curso__nome')).annotate(total=Count('id')).order_by('curso_nome').values(curso=F('curso_nome'), total=F('total'))),
            'orientadores': list(qs.values(orientador_nome=F('orientador__nome')).annotate(total=Count('id')).order_by('-total', 'orientador_nome').values(orientador=F('orientador_nome'), total=F('total'))),
        })


class TrabalhoGestaoViewSet(viewsets.ModelViewSet):
    queryset = com_relacoes(Trabalho.objects.all())
    serializer_class = TrabalhoGestaoSerializer

    def perform_create(self, serializer):
        serializer.save(cadastrado_por=self.request.user)


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer


class OrientadorViewSet(viewsets.ModelViewSet):
    queryset = Orientador.objects.all()
    serializer_class = OrientadorSerializer


class AutorViewSet(viewsets.ModelViewSet):
    queryset = Autor.objects.all()
    serializer_class = AutorSerializer


class PalavraChaveViewSet(viewsets.ModelViewSet):
    queryset = PalavraChave.objects.all()
    serializer_class = PalavraChaveSerializer


class TokenView(ObtainAuthToken):
    throttle_classes = [AnonRateThrottle]

    @extend_schema(responses={200: OpenApiResponse(description='Objeto JSON com a chave token.')}, description='Recebe username e password e devolve token. Use Authorization: Token <chave> na gestão.')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
