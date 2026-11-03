from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from catalogo import views

publico = DefaultRouter()
publico.register('trabalhos', views.TrabalhoPublicoViewSet, basename='publico-trabalho')
gestao = DefaultRouter()
gestao.register('trabalhos', views.TrabalhoGestaoViewSet)
gestao.register('cursos', views.CursoViewSet)
gestao.register('orientadores', views.OrientadorViewSet)
gestao.register('autores', views.AutorViewSet)
gestao.register('palavras-chave', views.PalavraChaveViewSet)
urlpatterns = [
    path('api/publico/v1/estatisticas/', views.EstatisticasView.as_view()),
    path('api/publico/v1/', include(publico.urls)),
    path('api/gestao/token/', views.TokenView.as_view()),
    path('api/gestao/', include(gestao.urls)),
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny], authentication_classes=[]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny], authentication_classes=[]), name='docs'),
]
