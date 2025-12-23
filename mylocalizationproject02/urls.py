# # mylocalizationproject/urls.py
# from django.contrib import admin
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from localizationtool.views import localize_tool_view, download_folder, delete_folder, view_and_edit_translations, edit_language_detail

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', localize_tool_view, name='localize_tool_view'),
#     path('download/<str:folder_name>/', download_folder, name='download_folder'),
#     path('delete/<str:folder_name>/', delete_folder, name='delete_folder'),
#     path('edit/<str:folder_name>/', view_and_edit_translations, name='view_and_edit_translations'),
#     path('edit/<str:folder_name>/<str:lang>/', edit_language_detail, name='edit_language_detail'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# mylocalizationproject/urls.py
# mylocalizationproject/urls.py
# from django.contrib import admin
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from localizationtool import views

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.localize_tool_view, name='localize_tool_view'),
#     path('download/<str:folder_name>/', views.download_folder, name='download_folder'),
#     path('delete/<str:folder_name>/', views.delete_folder, name='delete_folder'),
#     # Language selection page
#     path('edit/<str:folder_name>/', views.edit_language_selection, name='edit_language_selection'),
#     # Individual language editor
#     path('edit/<str:folder_name>/<str:lang>/', views.edit_language_detail, name='edit_language_detail'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# from django.contrib import admin
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from localizationtool.views import localize_tool_view, download_folder, delete_folder, view_and_edit_translations

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', localize_tool_view, name='localize_tool_view'),
#     path('download/<str:folder_name>/', download_folder, name='download_folder'),
#     path('delete/<str:folder_name>/', delete_folder, name='delete_folder'),
#     path('edit/<str:folder_name>/', view_and_edit_translations, name='view_and_edit_translations'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# from django.contrib import admin
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from localizationtool.views import (
#     localize_tool_view, download_folder, delete_folder,
#     view_and_edit_translations, edit_language_translations, save_translation
# )

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', localize_tool_view, name='localize_tool_view'),
#     path('download/<str:folder_name>/', download_folder, name='download_folder'),
#     path('delete/<str:folder_name>/', delete_folder, name='delete_folder'),
#     path('edit/<str:folder_name>/', view_and_edit_translations, name='view_and_edit_translations'),
#     path('edit/<str:folder_name>/<str:lang_code>/', edit_language_translations, name='edit_language_translations'),
#     path('save-translation/', save_translation, name='save_translation'),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



# mylocalizationproject02/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from localizationtool.views import (
    localize_tool_view,
    download_folder,
    delete_folder,
    view_and_edit_translations,
    edit_language_version,
    save_translation_version,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', localize_tool_view, name='localize_tool_view'),
    path('download/<str:folder_name>/', download_folder, name='download_folder'),
    path('delete/<str:folder_name>/', delete_folder, name='delete_folder'),
    path('edit/<str:folder_name>/', view_and_edit_translations, name='view_and_edit_translations'),
    path('edit/<str:folder_name>/<str:lang_code>/<int:version>/', 
         edit_language_version, name='edit_language_version'),
    path('save_version/<str:folder_name>/<str:lang_code>/<int:version>/', 
         save_translation_version, name='save_translation_version'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)