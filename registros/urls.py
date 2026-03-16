from django.urls import path

from .views import editar_registro, form_teste, listar_registros, upload_planilha

urlpatterns = [
    path("upload/", upload_planilha, name="upload_planilha"),
    path("registros/", listar_registros, name="listar_registros"),
    path("registros/<int:registro_id>/editar/", editar_registro, name="editar_registro"),
    path("form-teste/", form_teste, name="form_teste"),
]
