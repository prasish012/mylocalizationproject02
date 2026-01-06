
# # # localizationtool/localization_logic.py
# # # FINAL VERSION — Priority: WP.org → Glossary → ZIP PO → JSON → Google (Dec 30, 2025)

# # import polib
# # import csv
# # import os
# # import re
# # import json
# # import requests
# # from typing import Dict, Tuple, List, Optional
# # from django.conf import settings
# # from charset_normalizer import from_path
# # from deep_translator import GoogleTranslator as _GoogleTranslator


# # class _Translator:
# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         raise NotImplementedError


# # class GoogleTranslatorEngine(_Translator):
# #     _SEP = "|||INVISIBLE|||"

# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         if not texts:
# #             return []
# #         joined = self._SEP.join(texts)
# #         try:
# #             translator = _GoogleTranslator(source='auto', target=target_lang)
# #             out = translator.translate(joined)
# #             if isinstance(out, list):
# #                 return [str(x) for x in out]
# #             parts = str(out).split(self._SEP)
# #             if len(parts) == len(texts):
# #                 return parts
# #         except:
# #             pass
# #         return [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]


# # class ColabLocalizationTool:
# #     def __init__(self):
# #         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
# #         os.makedirs(self.json_dir, exist_ok=True)

# #         self.NON_TRANSLATABLE_ENTITIES = {
# #             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
# #             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
# #             "&trade;", "&TRADE;", "TRADEMARK",
# #             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
# #         }

# #         # Protected strings — never translate these (theme names, common buttons)
# #         self.PROTECTED_STRINGS = {
# #             "ChromeNews", "ReviewNews", "AF themes", "Get Started", "Upgrade to Pro", "Upgrade Now",
# #             "Starter Sites", "Header Builder", "Footer Builder", "Dashboard", "Customize"
# #         }

# #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# #         self.icu_placeholder_regex = re.compile(r"\{[^}]*\}")
# #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# #         self.translation_rules = {
# #             "%s min read": {
# #                 "ja": "%s分で読めます", "it": "%s min di lettura", "nl": "%s min gelezen",
# #                 "pl": "%s min czytania", "pt": "%s min de leitura", "de": "%s Min. Lesezeit",
# #                 "ar": "قراءة في %s دقيقة", "fr": "%s min de lecture", "ru": "%s мин. чтения",
# #                 "en": "%s mins read", "sw": "%s dakika kusoma", "da": "%s min læsning",
# #                 "fi": "%s min lukeminen", "is": "%s mín lestur", "no": "%s min lesing",
# #                 "sv": "%s min läsning", "zh-CH": "%s 分钟阅读",
# #             }
# #         }

# #         self._counts = {
# #             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
# #             "reused_zip": 0, "reused_json": 0, "translated_google": 0, "protected": 0
# #         }
# #         self._cache: Dict[Tuple[str, str], str] = {}
# #         self.translator_engine = GoogleTranslatorEngine()

# #         self.plural_forms_header = {
# #             "en": "nplurals=2; plural=(n != 1);",
# #             "es": "nplurals=2; plural=(n != 1);",
# #             "de": "nplurals=2; plural=(n != 1);",
# #             "fr": "nplurals=2; plural=(n > 1);",
# #             "pt": "nplurals=2; plural=(n != 1);",
# #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# #             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
# #             "ar": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
# #             "nl": "nplurals=2; plural=(n != 1);",
# #             "it": "nplurals=2; plural=(n != 1);",
# #             "ja": "nplurals=1; plural=0;",
# #             "hi": "nplurals=2; plural=(n != 1);",
# #             "ne": "nplurals=2; plural=(n != 1);",
# #         }

# #     def _display_status(self, message):
# #         print(f"\n--- STATUS: {message} ---")

# #     def _display_error(self, message):
# #         print(f"\n--- ERROR: {message} ---")

# #     def _contains_protected_entity(self, text: str) -> bool:
# #         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

# #     def _collect_placeholders(self, text: str) -> List[str]:
# #         ph = self.printf_placeholder_regex.findall(text) + self.icu_placeholder_regex.findall(text) + self.quoted_printf_regex.findall(text)
# #         return list(dict.fromkeys(ph))

# #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# #         try:
# #             return set(self._collect_placeholders(original)) == set(self._collect_placeholders(translated))
# #         except:
# #             return False

# #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# #         placeholders = self._collect_placeholders(text)
# #         tags = self.html_tag_regex.findall(text)
# #         to_protect = placeholders + tags
# #         to_protect.sort(key=len, reverse=True)
# #         placeholder_map = {}
# #         protected_text = text
# #         for i, ph in enumerate(to_protect):
# #             token = f"PH_{i}_TOKEN"
# #             placeholder_map[token] = ph
# #             protected_text = protected_text.replace(ph, token)
# #         return protected_text, placeholder_map

# #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# #         for token, ph in placeholder_map.items():
# #             text = text.replace(token, ph)
# #         return text

# #     def _clean_translated_text(self, text: str) -> str:
# #         if not text:
# #             return ""
# #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# #         text = re.sub(r'(“|\()\s+', r'\1', text)
# #         return text.strip()

# #     def _is_likely_untranslated(self, original_text: str, translated_text: str) -> bool:
# #         protected_orig, _ = self._protect_markers(original_text)
# #         protected_trans, _ = self._protect_markers(translated_text)
# #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig).strip().lower()
# #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans).strip().lower()
# #         return raw_orig == raw_trans

# #     def _apply_custom_rules(self, msgid: str, target_language: str):
# #         if msgid in self.translation_rules:
# #             lang_map = self.translation_rules[msgid]
# #             return lang_map.get(target_language) or lang_map.get(target_language.split('_')[0])
# #         return None

# #     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
# #         key = (text, target_language)
# #         if key in self._cache:
# #             return self._cache[key]
# #         protected, map_ = self._protect_markers(text)
# #         try:
# #             trans = self.translator_engine.translate([protected], target_language)[0]
# #             result = self._restore_markers(trans, map_)
# #             result = self._clean_translated_text(result)
# #             self._cache[key] = result
# #             memory[text] = result
# #             return result
# #         except:
# #             return text

# #     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
# #         glossary_lookup = {}
# #         short_terms = {}
# #         if not csv_file_path or not os.path.exists(csv_file_path):
# #             return glossary_lookup, short_terms

# #         encodings = ['utf-8', 'latin1', 'cp1252']
# #         for encoding in encodings:
# #             try:
# #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# #                     reader = csv.DictReader(f)
# #                     for row in reader:
# #                         orig = (row.get("Original String", "") or "").strip()
# #                         ctx = (row.get("Context", "") or "").strip()
# #                         trans = (row.get("Translated String", "") or "").strip()
# #                         if orig and trans:
# #                             glossary_lookup[(orig, ctx)] = trans
# #                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
# #                                 short_terms[orig] = trans
# #                 return glossary_lookup, short_terms
# #             except:
# #                 continue
# #         return glossary_lookup, short_terms

# #     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
# #         lookup = {}
# #         if not folder_path or not os.path.exists(folder_path):
# #             return lookup

# #         lang_pattern = f"-{lang_code}."
# #         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

# #         for root, _, files in os.walk(folder_path):
# #             for file in files:
# #                 if file.startswith('._') or file.startswith('__MACOSX'):
# #                     continue
# #                 if file.lower().endswith('.po') and lang_pattern in file.lower():
# #                     file_path = os.path.join(root, file)
# #                     try:
# #                         detection = from_path(file_path).best()
# #                         encoding = detection.encoding if detection else 'utf-8'
# #                         po = polib.pofile(file_path, encoding=encoding)
# #                         for entry in po:
# #                             if entry.msgstr.strip():
# #                                 key = (entry.msgid, entry.msgctxt or '')
# #                                 cleaned = self._clean_translated_text(entry.msgstr.strip())
# #                                 if self._placeholders_are_valid(entry.msgid, cleaned):
# #                                     lookup[key] = cleaned
# #                         print(f"   ✓ Loaded: {file} ({len(lookup)} strings)")
# #                     except Exception as e:
# #                         print(f"   ✗ Failed: {file} ({e})")
# #         return lookup

# #     def _download_wporg_po(self, theme_slug: str, lang_code: str) -> Optional[Dict[Tuple[str, str], str]]:
# #         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
# #         try:
# #             response = requests.get(url, timeout=15)
# #             if response.status_code == 200 and 'msgid ""' in response.text:
# #                 temp_path = os.path.join("/tmp", f"wporg_{lang_code}.po")
# #                 with open(temp_path, 'w', encoding='utf-8') as f:
# #                     f.write(response.text)
# #                 lookup = self._load_pos_from_folder(temp_path, lang_code)
# #                 os.remove(temp_path)
# #                 print(f"   ✓ Downloaded & loaded official WP.org translations for {lang_code}")
# #                 return lookup
# #         except Exception as e:
# #             print(f"   ✗ Failed to download WP.org for {lang_code}: {e}")
# #         return {}

# #     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
# #                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str):
# #         msgid = pot_entry.msgid
# #         msgctxt = pot_entry.msgctxt or ''
# #         key = (msgid, msgctxt)
# #         full_key = f"{msgctxt}||{msgid}"

# #         self._counts["total"] += 1

# #         # 1. Protected strings — never translate
# #         if msgid in self.PROTECTED_STRINGS:
# #             self._counts["protected"] += 1
# #             return msgid, "Protected String"

# #         # 2. WordPress.org official — HIGHEST PRIORITY
# #         if key in wporg_lookup:
# #             self._counts["reused_wporg"] += 1
# #             return wporg_lookup[key], "WP.org Official"

# #         # 3. Glossary (exact match)
# #         gloss = glossary_lookup.get(key)
# #         if gloss:
# #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# #                 fb = self._fallback_translate(memory, msgid, target_language)
# #                 self._counts["translated_google"] += 1
# #                 return fb, "Glossary → Google"
# #             self._counts["reused_glossary"] += 1
# #             return gloss, "Glossary"

# #         # 4. Existing PO from ZIP
# #         if key in existing_po_lookup:
# #             existing = existing_po_lookup[key]
# #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# #                 fb = self._fallback_translate(memory, msgid, target_language)
# #                 self._counts["translated_google"] += 1
# #                 return fb, "Existing → Google"
# #             self._counts["reused_zip"] += 1
# #             return existing, "Existing PO"

# #         # 5. JSON memory
# #         if full_key in memory:
# #             val = memory[full_key]
# #             if isinstance(val, list) and val:
# #                 text = val[0]
# #                 if text.startswith(("★", "○")):
# #                     self._counts["reused_json"] += 1
# #                     return text[2:].strip(), "Global JSON"

# #         # 6. Google Translate
# #         fb = self._fallback_translate(memory, msgid, target_language)
# #         self._counts["translated_google"] += 1

# #         # 7. Automatic term replacement from glossary short terms
# #         if short_terms:
# #             final = fb
# #             for term, replacement in short_terms.items():
# #                 pattern = rf'\b{re.escape(term)}\b'
# #                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
# #                 if new_text != final:
# #                     final = new_text
# #                     self._counts["reused_glossary"] += 1
# #             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

# #         return fb, "Google Translate"

# #     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
# #             use_wporg=False, theme_slug="reviewnews"):
# #         self._display_status("Starting Localization Tool")

# #         if zip_paths_by_lang is None:
# #             zip_paths_by_lang = {}

# #         project_dir = output_dir or os.path.dirname(pot_path)
# #         os.makedirs(project_dir, exist_ok=True)

# #         valid_langs = [code for code, _ in settings.LANGUAGES]
# #         target_languages = [lang for lang in target_langs if lang in valid_langs]

# #         if not target_languages:
# #             self._display_error("No valid languages")
# #             return False

# #         try:
# #             pot_file = polib.pofile(pot_path)

# #             existing_by_lang = {}
# #             for lang in target_languages:
# #                 folder = zip_paths_by_lang.get(lang)
# #                 if folder:
# #                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
# #                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
# #                 else:
# #                     existing_by_lang[lang] = {}

# #             wporg_by_lang = {}
# #             if use_wporg:
# #                 self._display_status("Downloading official WordPress.org translations...")
# #                 for lang in target_languages:
# #                     wporg_by_lang[lang] = self._download_wporg_po(theme_slug, lang)

# #             for target_language in target_languages:
# #                 self._counts = {k: 0 for k in self._counts}

# #                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
# #                 translations_memory = {}
# #                 if os.path.exists(jed_path):
# #                     try:
# #                         with open(jed_path, 'r', encoding='utf-8') as f:
# #                             data = json.load(f)
# #                             translations_memory = {k: v for k, v in data.items() if k}
# #                     except:
# #                         pass

# #                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
# #                 glossary = glossary_data[0]
# #                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

# #                 existing_lookup = existing_by_lang[target_language]
# #                 wporg_lookup = wporg_by_lang.get(target_language, {})

# #                 version = 1
# #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# #                     version += 1

# #                 po = polib.POFile()
# #                 po.metadata = {
# #                     'Project-Id-Version': '1.0',
# #                     'Language': target_language,
# #                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
# #                     'X-Generator': 'Advanced Localization Tool 2025',
# #                 }

# #                 for entry in pot_file:
# #                     if not entry.msgid:
# #                         continue

# #                     if entry.msgid_plural:
# #                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
# #                         clean_plurals = {i: v.strip() for i, v in plurals.items()}
# #                         po.append(polib.POEntry(
# #                             msgid=entry.msgid,
# #                             msgid_plural=entry.msgid_plural,
# #                             msgstr_plural=clean_plurals,
# #                             msgctxt=entry.msgctxt,
# #                         ))
# #                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
# #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
# #                     else:
# #                         translated, source = self._process_translation(
# #                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language
# #                         )
# #                         clean = translated.strip()
# #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
# #                         symbol = "★" if "Google" not in source else "○"
# #                         prefixed = f"{symbol} {clean}"
# #                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

# #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                 out_mo = out_po.replace('.po', '.mo')
# #                 po.save(out_po)
# #                 po.save_as_mofile(out_mo)

# #                 translations_memory[""] = {"lang": target_language}
# #                 with open(jed_path, 'w', encoding='utf-8') as f:
# #                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

# #                 self._display_status(f"{target_language.upper()} v{version} complete")
# #                 for k, v in self._counts.items():
# #                     if v:
# #                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")

# #             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
# #             return True

# #         except Exception as e:
# #             import traceback
# #             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
# #             return False

# #     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
# #         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
# #         npl = 2
# #         if "nplurals=1" in header:
# #             npl = 1
# #         elif "nplurals=3" in header:
# #             npl = 3
# #         elif "nplurals=6" in header:
# #             npl = 6

# #         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
# #         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
# #             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

# #         results = {}
# #         singular = self._fallback_translate(memory, entry.msgid, target_language)
# #         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

# #         results[0] = singular
# #         for i in range(1, npl):
# #             results[i] = plural

# #         self._counts["translated_google"] += 2
# #         return results



















# # localizationtool/localization_logic.py best code till now
# # FINAL WORKING VERSION — Direct single PO load for WP.org + strong headers (January 02, 2026)

# import polib
# import csv
# import os
# import re
# import json
# import requests
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path
# from deep_translator import GoogleTranslator as _GoogleTranslator


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "|||INVISIBLE|||"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         try:
#             translator = _GoogleTranslator(source='auto', target=target_lang)
#             out = translator.translate(joined)
#             if isinstance(out, list):
#                 return [str(x) for x in out]
#             parts = str(out).split(self._SEP)
#             if len(parts) == len(texts):
#                 return parts
#         except:
#             pass
#         return [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]


# class ColabLocalizationTool:
#     def __init__(self):
#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
#         }

#         self.PROTECTED_STRINGS = {
#             "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews", "Magnitude",
#             "CoverNews", "EnterNews", "Elegant Magazine", "DarkNews", "Newsium", "NewsCrunch",
#             "AF themes", "Get Started", "Upgrade to Pro", "Upgrade Now", "Starter Sites",
#             "Header Builder", "Footer Builder", "Dashboard", "Customize"
#         }

#         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
#         self.icu_placeholder_regex = re.compile(r"\{[^}]*\}")
#         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
#         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

#         self.translation_rules = {
#             "%s min read": {
#                 "ja": "%s分で読めます", "it": "%s min di lettura", "nl": "%s min gelezen",
#                 "pl": "%s min czytania", "pt": "%s min de leitura", "de": "%s Min. Lesezeit",
#                 "ar": "قراءة في %s دقيقة", "fr": "%s min de lecture", "ru": "%s мин. чтения",
#                 "en": "%s mins read", "sw": "%s dakika kusoma", "da": "%s min læsning",
#                 "fi": "%s min lukeminen", "is": "%s mín lestur", "no": "%s min lesing",
#                 "sv": "%s min läsning", "zh-CH": "%s 分钟阅读",
#             }
#         }

#         self._counts = {
#             "total": 0, "reused_wporg": 0, "reused_glossary": 0,
#             "reused_zip": 0, "reused_json": 0, "translated_google": 0, "protected": 0
#         }
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);",
#             "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);",
#             "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
#             "ar": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
#             "nl": "nplurals=2; plural=(n != 1);",
#             "it": "nplurals=2; plural=(n != 1);",
#             "ja": "nplurals=1; plural=0;",
#             "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);",
#         }

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = self.printf_placeholder_regex.findall(text) + self.icu_placeholder_regex.findall(text) + self.quoted_printf_regex.findall(text)
#         return list(dict.fromkeys(ph))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             return set(self._collect_placeholders(original)) == set(self._collect_placeholders(translated))
#         except:
#             return False

#     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
#         placeholders = self._collect_placeholders(text)
#         tags = self.html_tag_regex.findall(text)
#         to_protect = placeholders + tags
#         to_protect.sort(key=len, reverse=True)
#         placeholder_map = {}
#         protected_text = text
#         for i, ph in enumerate(to_protect):
#             token = f"PH_{i}_TOKEN"
#             placeholder_map[token] = ph
#             protected_text = protected_text.replace(ph, token)
#         return protected_text, placeholder_map

#     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
#         for token, ph in placeholder_map.items():
#             text = text.replace(token, ph)
#         return text

#     def _clean_translated_text(self, text: str) -> str:
#         if not text:
#             return ""
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text.strip()

#     def _is_likely_untranslated(self, original_text: str, translated_text: str) -> bool:
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig).strip().lower()
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans).strip().lower()
#         return raw_orig == raw_trans

#     def _apply_custom_rules(self, msgid: str, target_language: str):
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_language) or lang_map.get(target_language.split('_')[0])
#         return None

#     def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
#         key = (text, target_language)
#         if key in self._cache:
#             return self._cache[key]
#         protected, map_ = self._protect_markers(text)
#         try:
#             trans = self.translator_engine.translate([protected], target_language)[0]
#             result = self._restore_markers(trans, map_)
#             result = self._clean_translated_text(result)
#             self._cache[key] = result
#             memory[text] = result
#             return result
#         except:
#             return text

#     def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
#         glossary_lookup = {}
#         short_terms = {}
#         if not csv_file_path or not os.path.exists(csv_file_path):
#             return glossary_lookup, short_terms

#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         if orig and trans:
#                             glossary_lookup[(orig, ctx)] = trans
#                             if len(orig) <= 10 and orig.isalpha() and orig.isupper():
#                                 short_terms[orig] = trans
#                 return glossary_lookup, short_terms
#             except:
#                 continue
#         return glossary_lookup, short_terms

#     def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
#         lookup = {}
#         if not folder_path or not os.path.exists(folder_path):
#             return lookup

#         lang_pattern = f"-{lang_code}."
#         print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

#         for root, _, files in os.walk(folder_path):
#             for file in files:
#                 if file.startswith('._') or file.startswith('__MACOSX'):
#                     continue
#                 if file.lower().endswith('.po') and lang_pattern in file.lower():
#                     file_path = os.path.join(root, file)
#                     try:
#                         detection = from_path(file_path).best()
#                         encoding = detection.encoding if detection else 'utf-8'
#                         po = polib.pofile(file_path, encoding=encoding)
#                         for entry in po:
#                             if entry.msgstr.strip():
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = self._clean_translated_text(entry.msgstr.strip())
#                                 if self._placeholders_are_valid(entry.msgid, cleaned):
#                                     lookup[key] = cleaned
#                         print(f"   ✓ Loaded: {file} ({len(lookup)} strings)")
#                     except Exception as e:
#                         print(f"   ✗ Failed: {file} ({e})")
#         return lookup

#     def _download_wporg_po(self, theme_slug: str, lang_code: str) -> Optional[Dict[Tuple[str, str], str]]:
#         url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#             'Accept': 'text/plain,*/*;q=0.9',
#             'Referer': 'https://translate.wordpress.org/',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Connection': 'keep-alive',
#         }
#         try:
#             response = requests.get(url, timeout=30, headers=headers)
#             if response.status_code == 200 and len(response.text) > 10000 and 'msgid ""' in response.text:
#                 temp_path = os.path.join("/tmp", f"wporg-{lang_code}.po")
#                 with open(temp_path, 'w', encoding='utf-8') as f:
#                     f.write(response.text)
#                 lookup = self._load_pos_from_folder("/tmp", lang_code)
#                 os.remove(temp_path)
#                 print(f"   ✓ Downloaded & loaded official WP.org translations for {lang_code} ({len(lookup)} strings)")
#                 return lookup
#             else:
#                 print(f"   ✗ WP.org invalid response (status: {response.status_code}, length: {len(response.text)})")
#         except Exception as e:
#             print(f"   ✗ Failed to download WP.org for {theme_slug}/{lang_code}: {e}")
#         return {}

#     def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
#                              wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         key = (msgid, msgctxt)
#         full_key = f"{msgctxt}||{msgid}"

#         self._counts["total"] += 1

#         if msgid in self.PROTECTED_STRINGS:
#             self._counts["protected"] += 1
#             return msgid, "Protected String"

#         if key in wporg_lookup:
#             self._counts["reused_wporg"] += 1
#             return wporg_lookup[key], "WP.org Official"

#         gloss = glossary_lookup.get(key)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 return fb, "Glossary → Google"
#             self._counts["reused_glossary"] += 1
#             return gloss, "Glossary"

#         if key in existing_po_lookup:
#             existing = existing_po_lookup[key]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 return fb, "Existing → Google"
#             self._counts["reused_zip"] += 1
#             return existing, "Existing PO"

#         if full_key in memory:
#             val = memory[full_key]
#             if isinstance(val, list) and val:
#                 text = val[0]
#                 if text.startswith(("★", "○")):
#                     self._counts["reused_json"] += 1
#                     return text[2:].strip(), "Global JSON"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         self._counts["translated_google"] += 1

#         if short_terms:
#             final = fb
#             for term, replacement in short_terms.items():
#                 pattern = rf'\b{re.escape(term)}\b'
#                 new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
#                 if new_text != final:
#                     final = new_text
#                     self._counts["reused_glossary"] += 1
#             return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

#         return fb, "Google Translate"

#     def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
#             use_wporg=False):
#         self._display_status("Starting Localization Tool")

#         if zip_paths_by_lang is None:
#             zip_paths_by_lang = {}

#         project_dir = output_dir or os.path.dirname(pot_path)
#         os.makedirs(project_dir, exist_ok=True)

#         valid_langs = [code for code, _ in settings.LANGUAGES]
#         target_languages = [lang for lang in target_langs if lang in valid_langs]

#         if not target_languages:
#             self._display_error("No valid languages")
#             return False

#         pot_filename = os.path.basename(pot_path)
#         raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
#         raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
#         raw_name = raw_name.replace(' ', '-').strip('-').lower()

#         af_themes_mapping = {
#             "chromenews": "chromenews",
#             "reviewnews": "reviewnews",
#             "morenews": "morenews",
#             "newsever": "newsever",
#             "broadnews": "broadnews",
#             "magnitude": "magnitude",
#             "covernews": "covernews",
#             "enternews": "enternews",
#             "newsium": "newsium",
#             "darknews": "darknews",
#             "newscrunch": "newscrunch",
#             "elegantmagazine": "elegant-magazine",
#         }

#         theme_slug = af_themes_mapping.get(raw_name, raw_name)
#         if not theme_slug or len(theme_slug) < 3:
#             theme_slug = "unknown-theme"

#         self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

#         try:
#             pot_file = polib.pofile(pot_path)

#             existing_by_lang = {}
#             for lang in target_languages:
#                 folder = zip_paths_by_lang.get(lang)
#                 if folder:
#                     self._display_status(f"Loading existing translations for {lang.upper()} from folder")
#                     existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
#                 else:
#                     existing_by_lang[lang] = {}

#             wporg_by_lang = {}
#             if use_wporg:
#                 self._display_status("Downloading official WordPress.org translations...")
#                 for lang in target_languages:
#                     wporg_by_lang[lang] = self._download_wporg_po(theme_slug, lang)

#             for target_language in target_languages:
#                 self._counts = {k: 0 for k in self._counts}

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}
#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             data = json.load(f)
#                             translations_memory = {k: v for k, v in data.items() if k}
#                     except:
#                         pass

#                 glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
#                 glossary = glossary_data[0]
#                 short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

#                 existing_lookup = existing_by_lang[target_language]
#                 wporg_lookup = wporg_by_lang.get(target_language, {})

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 po.metadata = {
#                     'Project-Id-Version': '1.0',
#                     'Language': target_language,
#                     'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
#                     'X-Generator': 'Advanced Localization Tool 2026',
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     if entry.msgid_plural:
#                         plurals = self._pluralize_entry(translations_memory, entry, target_language)
#                         clean_plurals = {i: v.strip() for i, v in plurals.items()}
#                         po.append(polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr_plural=clean_plurals,
#                             msgctxt=entry.msgctxt,
#                         ))
#                         prefixed = [f"★ {v.strip()}" for v in plurals.values()]
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
#                     else:
#                         translated, source = self._process_translation(
#                             translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language
#                         )
#                         clean = translated.strip()
#                         po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
#                         symbol = "★" if "Google" not in source else "○"
#                         prefixed = f"{symbol} {clean}"
#                         translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 translations_memory[""] = {"lang": target_language}
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} v{version} complete")
#                 for k, v in self._counts.items():
#                     if v:
#                         self._display_status(f"   {k.replace('_', ' ').title()}: {v}")

#             self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
#             return False

#     def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
#         npl = 2
#         if "nplurals=1" in header:
#             npl = 1
#         elif "nplurals=3" in header:
#             npl = 3
#         elif "nplurals=6" in header:
#             npl = 6

#         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#         if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
#             return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

#         results = {}
#         singular = self._fallback_translate(memory, entry.msgid, target_language)
#         plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

#         results[0] = singular
#         for i in range(1, npl):
#             results[i] = plural

#         self._counts["translated_google"] += 2
#         return results







# localizationtool/localization_logic.py
# FINAL COMPLETE VERSION — Popular themes fallback + Language priority + All methods fixed (January 05, 2026)

import polib
import csv
import os
import re
import json
import requests
from typing import Dict, Tuple, List, Optional
from django.conf import settings
from charset_normalizer import from_path
from deep_translator import GoogleTranslator as _GoogleTranslator


class _Translator:
    def translate(self, texts: List[str], target_lang: str) -> List[str]:
        raise NotImplementedError


class GoogleTranslatorEngine(_Translator):
    _SEP = "|||INVISIBLE|||"

    def translate(self, texts: List[str], target_lang: str) -> List[str]:
        if not texts:
            return []
        joined = self._SEP.join(texts)
        try:
            translator = _GoogleTranslator(source='auto', target=target_lang)
            out = translator.translate(joined)
            if isinstance(out, list):
                return [str(x) for x in out]
            parts = str(out).split(self._SEP)
            if len(parts) == len(texts):
                return parts
        except:
            pass
        return [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]


class ColabLocalizationTool:
    def __init__(self):
        self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
        os.makedirs(self.json_dir, exist_ok=True)

        self.NON_TRANSLATABLE_ENTITIES = {
            "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
            "&reg;", "&REG;", "REGISTERED_TRADEMARK",
            "&trade;", "&TRADE;", "TRADEMARK",
            "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
        }

        self.PROTECTED_STRINGS = {
            "ChromeNews", "ReviewNews", "MoreNews", "NewsEver", "BroadNews", "Magnitude",
            "CoverNews", "EnterNews", "Elegant Magazine", "DarkNews", "Newsium", "NewsCrunch",
            "AF themes", "Get Started", "Upgrade to Pro", "Upgrade Now", "Starter Sites",
            "Header Builder", "Footer Builder", "Dashboard", "Customize"
        }

        self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
        self.icu_placeholder_regex = re.compile(r"\{[^}]*\}")
        self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
        self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

        self.translation_rules = {
            "%s min read": {
                "ja": "%s分で読めます", "it": "%s min di lettura", "nl": "%s min gelezen",
                "pl": "%s min czytania", "pt": "%s min de leitura", "de": "%s Min. Lesezeit",
                "ar": "قراءة في %s دقيقة", "fr": "%s min de lecture", "ru": "%s мин. чтения",
                "en": "%s mins read", "sw": "%s dakika kusoma", "da": "%s min læsning",
                "fi": "%s min lukeminen", "is": "%s mín lestur", "no": "%s min lesing",
                "sv": "%s min läsning", "zh-CH": "%s 分钟阅读",
            }
        }

        self._counts = {
            "total": 0, "reused_wporg": 0, "reused_glossary": 0,
            "reused_zip": 0, "reused_json": 0, "translated_google": 0, "protected": 0
        }
        self._cache: Dict[Tuple[str, str], str] = {}
        self.translator_engine = GoogleTranslatorEngine()

        self.plural_forms_header = {
            "en": "nplurals=2; plural=(n != 1);",
            "es": "nplurals=2; plural=(n != 1);",
            "de": "nplurals=2; plural=(n != 1);",
            "fr": "nplurals=2; plural=(n > 1);",
            "pt": "nplurals=2; plural=(n != 1);",
            "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
            "ru": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);",
            "ar": "nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5);",
            "nl": "nplurals=2; plural=(n != 1);",
            "it": "nplurals=2; plural=(n != 1);",
            "ja": "nplurals=1; plural=0;",
            "hi": "nplurals=2; plural=(n != 1);",
            "ne": "nplurals=2; plural=(n != 1);",
        }

        # YOUR LANGUAGE PRIORITY ORDER
        self.LANGUAGE_PRIORITY = [
            "en", "es", "de", "fr", "pt", "hi", "ne", "ar", "it", "ja", "pl", "ru", "nl"
        ]

        # POPULAR THEMES FALLBACK
        self.POPULAR_THEMES_FALLBACK = [
            "astra", "neve", "generatepress", "oceanwp", "kadence",
            "blocksy", "hello-elementor", "sydney", "hestia", "zakra",
        ]

    def _display_status(self, message):
        print(f"\n--- STATUS: {message} ---")

    def _display_error(self, message):
        print(f"\n--- ERROR: {message} ---")

    def _clean_translated_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
        text = re.sub(r'(\s+)(”|\))', r'\2', text)
        text = re.sub(r'(“|\()\s+', r'\1', text)
        return text.strip()

    def _placeholders_are_valid(self, original: str, translated: str) -> bool:
        try:
            orig_ph = self.printf_placeholder_regex.findall(original) + self.icu_placeholder_regex.findall(original)
            trans_ph = self.printf_placeholder_regex.findall(translated) + self.icu_placeholder_regex.findall(translated)
            return set(orig_ph) == set(trans_ph)
        except:
            return False

    def _is_likely_untranslated(self, original_text: str, translated_text: str) -> bool:
        raw_orig = re.sub(r'PH_\d+_TOKEN', '', original_text).strip().lower()
        raw_trans = re.sub(r'PH_\d+_TOKEN', '', translated_text).strip().lower()
        return raw_orig == raw_trans

    def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
        key = (text, target_language)
        if key in self._cache:
            return self._cache[key]
        try:
            trans = self.translator_engine.translate([text], target_language)[0]
            result = self._clean_translated_text(trans)
            self._cache[key] = result
            memory[text] = result
            return result
        except:
            return text

    def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Tuple[Dict[Tuple[str, str], str], Dict[str, str]]:
        glossary_lookup = {}
        short_terms = {}
        if not csv_file_path or not os.path.exists(csv_file_path):
            return glossary_lookup, short_terms

        encodings = ['utf-8', 'latin1', 'cp1252']
        for encoding in encodings:
            try:
                with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        orig = (row.get("Original String", "") or "").strip()
                        ctx = (row.get("Context", "") or "").strip()
                        trans = (row.get("Translated String", "") or "").strip()
                        if orig and trans:
                            glossary_lookup[(orig, ctx)] = trans
                            if len(orig) <= 10 and orig.isalpha() and orig.isupper():
                                short_terms[orig] = trans
                return glossary_lookup, short_terms
            except:
                continue
        return glossary_lookup, short_terms

    def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
        lookup = {}
        if not folder_path or not os.path.exists(folder_path):
            return lookup

        lang_pattern = f"-{lang_code}."
        print(f"Loading .po files for '{lang_code}' (only files containing '{lang_pattern}')")

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.startswith('._') or file.startswith('__MACOSX'):
                    continue
                if file.lower().endswith('.po') and lang_pattern in file.lower():
                    file_path = os.path.join(root, file)
                    try:
                        detection = from_path(file_path).best()
                        encoding = detection.encoding if detection else 'utf-8'
                        po = polib.pofile(file_path, encoding=encoding)
                        for entry in po:
                            if entry.msgstr.strip():
                                key = (entry.msgid, entry.msgctxt or '')
                                cleaned = self._clean_translated_text(entry.msgstr.strip())
                                if self._placeholders_are_valid(entry.msgid, cleaned):
                                    lookup[key] = cleaned
                        print(f"   ✓ Loaded: {file} ({len(lookup)} strings)")
                    except Exception as e:
                        print(f"   ✗ Failed: {file} ({e})")
        return lookup

    def _download_wporg_po(self, theme_slug: str, lang_code: str) -> Dict[Tuple[str, str], str]:
        url = f"https://translate.wordpress.org/projects/wp-themes/{theme_slug}/{lang_code}/default/export-translations?format=po"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/plain,*/*;q=0.9',
            'Referer': 'https://translate.wordpress.org/',
        }
        try:
            response = requests.get(url, timeout=30, headers=headers)
            if response.status_code == 200 and len(response.text) > 5000 and 'msgid ""' in response.text:
                temp_path = os.path.join("/tmp", f"wporg-{lang_code}.po")
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                lookup = self._load_pos_from_folder("/tmp", lang_code)
                os.remove(temp_path)
                print(f"   ✓ Downloaded from {theme_slug}/{lang_code} ({len(lookup)} strings)")
                return lookup
            else:
                print(f"   ✗ No valid .po for {theme_slug}/{lang_code} (length: {len(response.text)})")
        except Exception as e:
            print(f"   ✗ Failed download {theme_slug}/{lang_code}: {e}")
        return {}

    def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict,
                             wporg_lookup: Dict, short_terms: Dict[str, str], target_language: str):
        msgid = pot_entry.msgid
        msgctxt = pot_entry.msgctxt or ''
        key = (msgid, msgctxt)
        full_key = f"{msgctxt}||{msgid}"

        self._counts["total"] += 1

        if msgid in self.PROTECTED_STRINGS:
            self._counts["protected"] += 1
            return msgid, "Protected String"

        if key in wporg_lookup:
            self._counts["reused_wporg"] += 1
            return wporg_lookup[key], "WP.org Official"

        gloss = glossary_lookup.get(key)
        if gloss:
            if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
                fb = self._fallback_translate(memory, msgid, target_language)
                self._counts["translated_google"] += 1
                return fb, "Glossary → Google"
            self._counts["reused_glossary"] += 1
            return gloss, "Glossary"

        if key in existing_po_lookup:
            existing = existing_po_lookup[key]
            if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
                fb = self._fallback_translate(memory, msgid, target_language)
                self._counts["translated_google"] += 1
                return fb, "Existing → Google"
            self._counts["reused_zip"] += 1
            return existing, "Existing PO"

        if full_key in memory:
            val = memory[full_key]
            if isinstance(val, list) and val:
                text = val[0]
                if text.startswith(("★", "○")):
                    self._counts["reused_json"] += 1
                    return text[2:].strip(), "Global JSON"

        fb = self._fallback_translate(memory, msgid, target_language)
        self._counts["translated_google"] += 1

        if short_terms:
            final = fb
            for term, replacement in short_terms.items():
                pattern = rf'\b{re.escape(term)}\b'
                new_text = re.sub(pattern, replacement, final, flags=re.IGNORECASE)
                if new_text != final:
                    final = new_text
                    self._counts["reused_glossary"] += 1
            return final, "Google + Auto Term Fix" if final != fb else "Google Translate"

        return fb, "Google Translate"

    def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None,
            use_wporg=False):
        self._display_status("Starting Localization Tool")

        if zip_paths_by_lang is None:
            zip_paths_by_lang = {}

        project_dir = output_dir or os.path.dirname(pot_path)
        os.makedirs(project_dir, exist_ok=True)

        valid_langs = [code for code, _ in settings.LANGUAGES]
        selected_langs = [lang for lang in target_langs if lang in valid_langs]

        if not selected_langs:
            self._display_error("No valid languages")
            return False

        # REORDER BY YOUR PRIORITY
        def priority_key(lang):
            try:
                return self.LANGUAGE_PRIORITY.index(lang)
            except ValueError:
                return len(self.LANGUAGE_PRIORITY)

        target_languages = sorted(selected_langs, key=priority_key)

        self._display_status(f"Processing languages in your priority order: {', '.join([l.upper() for l in target_languages])}")

        pot_filename = os.path.basename(pot_path)
        raw_name = re.sub(r'\.pot$|\.po$', '', pot_filename, flags=re.IGNORECASE)
        raw_name = re.sub(r'^(theme-?|wp-?|languages/|source\.?)', '', raw_name, flags=re.IGNORECASE)
        raw_name = raw_name.replace(' ', '-').strip('-').lower()

        af_themes_mapping = {
            "chromenews": "chromenews",
            "reviewnews": "reviewnews",
            "morenews": "morenews",
            "newsever": "newsever",
            "broadnews": "broadnews",
            "magnitude": "magnitude",
            "covernews": "covernews",
            "enternews": "enternews",
            "newsium": "newsium",
            "darknews": "darknews",
            "newscrunch": "newscrunch",
            "elegantmagazine": "elegant-magazine",
        }

        theme_slug = af_themes_mapping.get(raw_name, raw_name)
        if not theme_slug or len(theme_slug) < 3:
            theme_slug = "unknown-theme"

        self._display_status(f"Auto-detected theme slug: {theme_slug} (from filename '{pot_filename}')")

        try:
            pot_file = polib.pofile(pot_path)

            existing_by_lang = {}
            for lang in target_languages:
                folder = zip_paths_by_lang.get(lang)
                if folder:
                    self._display_status(f"Loading existing translations for {lang.upper()} from folder")
                    existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
                else:
                    existing_by_lang[lang] = {}

            wporg_by_lang = {}
            if use_wporg:
                self._display_status("Downloading official + popular themes translations...")
                for lang in target_languages:
                    primary = self._download_wporg_po(theme_slug, lang)
                    
                    fallback = {}
                    self._display_status(f"   Adding fallback popular themes for {lang.upper()}")
                    for popular in self.POPULAR_THEMES_FALLBACK:
                        temp = self._download_wporg_po(popular, lang)
                        for k, v in temp.items():
                            if k not in fallback:
                                fallback[k] = v
                    
                    combined = primary.copy()
                    combined.update(fallback)
                    wporg_by_lang[lang] = combined
                    print(f"   → Total WP.org + popular strings for {lang.upper()}: {len(combined)} (your theme: {len(primary)}, popular: {len(fallback)})")

            for target_language in target_languages:
                self._counts = {k: 0 for k in self._counts}

                jed_path = os.path.join(self.json_dir, f"{target_language}.json")
                translations_memory = {}
                if os.path.exists(jed_path):
                    try:
                        with open(jed_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            translations_memory = {k: v for k, v in data.items() if k}
                    except:
                        pass

                glossary_data = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else ({}, {})
                glossary = glossary_data[0]
                short_terms = glossary_data[1] if len(glossary_data) > 1 else {}

                existing_lookup = existing_by_lang[target_language]
                wporg_lookup = wporg_by_lang.get(target_language, {})

                version = 1
                while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
                    version += 1

                po = polib.POFile()
                po.metadata = {
                    'Project-Id-Version': '1.0',
                    'Language': target_language,
                    'Plural-Forms': self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);"),
                    'X-Generator': 'Advanced Localization Tool 2026',
                }

                for entry in pot_file:
                    if not entry.msgid:
                        continue

                    if entry.msgid_plural:
                        plurals = self._pluralize_entry(translations_memory, entry, target_language)
                        clean_plurals = {i: v.strip() for i, v in plurals.items()}
                        po.append(polib.POEntry(
                            msgid=entry.msgid,
                            msgid_plural=entry.msgid_plural,
                            msgstr_plural=clean_plurals,
                            msgctxt=entry.msgctxt,
                        ))
                        prefixed = [f"★ {v.strip()}" for v in plurals.values()]
                        translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = prefixed
                    else:
                        translated, source = self._process_translation(
                            translations_memory, entry, glossary, existing_lookup, wporg_lookup, short_terms, target_language
                        )
                        clean = translated.strip()
                        po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
                        symbol = "★" if "Google" not in source else "○"
                        prefixed = f"{symbol} {clean}"
                        translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]

                out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
                out_mo = out_po.replace('.po', '.mo')
                po.save(out_po)
                po.save_as_mofile(out_mo)

                translations_memory[""] = {"lang": target_language}
                with open(jed_path, 'w', encoding='utf-8') as f:
                    json.dump(translations_memory, f, ensure_ascii=False, indent=2, sort_keys=True)

                self._display_status(f"{target_language.upper()} v{version} complete")
                for k, v in self._counts.items():
                    if v:
                        self._display_status(f"   {k.replace('_', ' ').title()}: {v}")

            self._display_status("ALL LANGUAGES COMPLETED SUCCESSFULLY!")
            return True

        except Exception as e:
            import traceback
            self._display_error(f"Crash: {e}\n{traceback.format_exc()}")
            return False

    def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
        header = self.plural_forms_header.get(target_language, "nplurals=2; plural=(n != 1);")
        npl = 2
        if "nplurals=1" in header:
            npl = 1
        elif "nplurals=3" in header:
            npl = 3
        elif "nplurals=6" in header:
            npl = 6

        full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
        if full_key in memory and isinstance(memory[full_key], list) and len(memory[full_key]) >= npl:
            return {i: memory[full_key][i][2:].strip() if memory[full_key][i].startswith("★") else memory[full_key][i].strip() for i in range(npl)}

        results = {}
        singular = self._fallback_translate(memory, entry.msgid, target_language)
        plural = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)

        results[0] = singular
        for i in range(1, npl):
            results[i] = plural

        self._counts["translated_google"] += 2
        return results

