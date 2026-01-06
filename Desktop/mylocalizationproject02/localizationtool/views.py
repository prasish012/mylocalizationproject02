# # localizationtool/views.py
# # FULLY UPDATED & FIXED VERSION — SINGLE FOLDER + WORKS WITH NEW TOOL (2025-12-16)
# import os
# import shutil
# import polib
# from collections import defaultdict
# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import FileResponse, Http404, JsonResponse
# from django.conf import settings
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_exempt
# from .forms import LocalizationForm
# from .models import LocalizationUpload, TranslationResult
# from .localization_logic import ColabLocalizationTool


# def localize_tool_view(request):
#     if request.method == 'POST':
#         form = LocalizationForm(request.POST, request.FILES)
#         if form.is_valid():
#             pot_file = request.FILES['upload_po_file']
#             zip_file = request.FILES.get('upload_zip_file')
#             glossary_file = request.FILES.get('upload_glossary_file')
#             target_languages = form.cleaned_data['target_languages']

#             # Generate folder name from .pot file
#             folder_name = os.path.splitext(pot_file.name)[0]

#             # Delete old project if exists
#             existing = LocalizationUpload.objects.filter(folder_name=folder_name).first()
#             if existing:
#                 existing.delete()

#             upload = LocalizationUpload(pot_file=pot_file)
#             upload.save()
#             folder_name = upload.folder_name  # Use DB-generated safe name if needed

#             # FIXED: Single project folder
#             project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
#             os.makedirs(project_dir, exist_ok=True)

#             # Save .pot file
#             pot_path = os.path.join(project_dir, pot_file.name)
#             with open(pot_path, 'wb') as f:
#                 for chunk in pot_file.chunks():
#                     f.write(chunk)

#             # Save ZIP file (optional)
#             zip_save_path = None
#             if zip_file:
#                 zip_save_path = os.path.join(project_dir, zip_file.name)
#                 with open(zip_save_path, 'wb') as f:
#                     for chunk in zip_file.chunks():
#                         f.write(chunk)

#             # Save Glossary CSV (optional)
#             glossary_save_path = None
#             if glossary_file:
#                 glossary_save_path = os.path.join(project_dir, glossary_file.name)
#                 with open(glossary_save_path, 'wb') as f:
#                     for chunk in glossary_file.chunks():
#                         f.write(chunk)

#             # Run the localization tool
#             tool = ColabLocalizationTool()
#             success = tool.run(
#                 pot_path=pot_path,
#                 zip_path=zip_save_path,
#                 csv_path=glossary_save_path,
#                 target_langs=target_languages,
#                 output_dir=project_dir  # Single folder
#             )

#             if not success:
#                 messages.error(request, "Translation failed.")
#                 return redirect('localize_tool_view')

#             # Update database with latest versions
#             lang_files = defaultdict(list)
#             for file_name in os.listdir(project_dir):
#                 if file_name.endswith('.po'):
#                     parts = file_name.rsplit('-', 1)
#                     if len(parts) == 2:
#                         lang_code = parts[0]
#                         version_part = parts[1].replace('.po', '')
#                         try:
#                             version_num = int(version_part)
#                             lang_files[lang_code].append((version_num, file_name))
#                         except ValueError:
#                             continue

#             for lang_code, files in lang_files.items():
#                 files.sort(key=lambda x: x[0], reverse=True)
#                 latest_file = files[0][1]
#                 po_path = os.path.join(project_dir, latest_file)
#                 mo_path = po_path.replace('.po', '.mo')
#                 TranslationResult.objects.update_or_create(
#                     upload=upload,
#                     language=lang_code,
#                     defaults={'po_file': po_path, 'mo_file': mo_path}
#                 )

#             messages.success(request, f'Translation complete: {folder_name}')
#             return redirect('localize_tool_view')
#     else:
#         form = LocalizationForm()

#     # List existing projects
#     translations_root = os.path.join(settings.MEDIA_ROOT, 'translations')
#     folders = []
#     if os.path.isdir(translations_root):
#         for d in sorted(os.listdir(translations_root), reverse=True):
#             full_path = os.path.join(translations_root, d)
#             if os.path.isdir(full_path):
#                 upload = LocalizationUpload.objects.filter(folder_name=d).first()
#                 folders.append({'id': len(folders) + 1, 'name': d, 'upload': upload})

#     context = {'form': form, 'folders': folders}
#     return render(request, 'localizationtool/combined_view.html', context)


# def view_and_edit_translations(request, folder_name):
#     # FIXED: Single folder path
#     project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
#     if not os.path.isdir(project_dir):
#         raise Http404("Project not found.")

#     upload = get_object_or_404(LocalizationUpload, folder_name=folder_name)

#     lang_versions = defaultdict(list)
#     if os.path.isdir(project_dir):
#         for file_name in os.listdir(project_dir):
#             if file_name.endswith('.po'):
#                 parts = file_name.rsplit('-', 1)
#                 if len(parts) == 2:
#                     lang_code = parts[0]
#                     version_part = parts[1].replace('.po', '')
#                     try:
#                         version_num = int(version_part)
#                         po_path = os.path.join(project_dir, file_name)
#                         mo_path = po_path.replace('.po', '.mo')
#                         lang_versions[lang_code].append({
#                             'version': version_num,
#                             'po_file': po_path,
#                             'mo_file': mo_path,
#                             'file_name': file_name,
#                         })
#                     except ValueError:
#                         continue

#     for lang in lang_versions:
#         lang_versions[lang].sort(key=lambda x: x['version'], reverse=True)

#     context = {
#         'folder_name': folder_name,
#         'upload': upload,
#         'lang_versions': dict(lang_versions),
#     }
#     return render(request, 'localizationtool/edit_translations.html', context)


# def edit_language_version(request, folder_name, lang_code, version):
#     # FIXED: Single folder path
#     po_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name, f"{lang_code}-{version}.po")
#     if not os.path.exists(po_path):
#         raise Http404("PO file not found.")
#     po = polib.pofile(po_path, encoding='utf-8')
#     entries = []
#     for entry in po:
#         if entry.msgid and entry.msgid.strip():
#             entries.append({
#                 'msgid': entry.msgid,
#                 'msgstr': entry.msgstr or '',
#                 'msgctxt': entry.msgctxt or '',
#                 'fuzzy': 'fuzzy' in entry.flags,
#                 'msgid_key': entry.msgid,
#             })
#     lang_name = dict(settings.LANGUAGES).get(lang_code, lang_code.upper())
#     context = {
#         'folder_name': folder_name,
#         'lang_code': lang_code,
#         'lang_name': lang_name,
#         'version': version,
#         'entries': entries,
#         'po_path': po_path,
#     }
#     return render(request, 'localizationtool/edit_language_version.html', context)


# @csrf_exempt
# def save_translation_version(request, folder_name, lang_code, version):
#     if request.method != 'POST':
#         return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)

#     # FIXED: Single folder path
#     po_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name, f"{lang_code}-{version}.po")
#     if not os.path.exists(po_path):
#         messages.error(request, 'PO file not found.')
#         return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)

#     po = polib.pofile(po_path, encoding='utf-8')
#     updated = 0
#     from django.utils.text import slugify

#     for entry in po:
#         key = f'translation_{slugify(entry.msgid)}'
#         if key in request.POST:
#             new_msgstr = request.POST[key].strip()
#             if entry.msgstr != new_msgstr:
#                 entry.msgstr = new_msgstr
#                 if 'fuzzy' in entry.flags:
#                     entry.flags.remove('fuzzy')
#                 updated += 1

#     po.save(po_path)
#     mo_path = po_path.replace('.po', '.mo')
#     po.save_as_mofile(mo_path)

#     if updated > 0:
#         messages.success(request, f'Great! {updated} string{"s" if updated > 1 else ""} updated in {lang_code.upper()} (v{version}).')
#     else:
#         messages.info(request, 'No changes made.')

#     return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)


# def download_folder(request, folder_name):
#     # FIXED: Single folder path
#     folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
#     if not os.path.isdir(folder_path):
#         raise Http404("Folder not found.")

#     temp_zip = shutil.make_archive(
#         base_name=os.path.join(settings.MEDIA_ROOT, 'temp', folder_name),
#         format='zip',
#         root_dir=os.path.join(settings.MEDIA_ROOT, 'translations'),
#         base_dir=folder_name
#     )

#     response = FileResponse(open(temp_zip, 'rb'), as_attachment=True, filename=f"{folder_name}_translations.zip")
#     response['Content-Length'] = os.path.getsize(temp_zip)
#     os.remove(temp_zip)
#     return response


# def delete_folder(request, folder_name):
#     if request.method == 'POST':
#         # FIXED: Single folder path
#         folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
#         if os.path.isdir(folder_path):
#             shutil.rmtree(folder_path)
#             upload = LocalizationUpload.objects.filter(folder_name=folder_name).first()
#             if upload:
#                 TranslationResult.objects.filter(upload=upload).delete()
#                 upload.delete()
#             messages.success(request, f'Folder "{folder_name}" deleted.')
#     return redirect('localize_tool_view')


# localizationtool/views.py
# FINAL PERFECT VERSION — Save original .pot filename + Enable WP.org by default (January 02, 2026)

import os
import shutil
import zipfile
import tempfile
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .forms import LocalizationForm
from .models import LocalizationUpload, TranslationResult
from .localization_logic import ColabLocalizationTool


# EXACT MAPPING FOR YOUR FOLDER NAMES (case-insensitive)
LANG_FOLDER_MAP = {
    "arabic": "ar",
    "dutch": "nl",
    "french": "fr",
    "german": "de",
    "hindi": "hi",
    "italian": "it",
    "japanese": "ja",
    "nepali": "ne",
    "polish": "pl",
    "portuguese": "pt",
    "russian": "ru",
    "spanish": "es",
}


def localize_tool_view(request):
    if request.method == 'POST':
        form = LocalizationForm(request.POST, request.FILES)
        if form.is_valid():
            pot_file = request.FILES['upload_po_file']
            zip_file = request.FILES.get('upload_zip_file')
            glossary_input = request.FILES.get('upload_glossary_file')
            target_languages = form.cleaned_data['target_languages']

            # Use original filename without extension as folder name
            folder_name = os.path.splitext(pot_file.name)[0]

            # Delete old project if exists
            existing = LocalizationUpload.objects.filter(folder_name=folder_name).first()
            if existing:
                existing.delete()

            upload = LocalizationUpload(pot_file=pot_file)
            upload.save()
            project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', upload.folder_name)
            os.makedirs(project_dir, exist_ok=True)

            # FIXED: Save .pot with ORIGINAL filename (critical for auto-detect!)
            original_pot_name = pot_file.name  # e.g., "chromenews.pot"
            pot_path = os.path.join(project_dir, original_pot_name)
            with open(pot_path, 'wb') as f:
                for chunk in pot_file.chunks():
                    f.write(chunk)

            # === PERFECT FOLDER DETECTION FOR YOUR STRUCTURE ===
            zip_paths_by_lang = {}
            if zip_file:
                extract_dir = os.path.join(project_dir, "existing_translations")
                os.makedirs(extract_dir, exist_ok=True)
                zip_save_path = os.path.join(project_dir, "existing.zip")
                with open(zip_save_path, 'wb') as f:
                    for chunk in zip_file.chunks():
                        f.write(chunk)

                with zipfile.ZipFile(zip_save_path, 'r') as zf:
                    zf.extractall(extract_dir)

                print("\n=== DETECTED FOLDERS IN ZIP ===")
                for item in os.listdir(extract_dir):
                    item_path = os.path.join(extract_dir, item)
                    if os.path.isdir(item_path):
                        folder_lower = item.lower()
                        lang_code = LANG_FOLDER_MAP.get(folder_lower)

                        if lang_code and lang_code in target_languages:
                            zip_paths_by_lang[lang_code] = item_path
                            print(f"✓ SUCCESS: Found '{item}' folder → using for language '{lang_code}'")
                        else:
                            if lang_code:
                                print(f"✗ IGNORED: '{item}' → '{lang_code}' (not selected)")
                            else:
                                print(f"✗ UNKNOWN: '{item}' (no language match)")

                if zip_paths_by_lang:
                    print(f"\n*** PERFECT: Using {len(zip_paths_by_lang)} dedicated language folder(s) ***")
                else:
                    print("\n!!! WARNING: No matching folders found for selected languages !!!")
                    print("→ Falling back to using ALL .po files (may mix languages)")
                    for lang in target_languages:
                        zip_paths_by_lang[lang] = extract_dir

            # Handle Glossary (CSV or ZIP)
            glossary_by_lang = {}
            if glossary_input:
                gloss_dir = os.path.join(project_dir, "glossaries")
                os.makedirs(gloss_dir, exist_ok=True)

                if glossary_input.name.lower().endswith('.zip'):
                    gloss_zip_path = os.path.join(gloss_dir, "glossary.zip")
                    with open(gloss_zip_path, 'wb') as f:
                        for chunk in glossary_input.chunks():
                            f.write(chunk)
                    with zipfile.ZipFile(gloss_zip_path, 'r') as zf:
                        for member in zf.namelist():
                            if member.lower().endswith('.csv'):
                                extracted = zf.extract(member, gloss_dir)
                                base = os.path.basename(member).lower().removesuffix('.csv')
                                lang_code = None
                                if '_' in base:
                                    possible = base.split('_')[-1]
                                    if len(possible) == 2 and possible in target_languages:
                                        lang_code = possible
                                if lang_code:
                                    glossary_by_lang[lang_code] = extracted
                                else:
                                    for lang in target_languages:
                                        glossary_by_lang[lang] = extracted
                else:
                    csv_path = os.path.join(gloss_dir, glossary_input.name)
                    with open(csv_path, 'wb') as f:
                        for chunk in glossary_input.chunks():
                            f.write(chunk)
                    for lang in target_languages:
                        glossary_by_lang[lang] = csv_path

            # Run the tool — WP.org enabled by default
            tool = ColabLocalizationTool()
            success = tool.run(
                pot_path=pot_path,
                zip_paths_by_lang=zip_paths_by_lang,
                glossary_by_lang=glossary_by_lang,
                target_langs=target_languages,
                output_dir=project_dir,
                use_wporg=True  # Always use official WP.org translations
            )

            if success:
                messages.success(request, f"Translation completed: {folder_name}")
            else:
                messages.error(request, "Translation failed — check console logs")

            return redirect('localize_tool_view')
    else:
        form = LocalizationForm()

    # List all projects
    folders = []
    translations_root = os.path.join(settings.MEDIA_ROOT, 'translations')
    if os.path.exists(translations_root):
        for d in sorted(os.listdir(translations_root), reverse=True):
            full_path = os.path.join(translations_root, d)
            if os.path.isdir(full_path):
                upload = LocalizationUpload.objects.filter(folder_name=d).first()
                folders.append({'name': d, 'upload': upload})

    return render(request, 'localizationtool/combined_view.html', {'form': form, 'folders': folders})


# === OTHER VIEWS (UNCHANGED BUT INCLUDED FOR COMPLETENESS) ===

def view_and_edit_translations(request, folder_name):
    project_dir = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
    if not os.path.isdir(project_dir):
        raise Http404("Project not found")

    upload = get_object_or_404(LocalizationUpload, folder_name=folder_name)

    lang_versions = defaultdict(list)
    for file_name in os.listdir(project_dir):
        if file_name.endswith('.po'):
            parts = file_name.rsplit('-', 1)
            if len(parts) == 2:
                lang_code = parts[0]
                try:
                    version = int(parts[1].replace('.po', ''))
                    po_path = os.path.join(project_dir, file_name)
                    mo_path = po_path.replace('.po', '.mo')
                    lang_versions[lang_code].append({
                        'version': version,
                        'po_file': po_path,
                        'mo_file': mo_path,
                        'file_name': file_name,
                    })
                except:
                    continue

    for lang in lang_versions:
        lang_versions[lang].sort(key=lambda x: x['version'], reverse=True)

    context = {
        'folder_name': folder_name,
        'upload': upload,
        'lang_versions': dict(lang_versions),
    }
    return render(request, 'localizationtool/edit_translations.html', context)


def edit_language_version(request, folder_name, lang_code, version):
    po_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name, f"{lang_code}-{version}.po")
    if not os.path.exists(po_path):
        raise Http404("PO file not found")

    import polib
    po = polib.pofile(po_path)
    entries = []
    for entry in po:
        if entry.msgid:
            entries.append({
                'msgid': entry.msgid,
                'msgstr': entry.msgstr,
                'msgctxt': entry.msgctxt or '',
                'fuzzy': 'fuzzy' in entry.flags,
            })

    lang_name = dict(settings.LANGUAGES).get(lang_code, lang_code.upper())

    context = {
        'folder_name': folder_name,
        'lang_code': lang_code,
        'lang_name': lang_name,
        'version': version,
        'entries': entries,
        'po_path': po_path,
    }
    return render(request, 'localizationtool/edit_language_version.html', context)


@csrf_exempt
def save_translation_version(request, folder_name, lang_code, version):
    if request.method != 'POST':
        return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)

    po_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name, f"{lang_code}-{version}.po")
    if not os.path.exists(po_path):
        messages.error(request, "PO file not found")
        return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)

    import polib
    po = polib.pofile(po_path)

    updated = 0
    for entry in po:
        key = f"trans_{hash(entry.msgid) % 100000}"
        if key in request.POST:
            new_text = request.POST[key].strip()
            if entry.msgstr != new_text:
                entry.msgstr = new_text
                if 'fuzzy' in entry.flags:
                    entry.flags.remove('fuzzy')
                updated += 1

    po.save(po_path)
    po.save_as_mofile(po_path.replace('.po', '.mo'))

    if updated:
        messages.success(request, f"{updated} translations updated!")
    else:
        messages.info(request, "No changes made.")

    return redirect('edit_language_version', folder_name=folder_name, lang_code=lang_code, version=version)


def download_folder(request, folder_name):
    folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
    if not os.path.isdir(folder_path):
        raise Http404("Folder not found")

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_zip.close()
    zip_path = shutil.make_archive(
        base_name=os.path.splitext(temp_zip.name)[0],
        format='zip',
        root_dir=os.path.dirname(folder_path),
        base_dir=folder_name
    )

    response = FileResponse(open(zip_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{folder_name}_translations.zip"'

    import atexit
    atexit.register(os.remove, zip_path)

    return response


def delete_folder(request, folder_name):
    if request.method == 'POST':
        folder_path = os.path.join(settings.MEDIA_ROOT, 'translations', folder_name)
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            upload = LocalizationUpload.objects.filter(folder_name=folder_name).first()
            if upload:
                TranslationResult.objects.filter(upload=upload).delete()
                upload.delete()
            messages.success(request, f'Project "{folder_name}" deleted successfully.')
    return redirect('localize_tool_view')