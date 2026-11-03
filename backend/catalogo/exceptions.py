from django.db.models.deletion import ProtectedError
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        return Response({'detail': 'Este cadastro está vinculado a trabalhos e não pode ser excluído.'}, status=400)
    if isinstance(exc, IntegrityError):
        return Response({'detail': 'Operação viola a integridade ou unicidade dos dados.'}, status=400)
    return exception_handler(exc, context)
