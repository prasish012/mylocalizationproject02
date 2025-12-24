# # # # # mylocalizationproject/localizationtool/localization_logic.py
# # # # import polib
# # # # import csv
# # # # import zipfile
# # # # import os
# # # # import shutil
# # # # from datetime import datetime
# # # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # # import re
# # # # from charset_normalizer import from_path
# # # # import time
# # # # import json
# # # # from typing import Dict, Tuple, List, Optional
# # # # from django.conf import settings  # For LANGUAGES list

# # # # try:
# # # #     from babel.core import Locale
# # # #     from babel.plural import PluralRule
# # # # except Exception:  # Babel optional; code works with fallback headers
# # # #     Locale = None
# # # #     PluralRule = None


# # # # class _Translator:
# # # #     """Pluggable translator interface."""
# # # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # # #         raise NotImplementedError


# # # # class GoogleTranslatorEngine(_Translator):
# # # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator with UTF-8 support."""
# # # #     _SEP = "\u2063"  # Invisible Separator – rare in UI text

# # # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # # #         if not texts:
# # # #             return []
# # # #         joined = self._SEP.join(texts)
# # # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # # #         try:
# # # #             out = translator.translate(joined)
# # # #             if isinstance(out, list):
# # # #                 return [str(x) for x in out]
# # # #             parts = str(out).split(self._SEP)
# # # #             if len(parts) != len(texts):
# # # #                 parts = [self._translate_single(t, target_lang) for t in texts]
# # # #             return [p.encode('utf-8', errors='replace').decode('utf-8') for p in parts]
# # # #         except exceptions.TranslationError as e:
# # # #             print(f"Translation error for {target_lang}: {e}")
# # # #             return [self._translate_single(t, target_lang) for t in texts]

# # # #     def _translate_single(self, text: str, target_lang: str) -> str:
# # # #         try:
# # # #             translator = _GoogleTranslator(source='auto', target=target_lang)
# # # #             return str(translator.translate(text)).encode('utf-8', errors='replace').decode('utf-8')
# # # #         except exceptions.TranslationError:
# # # #             return text  # Fallback to original text if translation fails


# # # # class ColabLocalizationTool:
# # # #     def __init__(self, memory_base_dir: str = "translation_memory"):
# # # #         self.pot_file_path = None
# # # #         self.zip_file_path = None
# # # #         self.csv_file_path = None
# # # #         self.target_languages: List[str] = []
# # # #         self.temp_dir = "/tmp/po_extract"
# # # #         self.memory_base_dir = memory_base_dir
# # # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # # #         self.translation_rules = {
# # # #             "%s min read": {
# # # #                 "ja": "%s分で読めます",
# # # #                 "it": "%s min di lettura",
# # # #                 "nl": "%s minuten gelezen",
# # # #                 "pl": "%s min czytania",
# # # #                 "pt": "%s min de leitura",
# # # #                 "de": "%s Min. Lesezeit",
# # # #                 "ar": "قراءة في %s دقيقة",
# # # #                 "fr": "%s min de lecture",
# # # #                 "ru": "%s мин. чтения",
# # # #                 "en": "%s mins read"
# # # #             }
# # # #         }

# # # #         self.translation_rules_plural_templates = {
# # # #             "%s min read": {
# # # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # # #                 "ja": {"other": "%s分で読めます"},  # Japanese uses no plural forms
# # # #                 "nl": {"one": "%s minuut gelezen", "other": "%s minuten gelezen"},
# # # #             }
# # # #         }

# # # #         self.memory_storage_limit_mb = 100
# # # #         self._qa_rows: List[Dict] = []
# # # #         self._counts = {
# # # #             "new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0,
# # # #         }
# # # #         self._cache: Dict[Tuple[str, str], str] = {}
# # # #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# # # #         self.plural_forms_header = {
# # # #             "en": "nplurals=2; plural=(n != 1);",
# # # #             "es": "nplurals=2; plural=(n != 1);",
# # # #             "de": "nplurals=2; plural=(n != 1);",
# # # #             "fr": "nplurals=2; plural=(n > 1);",
# # # #             "pt": "nplurals=2; plural=(n != 1);",
# # # #             "hi": "nplurals=2; plural=(n != 1);",
# # # #             "ne": "nplurals=2; plural=(n != 1);",
# # # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # # #             "it": "nplurals=2; plural=(n != 1);",
# # # #             "ja": "nplurals=1; plural=0;",
# # # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # # #             "nl": "nplurals=2; plural=(n != 1);",
# # # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # # #             "zh": "nplurals=1; plural=0;",
# # # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # # #         }

# # # #     def _get_memory_file_path(self, project_name, lang):
# # # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # # #         os.makedirs(project_dir, exist_ok=True)
# # # #         return os.path.join(project_dir, f"{lang}.json")

# # # #     def _get_snapshot_file_path(self, project_name):
# # # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # # #         os.makedirs(project_dir, exist_ok=True)
# # # #         return os.path.join(project_dir, "_last_snapshot.json")

# # # #     def _load_memory(self, project_name, lang):
# # # #         path = self._get_memory_file_path(project_name, lang)
# # # #         if os.path.exists(path):
# # # #             try:
# # # #                 with open(path, 'r', encoding='utf-8') as f:
# # # #                     return json.load(f)
# # # #             except Exception:
# # # #                 return {}
# # # #         return {}

# # # #     def _save_memory(self, memory, project_name, lang):
# # # #         path = self._get_memory_file_path(project_name, lang)
# # # #         try:
# # # #             with open(path, 'w', encoding='utf-8') as f:
# # # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # # #         except Exception as e:
# # # #             self._display_error(f"Failed to save memory file: {e}")

# # # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # # #         return memory.get(msgid)

# # # #     def _update_memory(self, memory, msgid, translation):
# # # #         memory[msgid] = translation

# # # #     def _display_status(self, message):
# # # #         print(f"\n--- STATUS: {message} ---")

# # # #     def _display_error(self, message):
# # # #         print(f"\n--- ERROR: {message} ---")

# # # #     def _parse_glossary_csv(self, csv_file_path):
# # # #         """Enhanced CSV parsing with better error handling."""
# # # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # # #         try:
# # # #             detected = from_path(csv_file_path).best()
# # # #             encoding = detected.encoding if detected else 'utf-8'
# # # #             with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # # #                 reader = csv.DictReader(f)
# # # #                 for row in reader:
# # # #                     orig = (row.get("Original String", "") or "").strip()
# # # #                     ctx = (row.get("Context", "") or "").strip()
# # # #                     trans = (row.get("Translated String", "") or "").strip()
# # # #                     trans = self._normalize_placeholders(trans)
# # # #                     if orig and trans:
# # # #                         glossary_lookup[(orig, ctx)] = trans
# # # #         except Exception as e:
# # # #             self._display_error(f"Glossary parse error: {str(e)} - Using fallback encoding 'utf-8' with errors='replace'")
# # # #         return glossary_lookup

# # # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # # #         key = (msgid, msgctxt or '')
# # # #         if key in glossary_lookup:
# # # #             return glossary_lookup[key]
# # # #         for (orig, ctx), trans in glossary_lookup.items():
# # # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # # #                 return trans
# # # #         return None

# # # #     def _normalize_placeholders(self, msgstr):
# # # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # # #         existing_po_lookup = {}
# # # #         if os.path.exists(self.temp_dir):
# # # #             shutil.rmtree(self.temp_dir)
# # # #         os.makedirs(self.temp_dir)
# # # #         try:
# # # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # # #                 for member in zf.namelist():
# # # #                     if member.endswith('.po'):
# # # #                         zf.extract(member, self.temp_dir)
# # # #                         path = os.path.join(self.temp_dir, member)
# # # #                         try:
# # # #                             po = polib.pofile(path)
# # # #                             for entry in po:
# # # #                                 key = (entry.msgid, entry.msgctxt or '')
# # # #                                 cleaned_msgstr = entry.msgstr
# # # #                                 if cleaned_msgstr:
# # # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # # #                                         existing_po_lookup[key] = cleaned_msgstr
# # # #                         except Exception as e:
# # # #                             self._display_error(f"Error parsing PO: {e}")
# # # #         except Exception as e:
# # # #             self._display_error(f"Error extracting ZIP: {e}")
# # # #         finally:
# # # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # # #         return existing_po_lookup

# # # #     def _collect_placeholders(self, text: str) -> List[str]:
# # # #         ph = []
# # # #         ph += self.printf_placeholder_regex.findall(text)
# # # #         ph += self.icu_placeholder_regex.findall(text)
# # # #         quoted = self.quoted_printf_regex.findall(text)
# # # #         ph += quoted
# # # #         normalized = []
# # # #         for x in ph:
# # # #             if isinstance(x, tuple):
# # # #                 normalized.append('{' + x[0] + '}')
# # # #             else:
# # # #                 normalized.append(x)
# # # #         return list(dict.fromkeys(normalized))

# # # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # # #         try:
# # # #             orig_ph = self._collect_placeholders(original)
# # # #             trans_ph = self._collect_placeholders(translated)
# # # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # # #         except Exception as e:
# # # #             self._display_error(f"Placeholder validation failed: {e}")
# # # #             return False

# # # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # # #         placeholders = self._collect_placeholders(text)
# # # #         tags = self.html_tag_regex.findall(text)
# # # #         to_protect = placeholders + tags
# # # #         to_protect.sort(key=len, reverse=True)
# # # #         placeholder_map = {}
# # # #         protected_text = text
# # # #         for i, ph in enumerate(to_protect):
# # # #             token = f"PH_{i}_TOKEN"
# # # #             placeholder_map[token] = ph
# # # #             protected_text = protected_text.replace(ph, token)
# # # #         return protected_text, placeholder_map

# # # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # # #         for token in list(placeholder_map.keys()):
# # # #             escaped = re.escape(token)
# # # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # # #             text = pattern.sub(token, text)
# # # #         for token, ph in placeholder_map.items():
# # # #             text = text.replace(token, ph)
# # # #         return text

# # # #     def _clean_translated_text(self, text):
# # # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # # #         return text

# # # #     def _is_likely_untranslated(self, original_text, translated_text):
# # # #         protected_orig, _ = self._protect_markers(original_text)
# # # #         protected_trans, _ = self._protect_markers(translated_text)
# # # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # # #         if msgid in self.translation_rules_plural_templates:
# # # #             lang_map = self.translation_rules_plural_templates[msgid]
# # # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # # #             if lang_map and plural_category and plural_category in lang_map:
# # # #                 return lang_map[plural_category]
# # # #         if msgid in self.translation_rules:
# # # #             lang_map = self.translation_rules[msgid]
# # # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # # #         return None

# # # #     def _is_valid_translation(self, text):
# # # #         error_signs = ["Error 500", "That’s an error", "There was an error", "<html", "</html>", "<body>", "</body>", "Please try again later"]
# # # #         lowered = text.lower()
# # # #         return not any(s.lower() in lowered for s in error_signs)

# # # #     def _retry(self, func, max_retries=3):
# # # #         delay = 1.0
# # # #         for i in range(max_retries):
# # # #             try:
# # # #                 return func()
# # # #             except Exception as e:
# # # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # # #                 if i == max_retries - 1:
# # # #                     raise
# # # #                 time.sleep(delay)
# # # #                 delay *= 2

# # # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # # #         outputs = [None] * len(texts)
# # # #         to_query_idx = []
# # # #         to_query = []
# # # #         for i, t in enumerate(texts):
# # # #             mem = self._get_memory_translation(memory, t, target_lang)
# # # #             if mem:
# # # #                 outputs[i] = mem
# # # #                 continue
# # # #             key = (t, target_lang)
# # # #             if key in self._cache:
# # # #                 outputs[i] = self._cache[key]
# # # #             else:
# # # #                 to_query_idx.append(i)
# # # #                 to_query.append(t)
# # # #         if to_query:
# # # #             def call():
# # # #                 return self.translator_engine.translate(to_query, target_lang)
# # # #             translated_list = self._retry(call, max_retries=3)
# # # #             for j, out in enumerate(translated_list):
# # # #                 idx = to_query_idx[j]
# # # #                 outputs[idx] = out
# # # #                 self._cache[(texts[idx], target_lang)] = out
# # # #                 self._update_memory(memory, texts[idx], out)
# # # #         return [x or "" for x in outputs]

# # # #     def _fallback_translate(self, memory, text, target_lang):
# # # #         mem = self._get_memory_translation(memory, text, target_lang)
# # # #         if mem:
# # # #             return mem
# # # #         key = (text, target_lang)
# # # #         if key in self._cache:
# # # #             return self._cache[key]
# # # #         protected_text, placeholder_map = self._protect_markers(text)
# # # #         translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # # #         translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # # #         translated = self._restore_markers(translated_protected, placeholder_map)
# # # #         translated = self._clean_translated_text(translated)
# # # #         if not self._is_valid_translation(translated):
# # # #             self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # # #             return text
# # # #         self._cache[key] = translated
# # # #         self._update_memory(memory, text, translated)
# # # #         return translated

# # # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # # #         msgid = pot_entry.msgid
# # # #         msgctxt = pot_entry.msgctxt or ''
# # # #         key_ctxt = (msgid, msgctxt)

# # # #         custom = self._apply_custom_rules(msgid, target_lang)
# # # #         if custom:
# # # #             self._update_memory(memory, msgid, custom)
# # # #             self._counts["translated"] += 1
# # # #             return custom, "Custom Rule"

# # # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # # #         if gloss:
# # # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # # #                 self._counts["translated"] += 1
# # # #                 return fb, "Glossary (Fuzzy)"
# # # #             self._update_memory(memory, msgid, gloss)
# # # #             self._counts["reused"] += 1
# # # #             return gloss, "Glossary"

# # # #         if key_ctxt in existing_po_lookup:
# # # #             existing = existing_po_lookup[key_ctxt]
# # # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # # #                 self._counts["translated"] += 1
# # # #                 return fb, "Existing PO (Fuzzy)"
# # # #             self._update_memory(memory, msgid, existing)
# # # #             self._counts["reused"] += 1
# # # #             return existing, "Existing PO"

# # # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # # #         self._counts["translated"] += 1
# # # #         return fb, "Machine Translation"

# # # #     def _plural_header_for_lang(self, lang: str) -> str:
# # # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # # #     def _nplurals_from_header(self, header: str) -> int:
# # # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # # #         return int(m.group(1)) if m else 2

# # # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # # #         base = lang.split('_', 1)[0]
# # # #         if PluralRule and Locale:
# # # #             try:
# # # #                 loc = Locale.parse(lang)
# # # #             except Exception:
# # # #                 try:
# # # #                     loc = Locale.parse(base)
# # # #                 except Exception:
# # # #                     loc = None
# # # #             if loc:
# # # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # # #         return ["one", "other"] if lang != "ja" else ["other"]

# # # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # # #         header = self._plural_header_for_lang(target_lang)
# # # #         npl = self._nplurals_from_header(header)
# # # #         categories = self._plural_categories_for_lang(target_lang)
# # # #         if "one" not in categories:
# # # #             categories = ["one"] + [c for c in categories if c != "one"]
# # # #         if "other" not in categories:
# # # #             categories = categories + ["other"]

# # # #         templates_by_cat: Dict[str, str] = {}
# # # #         for cat in categories:
# # # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # # #             if custom:
# # # #                 templates_by_cat[cat] = custom

# # # #         if not templates_by_cat:
# # # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # # #             templates_by_cat["one"] = one_tmpl
# # # #             templates_by_cat["other"] = other_tmpl

# # # #         idx_map = ["one", "other"] if npl == 2 else ["one", "few", "other"] if npl == 3 else ["zero", "one", "two", "few", "many", "other"][:npl]
# # # #         idx_map = [c if c in categories else "other" for c in idx_map]

# # # #         msgstr_plural: Dict[int, str] = {}
# # # #         for i, cat in enumerate(idx_map):
# # # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # # #             msgstr_plural[i] = tmpl
# # # #         return msgstr_plural

# # # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # # #         snap = {}
# # # #         for e in pot:
# # # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # # #             snap[key] = {"msgctxt": e.msgctxt or '', "msgid": e.msgid or '', "msgid_plural": e.msgid_plural or ''}
# # # #         return snap

# # # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # # #         diff = {}
# # # #         for k, nv in new.items():
# # # #             if k not in old:
# # # #                 diff[k] = "new"
# # # #             else:
# # # #                 ov = old[k]
# # # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # # #                     diff[k] = "modified"
# # # #                 else:
# # # #                     diff[k] = "unchanged"
# # # #         return diff

# # # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # # #         issues = []
# # # #         if not translated:
# # # #             issues.append("empty")
# # # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # # #             issues.append("placeholders")
# # # #         tags = self.html_tag_regex.findall(translated)
# # # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # # #         closes = sum(1 for t in tags if t.startswith("</"))
# # # #         if opens != closes:
# # # #             issues.append("html_unbalanced")
# # # #         if self._is_likely_untranslated(entry.msgid, translated):
# # # #             issues.append("unchanged_like")
# # # #         row = {"msgctxt": entry.msgctxt or '', "msgid": entry.msgid, "msgid_plural": entry.msgid_plural or '', "target_lang": target_lang, "status": status, "issues": ",".join(issues)}
# # # #         self._qa_rows.append(row)
# # # #         if "placeholders" in issues or "empty" in issues:
# # # #             self._counts["failed"] += 1

# # # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # # #         self._display_status("Starting WP Localization Tool")

# # # #         self.pot_file_path = pot_path
# # # #         self.zip_file_path = zip_path
# # # #         self.csv_file_path = csv_path
# # # #         self.target_languages = [lang for lang in target_langs if lang in dict(settings.LANGUAGES)]  # Validate against LANGUAGES

# # # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # # #         project_dir = output_dir  # Save directly in output_dir (no random subfolder)
# # # #         os.makedirs(project_dir, exist_ok=True)

# # # #         if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # # #             self._display_error("POT file not found.")
# # # #             return None

# # # #         pot_file = polib.pofile(self.pot_file_path)

# # # #         snapshot_path = self._get_snapshot_file_path(project_name)
# # # #         prev_snap = {}
# # # #         if os.path.exists(snapshot_path):
# # # #             try:
# # # #                 with open(snapshot_path, 'r', encoding='utf-8') as f:
# # # #                     prev_snap = json.load(f)
# # # #             except Exception:
# # # #                 prev_snap = {}
# # # #         new_snap = self._snapshot_from_pot(pot_file)
# # # #         diff_map = self._diff_snapshots(prev_snap, new_snap)

# # # #         with open(snapshot_path, 'w', encoding='utf-8') as f:
# # # #             json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # # #         glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # # #         existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # # #         entry_status: Dict[polib.POEntry, str] = {}
# # # #         for e in pot_file:
# # # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # # #             status = diff_map.get(key, "new")
# # # #             entry_status[e] = status
# # # #             self._counts[status] += 1

# # # #         timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

# # # #         for target_language in self.target_languages:
# # # #             self._qa_rows = []
# # # #             self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # # #             memory = self._load_memory(project_name, target_language)
# # # #             self._display_status(f"Translating into {target_language}…")
# # # #             po = polib.POFile()
# # # #             now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # # #             po.metadata = {
# # # #                 'Project-Id-Version': 'Colab Free',
# # # #                 'POT-Creation-Date': now,
# # # #                 'PO-Revision-Date': now,
# # # #                 'Language': target_language,
# # # #                 'MIME-Version': '1.0',
# # # #                 'Content-Type': 'text/plain; charset=UTF-8',
# # # #                 'Content-Transfer-Encoding': '8bit',
# # # #                 'X-Generator': 'Colab Tool',
# # # #                 'Plural-Forms': self._plural_header_for_lang(target_language)
# # # #             }

# # # #             for entry in pot_file:
# # # #                 if not entry.msgid:
# # # #                     continue
# # # #                 status = entry_status.get(entry, "new")
# # # #                 try:
# # # #                     if entry.msgid_plural:
# # # #                         msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # # #                         new_entry = polib.POEntry(
# # # #                             msgid=entry.msgid,
# # # #                             msgid_plural=entry.msgid_plural,
# # # #                             msgstr_plural=msgstr_plural,
# # # #                             msgctxt=entry.msgctxt,
# # # #                             occurrences=entry.occurrences,
# # # #                             comment=entry.comment,
# # # #                             tcomment=entry.tcomment
# # # #                         )
# # # #                         if status == "modified":
# # # #                             new_entry.flags.append("fuzzy")
# # # #                             self._counts["fuzzy"] += 1
# # # #                         po.append(new_entry)
# # # #                         for i, s in msgstr_plural.items():
# # # #                             self._qa_check(entry, s, status, target_language)
# # # #                         continue

# # # #                     translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)

# # # #                     new_entry = polib.POEntry(
# # # #                         msgid=entry.msgid,
# # # #                         msgstr=translated_msgstr,
# # # #                         msgctxt=entry.msgctxt,
# # # #                         occurrences=entry.occurrences,
# # # #                         comment=entry.comment,
# # # #                         tcomment=entry.tcomment
# # # #                     )
# # # #                     if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # # #                         new_entry.flags.append("fuzzy")
# # # #                         self._counts["fuzzy"] += 1
# # # #                     if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # # #                         self._counts["reused"] += 1

# # # #                     po.append(new_entry)
# # # #                     self._qa_check(entry, translated_msgstr, status, target_language)
# # # #                 except Exception as e:
# # # #                     self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # # #                     new_entry = polib.POEntry(
# # # #                         msgid=entry.msgid,
# # # #                         msgstr='',
# # # #                         msgctxt=entry.msgctxt,
# # # #                         occurrences=entry.occurrences,
# # # #                         comment=entry.comment,
# # # #                         tcomment=entry.tcomment
# # # #                     )
# # # #                     new_entry.flags.append("fuzzy")
# # # #                     self._counts["failed"] += 1
# # # #                     po.append(new_entry)

# # # #             # Save files directly in project_dir (output_dir)
# # # #             out_po = os.path.join(project_dir, f"{target_language}-v1.po")
# # # #             out_mo = os.path.join(project_dir, f"{target_language}-v1.mo")
# # # #             po.save(out_po)
# # # #             po.save_as_mofile(out_mo)

# # # #             self._save_memory(memory, project_name, target_language)

# # # #             report_json = os.path.join(project_dir, f"report-{target_language}-{timestamp}.json")
# # # #             report_csv = os.path.join(project_dir, f"report-{target_language}-{timestamp}.csv")
# # # #             report = {
# # # #                 "language": target_language,
# # # #                 "generated_at": timestamp,
# # # #                 "counts": dict(self._counts),
# # # #                 "rows": self._qa_rows,
# # # #             }
# # # #             try:
# # # #                 with open(report_json, 'w', encoding='utf-8') as f:
# # # #                     json.dump(report, f, ensure_ascii=False, indent=2)
# # # #             except Exception as e:
# # # #                 self._display_error(f"Failed to write JSON report: {e}")
# # # #             try:
# # # #                 if self._qa_rows:
# # # #                     headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # # #                     with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # # #                         w = csv.DictWriter(f, fieldnames=headers)
# # # #                         w.writeheader()
# # # #                         for r in self._qa_rows:
# # # #                             w.writerow({k: r.get(k, "") for k in headers})
# # # #             except Exception as e:
# # # #                 self._display_error(f"Failed to write CSV report: {e}")

# # # #         self._display_status("Translation complete.")
# # # #         return True



# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings  # For LANGUAGES list

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except Exception:  # Babel optional; code works with fallback headers
# # #     Locale = None
# # #     PluralRule = None


# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError


# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator with UTF-8 support."""
# # #     _SEP = "\u2063"  # Invisible Separator – rare in UI text

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         try:
# # #             out = translator.translate(joined)
# # #             if isinstance(out, list):
# # #                 return [str(x) for x in out]
# # #             parts = str(out).split(self._SEP)
# # #             if len(parts) != len(texts):
# # #                 parts = [self._translate_single(t, target_lang) for t in texts]
# # #             return [p.encode('utf-8', errors='replace').decode('utf-8') for p in parts]
# # #         except exceptions.TranslationError as e:
# # #             print(f"Translation error for {target_lang}: {e}")
# # #             return [self._translate_single(t, target_lang) for t in texts]

# # #     def _translate_single(self, text: str, target_lang: str) -> str:
# # #         try:
# # #             translator = _GoogleTranslator(source='auto', target=target_lang)
# # #             return str(translator.translate(text)).encode('utf-8', errors='replace').decode('utf-8')
# # #         except exceptions.TranslationError:
# # #             return text  # Fallback to original text if translation fails


# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = "translation_memory"):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = "/tmp/po_extract"
# # #         self.memory_base_dir = memory_base_dir
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s minuten gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #                 "ja": {"other": "%s分で読めます"},
# # #                 "nl": {"one": "%s minuut gelezen", "other": "%s minuten gelezen"},
# # #             }
# # #         }

# # #         self.memory_storage_limit_mb = 100
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0,
# # #         }
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #         }

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         """Enhanced CSV parsing with better error handling."""
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         try:
# # #             detected = from_path(csv_file_path).best()
# # #             encoding = detected.encoding if detected else 'utf-8'
# # #             with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                 reader = csv.DictReader(f)
# # #                 for row in reader:
# # #                     orig = (row.get("Original String", "") or "").strip()
# # #                     ctx = (row.get("Context", "") or "").strip()
# # #                     trans = (row.get("Translated String", "") or "").strip()
# # #                     trans = self._normalize_placeholders(trans)
# # #                     if orig and trans:
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #         except Exception as e:
# # #             self._display_error(f"Glossary parse error: {str(e)} - Using fallback encoding 'utf-8' with errors='replace'")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = ["Error 500", "That’s an error", "There was an error", "<html", "</html>", "<body>", "</body>", "Please try again later"]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         outputs = [None] * len(texts)
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]
# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #         translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #         translated = self._restore_markers(translated_protected, placeholder_map)
# # #         translated = self._clean_translated_text(translated)
# # #         if not self._is_valid_translation(translated):
# # #             self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #             return text
# # #         self._cache[key] = translated
# # #         self._update_memory(memory, text, translated)
# # #         return translated

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key_ctxt = (msgid, msgctxt)

# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc:
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"] if lang != "ja" else ["other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         idx_map = ["one", "other"] if npl == 2 else ["one", "few", "other"] if npl == 3 else ["zero", "one", "two", "few", "many", "other"][:npl]
# # #         idx_map = [c if c in categories else "other" for c in idx_map]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {"msgctxt": e.msgctxt or '', "msgid": e.msgid or '', "msgid_plural": e.msgid_plural or ''}
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {"msgctxt": entry.msgctxt or '', "msgid": entry.msgid, "msgid_plural": entry.msgid_plural or '', "target_lang": target_lang, "status": status, "issues": ",".join(issues)}
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # #         self._display_status("Starting WP Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         self.target_languages = [lang for lang in target_langs if lang in dict(settings.LANGUAGES)]  # Validate against LANGUAGES

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         # REMOVE random subdirectory creation
# # #         project_dir = output_dir  # Save directly to output_dir, no subfolder

# # #         os.makedirs(project_dir, exist_ok=True)

# # #         if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # #             self._display_error("POT file not found.")
# # #             return None

# # #         pot_file = polib.pofile(self.pot_file_path)

# # #         snapshot_path = self._get_snapshot_file_path(project_name)
# # #         prev_snap = {}
# # #         if os.path.exists(snapshot_path):
# # #             try:
# # #                 with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                     prev_snap = json.load(f)
# # #             except Exception:
# # #                 prev_snap = {}
# # #         new_snap = self._snapshot_from_pot(pot_file)
# # #         diff_map = self._diff_snapshots(prev_snap, new_snap)

# # #         with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #             json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #         glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #         existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #         entry_status: Dict[polib.POEntry, str] = {}
# # #         for e in pot_file:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             status = diff_map.get(key, "new")
# # #             entry_status[e] = status
# # #             self._counts[status] += 1

# # #         timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

# # #         for target_language in self.target_languages:
# # #             self._qa_rows = []
# # #             self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #             memory = self._load_memory(project_name, target_language)
# # #             self._display_status(f"Translating into {target_language}…")
# # #             po = polib.POFile()
# # #             now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # #             po.metadata = {
# # #                 'Project-Id-Version': 'Colab Free',
# # #                 'POT-Creation-Date': now,
# # #                 'PO-Revision-Date': now,
# # #                 'Language': target_language,
# # #                 'MIME-Version': '1.0',
# # #                 'Content-Type': 'text/plain; charset=UTF-8',
# # #                 'Content-Transfer-Encoding': '8bit',
# # #                 'X-Generator': 'Colab Tool',
# # #                 'Plural-Forms': self._plural_header_for_lang(target_language)
# # #             }

# # #             for entry in pot_file:
# # #                 if not entry.msgid:
# # #                     continue
# # #                 status = entry_status.get(entry, "new")
# # #                 try:
# # #                     if entry.msgid_plural:
# # #                         msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural=msgstr_plural,
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         if status == "modified":
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["fuzzy"] += 1
# # #                         po.append(new_entry)
# # #                         for i, s in msgstr_plural.items():
# # #                             self._qa_check(entry, s, status, target_language)
# # #                         continue

# # #                     translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)

# # #                     new_entry = polib.POEntry(
# # #                         msgid=entry.msgid,
# # #                         msgstr=translated_msgstr,
# # #                         msgctxt=entry.msgctxt,
# # #                         occurrences=entry.occurrences,
# # #                         comment=entry.comment,
# # #                         tcomment=entry.tcomment
# # #                     )
# # #                     if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # #                         new_entry.flags.append("fuzzy")
# # #                         self._counts["fuzzy"] += 1
# # #                     if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                         self._counts["reused"] += 1

# # #                     po.append(new_entry)
# # #                     self._qa_check(entry, translated_msgstr, status, target_language)
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # #                     new_entry = polib.POEntry(
# # #                         msgid=entry.msgid,
# # #                         msgstr='',
# # #                         msgctxt=entry.msgctxt,
# # #                         occurrences=entry.occurrences,
# # #                         comment=entry.comment,
# # #                         tcomment=entry.tcomment
# # #                     )
# # #                     new_entry.flags.append("fuzzy")
# # #                     self._counts["failed"] += 1
# # #                     po.append(new_entry)

# # #             # Save files directly in project_dir (output_dir)
# # #             out_po = os.path.join(project_dir, f"{target_language}-v1.po")
# # #             out_mo = os.path.join(project_dir, f"{target_language}-v1.mo")
# # #             po.save(out_po)
# # #             po.save_as_mofile(out_mo)

# # #             self._save_memory(memory, project_name, target_language)

# # #             report_json = os.path.join(project_dir, f"report-{target_language}-{timestamp}.json")
# # #             report_csv = os.path.join(project_dir, f"report-{target_language}-{timestamp}.csv")
# # #             report = {
# # #                 "language": target_language,
# # #                 "generated_at": timestamp,
# # #                 "counts": dict(self._counts),
# # #                 "rows": self._qa_rows,
# # #             }
# # #             try:
# # #                 with open(report_json, 'w', encoding='utf-8') as f:
# # #                     json.dump(report, f, ensure_ascii=False, indent=2)
# # #             except Exception as e:
# # #                 self._display_error(f"Failed to write JSON report: {e}")
# # #             try:
# # #                 if self._qa_rows:
# # #                     headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                     with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                         w = csv.DictWriter(f, fieldnames=headers)
# # #                         w.writeheader()
# # #                         for r in self._qa_rows:
# # #                             w.writerow({k: r.get(k, "") for k in headers})
# # #             except Exception as e:
# # #                 self._display_error(f"Failed to write CSV report: {e}")

# # #         self._display_status("Translation complete.")
# # #         return True



# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional

# # # # Import Django settings to validate languages
# # # from django.conf import settings

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except Exception:  # Babel optional; code works with fallback headers
# # #     Locale = None
# # #     PluralRule = None


# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError


# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator.
# # #     We implement naive batching by joining with a delimiter that is unlikely to appear.
# # #     """

# # #     _SEP = "\u2063"  # Invisible Separator – rare in UI text

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         out = translator.translate(joined)
# # #         # Some engines may return list already; normalize to string first
# # #         if isinstance(out, list):
# # #             # deep_translator usually returns str; handle list defensively
# # #             return [str(x) for x in out]
# # #         parts = str(out).split(self._SEP)
# # #         if len(parts) != len(texts):
# # #             # delimiter collision fallback – translate one by one
# # #             parts = []
# # #             for t in texts:
# # #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# # #         return parts


# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = "translation_memory"):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = "/tmp/po_extract"
# # #         self.memory_base_dir = memory_base_dir
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # Placeholder regexes (extended)
# # #         # printf: %s, %1$s, %d, %04d, %name, %%
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         # ICU/JS: {0}, {name}, {count, plural, one {...} other {...}}
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         # HTML tags: <b>, </b>, <strong attr="..">, <br/>
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         # Legacy complex placeholder (from quotes)
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         # Custom rule templates for specific strings (by msgid)
# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"  # default plural template – we still map one/other
# # #             }
# # #         }

# # #         # Plural templates for languages that need category-specific texts
# # #         # For msgid "%s min read" -> different singular/plural.
# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 # category -> template
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #             }
# # #         }

# # #         # Limit for all memories (not enforced strictly here; kept from original)
# # #         self.memory_storage_limit_mb = 100

# # #         # QA & diff tracking (per run)
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0,
# # #             "modified": 0,
# # #             "unchanged": 0,
# # #             "reused": 0,
# # #             "fuzzy": 0,
# # #             "failed": 0,
# # #             "translated": 0,
# # #         }

# # #         # In-memory translation cache for this run
# # #         self._cache: Dict[Tuple[str, str], str] = {}

# # #         # Default translator engine (pluggable)
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# # #         # Plural-Forms header map (gettext) for common locales
# # #         # Add more as needed.
# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             # The following are inconsistent with the simplified forms.py but are kept for completeness
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #         }

# # #     # -----------------------
# # #     # Memory Handling
# # #     # -----------------------
# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     # -----------------------
# # #     # Status & Error
# # #     # -----------------------
# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     # -----------------------
# # #     # Glossary
# # #     # -----------------------
# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         """CSV columns: Original String, Translated String, Context (optional, regex allowed)."""
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         try:
# # #             detected = from_path(csv_file_path).best()
# # #             encoding = detected.encoding if detected else 'utf-8'
# # #             with open(csv_file_path, 'r', encoding=encoding) as f:
# # #                 reader = csv.DictReader(f)
# # #                 for row in reader:
# # #                     orig = (row.get("Original String", "") or "").strip()
# # #                     ctx = (row.get("Context", "") or "").strip()
# # #                     trans = (row.get("Translated String", "") or "").strip()
# # #                     trans = self._normalize_placeholders(trans)
# # #                     glossary_lookup[(orig, ctx)] = trans
# # #         except Exception as e:
# # #             self._display_error(f"Glossary parse error: {e}")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         # 1) Exact context match
# # #         key = (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         # 2) Partial context match (substring)
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #         # 3) Regex context match
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx:
# # #                 try:
# # #                     if re.search(ctx, msgctxt or ''):
# # #                         return trans
# # #                 except re.error:
# # #                     continue
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     # -----------------------
# # #     # Existing PO files
# # #     # -----------------------
# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     # -----------------------
# # #     # Placeholders
# # #     # -----------------------
# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         # Normalize ICU capture (regex returns only the name) into canonical tokens
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):  # ICU group returns tuple due to capturing name
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         # Unique, keep order by dict
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         # Sort long → short to avoid partial overlaps
# # #         to_protect.sort(key=len, reverse=True)
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         # Avoid token mangling by MT adding spaces – normalize tokens first
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         # Plural-aware specific templates if present
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         # Non-plural override
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = [
# # #             "Error 500",
# # #             "That’s an error",
# # #             "There was an error",
# # #             "<html", "</html>", "<body>", "</body>",
# # #             "Please try again later",
# # #         ]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     # -----------------------
# # #     # Translation Core
# # #     # -----------------------
# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         # Use cache + translator_engine
# # #         outputs: List[str] = [None] * len(texts)  # type: ignore
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             # Memory first
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             # Run-cache
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         # Returns a single string; use batch variant for speed when possible
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]

# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         try:
# # #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #             translated = self._restore_markers(translated_protected, placeholder_map)
# # #             translated = self._clean_translated_text(translated)
# # #             if not self._is_valid_translation(translated):
# # #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #                 return text
# # #             self._cache[key] = translated
# # #             self._update_memory(memory, text, translated)
# # #             return translated
# # #         except exceptions.NotValidPayload as e:
# # #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# # #             return text
# # #         except Exception as e:
# # #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# # #             return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key_ctxt = (msgid, msgctxt)

# # #         # Custom rules (non-plural)
# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         # Glossary (context-aware)
# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         # Existing PO reuse
# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         # MT fallback
# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     # -----------------------
# # #     # Pluralization helpers
# # #     # -----------------------
# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         # Requires Babel; otherwise default to [one, other]
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc is not None:
# # #                 # Common set – order is heuristic (one, two, few, many, other)
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         # Ensure at least one/other
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         # Build base templates: try custom plural templates, else translate msgid and msgid_plural
# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             # Fallback: translate singular and plural once each
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         # Map indices 0..npl-1 to categories heuristically: 0->one, last->other
# # #         idx_map: List[str] = []
# # #         if npl == 1:
# # #             idx_map = ["other"]
# # #         elif npl == 2:
# # #             idx_map = ["one", "other"]
# # #         elif npl == 3:
# # #             # Slavic-like: one, few, other
# # #             pref = ["one", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         elif npl == 4:
# # #             pref = ["one", "two", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         else:  # 5 or 6 (Arabic)
# # #             pref = ["zero", "one", "two", "few", "many", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     # -----------------------
# # #     # POT diffing
# # #     # -----------------------
# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {
# # #                 "msgctxt": e.msgctxt or '',
# # #                 "msgid": e.msgid or '',
# # #                 "msgid_plural": e.msgid_plural or ''
# # #             }
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         # returns key -> status: new|modified|unchanged
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     # -----------------------
# # #     # QA helpers
# # #     # -----------------------
# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         # HTML balance (very naive): count opening/closing tags
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {
# # #             "msgctxt": entry.msgctxt or '',
# # #             "msgid": entry.msgid,
# # #             "msgid_plural": entry.msgid_plural or '',
# # #             "target_lang": target_lang,
# # #             "status": status,
# # #             "issues": ",".join(issues)
# # #         }
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     # -----------------------
# # #     # Main run
# # #     # -----------------------
# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # #         self._display_status("Starting WP Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         self.target_languages = target_langs

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         project_dir = os.path.join(output_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         try:
# # #             if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # #                 self._display_error("POT file not found.")
# # #                 return None

# # #             pot_file = polib.pofile(self.pot_file_path)

# # #             # POT diffing against last snapshot
# # #             snapshot_path = self._get_snapshot_file_path(project_name)
# # #             prev_snap = {}
# # #             if os.path.exists(snapshot_path):
# # #                 try:
# # #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                         prev_snap = json.load(f)
# # #                 except Exception:
# # #                     prev_snap = {}
# # #             new_snap = self._snapshot_from_pot(pot_file)
# # #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# # #             # Persist new snapshot for next run
# # #             with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #                 json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #             glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #             # Prepare list of entries with their diff status
# # #             entry_status: Dict[polib.POEntry, str] = {}
# # #             for e in pot_file:
# # #                 key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #                 status = diff_map.get(key, "new")
# # #                 entry_status[e] = status
# # #                 self._counts[status] += 1

# # #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

# # #             for target_language in self.target_languages:
# # #                 self._qa_rows = []
# # #                 # Reset per-language counters that matter (keep global diffs)
# # #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #                 memory = self._load_memory(project_name, target_language)
# # #                 self._display_status(f"Translating into {target_language}…")
# # #                 po = polib.POFile()
# # #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # #                 po.metadata = {
# # #                     'Project-Id-Version': 'Colab Free',
# # #                     'POT-Creation-Date': now,
# # #                     'PO-Revision-Date': now,
# # #                     'Language': target_language,
# # #                     'MIME-Version': '1.0',
# # #                     'Content-Type': 'text/plain; charset=UTF-8',
# # #                     'Content-Transfer-Encoding': '8bit',
# # #                     'X-Generator': 'Colab Tool',
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue
# # #                     status = entry_status.get(entry, "new")
# # #                     try:
# # #                         if entry.msgid_plural:
# # #                             # Plural path: build msgstr_plural
# # #                             msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgid_plural=entry.msgid_plural,
# # #                                 msgstr_plural=msgstr_plural,
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             if status == "modified":
# # #                                 new_entry.flags.append("fuzzy")
# # #                                 self._counts["fuzzy"] += 1
# # #                             po.append(new_entry)
# # #                             # QA for each plural form (combine issues)
# # #                             for i, s in msgstr_plural.items():
# # #                                 self._qa_check(entry, s, status, target_language)
# # #                             continue

# # #                         # Non-plural path
# # #                         translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)

# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgstr=translated_msgstr,
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["fuzzy"] += 1
# # #                         if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                             self._counts["reused"] += 1

# # #                         po.append(new_entry)
# # #                         self._qa_check(entry, translated_msgstr, status, target_language)
# # #                     except Exception as e:
# # #                         self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgstr='',
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         new_entry.flags.append("fuzzy")
# # #                         self._counts["failed"] += 1
# # #                         po.append(new_entry)

# # #                 # --- Save PO & MO files with versioning ---
# # #                 counter = 1
# # #                 while True:
# # #                     out_po = os.path.join(project_dir, f"{target_language}-v{counter}.po")
# # #                     out_mo = os.path.join(project_dir, f"{target_language}-v{counter}.mo")
# # #                     if not os.path.exists(out_po) and not os.path.exists(out_mo):
# # #                         po.save(out_po)
# # #                         po.save_as_mofile(out_mo)
# # #                         break
# # #                     counter += 1

# # #                 # Save memory JSON
# # #                 self._save_memory(memory, project_name, target_language)

# # #                 # --- Reports ---
# # #                 report_json = os.path.join(project_dir, f"report-{target_language}-{timestamp}.json")
# # #                 report_csv = os.path.join(project_dir, f"report-{target_language}-{timestamp}.csv")
# # #                 report = {
# # #                     "language": target_language,
# # #                     "generated_at": timestamp,
# # #                     "counts": dict(self._counts),
# # #                     "rows": self._qa_rows,
# # #                 }
# # #                 try:
# # #                     with open(report_json, 'w', encoding='utf-8') as f:
# # #                         json.dump(report, f, ensure_ascii=False, indent=2)
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write JSON report: {e}")
# # #                 try:
# # #                     # CSV
# # #                     if self._qa_rows:
# # #                         headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                         with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                             w = csv.DictWriter(f, fieldnames=headers)
# # #                             w.writeheader()
# # #                             for r in self._qa_rows:
# # #                                 w.writerow({k: r.get(k, "") for k in headers})
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write CSV report: {e}")

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Unexpected error during setup or file processing: {e}")
# # #             return False


# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None

# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError

# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# # #     _SEP = "\u2063"  # Invisible Separator

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         out = translator.translate(joined)
# # #         if isinstance(out, list):
# # #             return [str(x) for x in out]
# # #         parts = str(out).split(self._SEP)
# # #         if len(parts) != len(texts):
# # #             parts = []
# # #             for t in texts:
# # #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# # #         return parts

# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # Placeholder regexes
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #             }
# # #         }

# # #         self.memory_storage_limit_mb = 100
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0,
# # #             "modified": 0,
# # #             "unchanged": 0,
# # #             "reused": 0,
# # #             "fuzzy": 0,
# # #             "failed": 0,
# # #             "translated": 0,
# # #         }
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()
# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #         }

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         """CSV columns: Original String, Translated String, Context (optional, regex allowed)."""
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# # #         self._display_error("All encoding attempts failed for glossary CSV.")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #             if orig == msgid and ctx:
# # #                 try:
# # #                     if re.search(ctx, msgctxt or ''):
# # #                         return trans
# # #                 except re.error:
# # #                     continue
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         to_protect.sort(key=len, reverse=True)
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = [
# # #             "Error 500",
# # #             "That’s an error",
# # #             "There was an error",
# # #             "<html", "</html>", "<body>", "</body>",
# # #             "Please try again later",
# # #         ]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         outputs: List[str] = [None] * len(texts)
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]

# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         try:
# # #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #             translated = self._restore_markers(translated_protected, placeholder_map)
# # #             translated = self._clean_translated_text(translated)
# # #             if not self._is_valid_translation(translated):
# # #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #                 return text
# # #             self._cache[key] = translated
# # #             self._update_memory(memory, text, translated)
# # #             return translated
# # #         except exceptions.NotValidPayload as e:
# # #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# # #             return text
# # #         except Exception as e:
# # #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# # #             return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key_ctxt = (msgid, msgctxt)

# # #         # Custom rules (non-plural)
# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         # Glossary (context-aware)
# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         # Existing PO reuse
# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         # MT fallback
# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc is not None:
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         idx_map: List[str] = []
# # #         if npl == 1:
# # #             idx_map = ["other"]
# # #         elif npl == 2:
# # #             idx_map = ["one", "other"]
# # #         elif npl == 3:
# # #             pref = ["one", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         elif npl == 4:
# # #             pref = ["one", "two", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         else:
# # #             pref = ["zero", "one", "two", "few", "many", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {
# # #                 "msgctxt": e.msgctxt or '',
# # #                 "msgid": e.msgid or '',
# # #                 "msgid_plural": e.msgid_plural or ''
# # #             }
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {
# # #             "msgctxt": entry.msgctxt or '',
# # #             "msgid": entry.msgid,
# # #             "msgid_plural": entry.msgid_plural or '',
# # #             "target_lang": target_lang,
# # #             "status": status,
# # #             "issues": ",".join(issues)
# # #         }
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # #         self._display_status("Starting Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# # #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# # #         if not self.target_languages:
# # #             self._display_error("No valid target languages provided.")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         project_dir = output_dir
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         try:
# # #             if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # #                 self._display_error("POT file not found.")
# # #                 return False

# # #             pot_file = polib.pofile(self.pot_file_path)

# # #             snapshot_path = self._get_snapshot_file_path(project_name)
# # #             prev_snap = {}
# # #             if os.path.exists(snapshot_path):
# # #                 try:
# # #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                         prev_snap = json.load(f)
# # #                 except Exception:
# # #                     prev_snap = {}
# # #             new_snap = self._snapshot_from_pot(pot_file)
# # #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# # #             with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #                 json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #             glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #             entry_status: Dict[polib.POEntry, str] = {}
# # #             for e in pot_file:
# # #                 key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #                 status = diff_map.get(key, "new")
# # #                 entry_status[e] = status
# # #                 self._counts[status] += 1

# # #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# # #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# # #             os.makedirs(report_dir, exist_ok=True)

# # #             for target_language in self.target_languages:
# # #                 self._qa_rows = []
# # #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #                 memory = self._load_memory(project_name, target_language)
# # #                 self._display_status(f"Translating into {target_language}…")
# # #                 po = polib.POFile()
# # #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # #                 po.metadata = {
# # #                     'Project-Id-Version': 'Colab Free',
# # #                     'POT-Creation-Date': now,
# # #                     'PO-Revision-Date': now,
# # #                     'Language': target_language,
# # #                     'MIME-Version': '1.0',
# # #                     'Content-Type': 'text/plain; charset=UTF-8',
# # #                     'Content-Transfer-Encoding': '8bit',
# # #                     'X-Generator': 'Colab Tool',
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue
# # #                     status = entry_status.get(entry, "new")
# # #                     try:
# # #                         if entry.msgid_plural:
# # #                             msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgid_plural=entry.msgid_plural,
# # #                                 msgstr_plural=msgstr_plural,
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             if status == "modified":
# # #                                 new_entry.flags.append("fuzzy")
# # #                                 self._counts["fuzzy"] += 1
# # #                             po.append(new_entry)
# # #                             for i, s in msgstr_plural.items():
# # #                                 self._qa_check(entry, s, status, target_language)
# # #                             continue

# # #                         translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgstr=translated_msgstr,
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["fuzzy"] += 1
# # #                         if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                             self._counts["reused"] += 1
# # #                         po.append(new_entry)
# # #                         self._qa_check(entry, translated_msgstr, status, target_language)
# # #                     except Exception as e:
# # #                         self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgstr='',
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         new_entry.flags.append("fuzzy")
# # #                         self._counts["failed"] += 1
# # #                         po.append(new_entry)

# # #                 out_po = os.path.join(project_dir, f"{target_language}.po")
# # #                 out_mo = os.path.join(project_dir, f"{target_language}.mo")
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# # #                 report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# # #                 report = {
# # #                     "language": target_language,
# # #                     "generated_at": timestamp,
# # #                     "counts": dict(self._counts),
# # #                     "rows": self._qa_rows,
# # #                 }
# # #                 try:
# # #                     with open(report_json, 'w', encoding='utf-8') as f:
# # #                         json.dump(report, f, ensure_ascii=False, indent=2)
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write JSON report: {e}")
# # #                 try:
# # #                     if self._qa_rows:
# # #                         headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                         with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                             w = csv.DictWriter(f, fieldnames=headers)
# # #                             w.writeheader()
# # #                             for r in self._qa_rows:
# # #                                 w.writerow({k: r.get(k, "") for k in headers})
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write CSV report: {e}")

# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Unexpected error during setup or file processing: {e}")
# # #             return False



# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None

# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError

# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# # #     _SEP = "\u2063"  # Invisible Separator

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         out = translator.translate(joined)
# # #         if isinstance(out, list):
# # #             return [str(x) for x in out]
# # #         parts = str(out).split(self._SEP)
# # #         if len(parts) != len(texts):
# # #             parts = []
# # #             for t in texts:
# # #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# # #         return parts

# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # Placeholder regexes
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #             }
# # #         }

# # #         self.memory_storage_limit_mb = 100
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0,
# # #             "modified": 0,
# # #             "unchanged": 0,
# # #             "reused": 0,
# # #             "fuzzy": 0,
# # #             "failed": 0,
# # #             "translated": 0,
# # #         }
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()
# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #         }

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         """CSV columns: Original String, Translated String, Context (optional, regex allowed)."""
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# # #         self._display_error("All encoding attempts failed for glossary CSV.")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #             if orig == msgid and ctx:
# # #                 try:
# # #                     if re.search(ctx, msgctxt or ''):
# # #                         return trans
# # #                 except re.error:
# # #                     continue
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = [
# # #             "Error 500",
# # #             "That’s an error",
# # #             "There was an error",
# # #             "<html", "</html>", "<body>", "</body>",
# # #             "Please try again later",
# # #         ]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         outputs: List[str] = [None] * len(texts)
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]

# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         try:
# # #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #             translated = self._restore_markers(translated_protected, placeholder_map)
# # #             translated = self._clean_translated_text(translated)
# # #             if not self._is_valid_translation(translated):
# # #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #                 return text
# # #             self._cache[key] = translated
# # #             self._update_memory(memory, text, translated)
# # #             return translated
# # #         except exceptions.NotValidPayload as e:
# # #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# # #             return text
# # #         except Exception as e:
# # #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# # #             return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key_ctxt = (msgid, msgctxt)

# # #         # Custom rules (non-plural)
# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         # Glossary (context-aware)
# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         # Existing PO reuse
# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         # MT fallback
# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc is not None:
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         idx_map: List[str] = []
# # #         if npl == 1:
# # #             idx_map = ["other"]
# # #         elif npl == 2:
# # #             idx_map = ["one", "other"]
# # #         elif npl == 3:
# # #             pref = ["one", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         elif npl == 4:
# # #             pref = ["one", "two", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         else:
# # #             pref = ["zero", "one", "two", "few", "many", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {
# # #                 "msgctxt": e.msgctxt or '',
# # #                 "msgid": e.msgid or '',
# # #                 "msgid_plural": e.msgid_plural or ''
# # #             }
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {
# # #             "msgctxt": entry.msgctxt or '',
# # #             "msgid": entry.msgid,
# # #             "msgid_plural": entry.msgid_plural or '',
# # #             "target_lang": target_lang,
# # #             "status": status,
# # #             "issues": ",".join(issues)
# # #         }
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir, existing_translations=None):
# # #         self._display_status("Starting Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# # #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# # #         if not self.target_languages:
# # #             self._display_error("No valid target languages provided.")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         project_dir = output_dir
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         try:
# # #             if not os.path.exists(self.pot_file_path):
# # #                 self._display_error("POT file not found.")
# # #                 return False

# # #             pot_file = polib.pofile(self.pot_file_path)

# # #             # Snapshot for diff
# # #             snapshot_path = self._get_snapshot_file_path(project_name)
# # #             prev_snap = {}
# # #             if os.path.exists(snapshot_path):
# # #                 with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                     prev_snap = json.load(f)
# # #             new_snap = self._snapshot_from_pot(pot_file)
# # #             diff_map = self._diff_snapshots(prev_snap, new_snap)
# # #             with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #                 json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #             glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #             # Build entry_status
# # #             entry_status = {}
# # #             for e in pot_file:
# # #                 key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #                 status = diff_map.get(key, "new")
# # #                 entry_status[e] = status
# # #                 self._counts[status] += 1

# # #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# # #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# # #             os.makedirs(report_dir, exist_ok=True)

# # #             for target_language in self.target_languages:
# # #                 self._qa_rows = []
# # #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #                 memory = self._load_memory(project_name, target_language)
# # #                 self._display_status(f"Translating into {target_language}…")
# # #                 po = polib.POFile()
# # #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
# # #                 po.metadata = {
# # #                     'Project-Id-Version': 'Colab Free',
# # #                     'POT-Creation-Date': now,
# # #                     'PO-Revision-Date': now,
# # #                     'Language': target_language,
# # #                     'MIME-Version': '1.0',
# # #                     'Content-Type': 'text/plain; charset=UTF-8',
# # #                     'Content-Transfer-Encoding': '8bit',
# # #                     'X-Generator': 'Colab Tool',
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 # Versioning
# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 # === MAIN LOOP: ONE PLACE FOR REUSE ===
# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     status = entry_status.get(entry, "new")
# # #                     reused = False

# # #                     # === REUSE FROM existing_translations (supports msgctxt) ===
# # #                     if existing_translations and target_language in existing_translations:
# # #                         key = entry.msgid
# # #                         if entry.msgctxt:
# # #                             key = f"{entry.msgctxt}|||{entry.msgid}"
# # #                         if key in existing_translations[target_language]:
# # #                             msgstr = existing_translations[target_language][key]
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr=msgstr,
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             if status == "unchanged":
# # #                                 new_entry.flags.append("reused")
# # #                                 self._counts["reused"] += 1
# # #                             po.append(new_entry)
# # #                             self._qa_check(entry, msgstr, status, target_language)
# # #                             reused = True

# # #                     if reused:
# # #                         continue  # Skip MT

# # #                     # === PLURAL ===
# # #                     if entry.msgid_plural:
# # #                         msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                         new_entry = polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural=msgstr_plural,
# # #                             msgctxt=entry.msgctxt,
# # #                             occurrences=entry.occurrences,
# # #                             comment=entry.comment,
# # #                             tcomment=entry.tcomment
# # #                         )
# # #                         if status == "modified":
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["fuzzy"] += 1
# # #                         po.append(new_entry)
# # #                         for s in msgstr_plural.values():
# # #                             self._qa_check(entry, s, status, target_language)
# # #                         continue

# # #                     # === NORMAL TRANSLATION ===
# # #                     translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                     new_entry = polib.POEntry(
# # #                         msgid=entry.msgid,
# # #                         msgstr=translated_msgstr,
# # #                         msgctxt=entry.msgctxt,
# # #                         occurrences=entry.occurrences,
# # #                         comment=entry.comment,
# # #                         tcomment=entry.tcomment
# # #                     )
# # #                     if status == "modified" or "Fuzzy" in source:
# # #                         new_entry.flags.append("fuzzy")
# # #                         self._counts["fuzzy"] += 1
# # #                     if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                         self._counts["reused"] += 1
# # #                     po.append(new_entry)
# # #                     self._qa_check(entry, translated_msgstr, status, target_language)

# # #                 # === SAVE .po and .mo ===
# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 # === REPORT ===
# # #                 report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# # #                 report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# # #                 report = {
# # #                     "language": target_language,
# # #                     "generated_at": timestamp,
# # #                     "counts": dict(self._counts),
# # #                     "rows": self._qa_rows,
# # #                 }
# # #                 with open(report_json, 'w', encoding='utf-8') as f:
# # #                     json.dump(report, f, ensure_ascii=False, indent=2)
# # #                 if self._qa_rows:
# # #                     headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                     with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                         w = csv.DictWriter(f, fieldnames=headers)
# # #                         w.writeheader()
# # #                         for r in self._qa_rows:
# # #                             w.writerow({k: r.get(k, "") for k in headers})

# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Unexpected error: {e}")
# # #             import traceback
# # #             traceback.print_exc()
# # #             return False



# # # localization_logic.py

# # # localization_logic.py

# # # localization_logic.py

# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator
# # # import re
# # # import time
# # # import json
# # # import logging
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # # === LOGGING SETUP ===
# # # logger = logging.getLogger(__name__)
# # # logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None


# # # class _Translator:
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError


# # # class GoogleTranslatorEngine(_Translator):
# # #     _SEP = "\u2063"

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         try:
# # #             out = translator.translate(joined)
# # #             if isinstance(out, list):
# # #                 return [str(x) for x in out]
# # #             parts = str(out).split(self._SEP)
# # #             return parts if len(parts) == len(texts) else [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]
# # #         except Exception as e:
# # #             logger.warning("GoogleTranslatorEngine batch failed: %s", e)
# # #             return [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]


# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # Language mappings
# # #         self.lang_map = {code: name for code, name in settings.LANGUAGES}
# # #         self.base_map = {
# # #             'en-us': 'en', 'en-gb': 'en', 'en-ca': 'en', 'en-au': 'en', 'en-nz': 'en',
# # #             'es-ar': 'es', 'es-mx': 'es', 'es-cl': 'es', 'es-co': 'es', 'es-pe': 'es',
# # #             'fr-ca': 'fr',
# # #             'pt-br': 'pt',
# # #             'nl-be': 'nl',
# # #         }

# # #         # Google Translator language codes + 'in' alias for Indonesian
# # #         self.google_lang_map = {
# # #             'en': 'en', 'en-us': 'en', 'en-gb': 'en', 'en-ca': 'en', 'en-au': 'en', 'en-nz': 'en',
# # #             'es': 'es', 'es-ar': 'es', 'es-mx': 'es', 'es-cl': 'es', 'es-co': 'es', 'es-pe': 'es',
# # #             'fr': 'fr', 'fr-ca': 'fr',
# # #             'pt': 'pt', 'pt-br': 'pt',
# # #             'de': 'de',
# # #             'it': 'it',
# # #             'nl': 'nl', 'nl-be': 'nl',
# # #             'pl': 'pl',
# # #             'ru': 'ru',
# # #             'ar': 'ar',
# # #             'ja': 'ja',
# # #             'ko': 'ko',
# # #             'id': 'id', 'in': 'id',  # ← ALIAS FIX
# # #             'hi': 'hi',
# # #             'ne': 'ne',
# # #             'th': 'th',
# # #             'tl': 'tl',
# # #             'sw': 'sw',
# # #             'af': 'af',
# # #             'sv': 'sv',
# # #             'no': 'no',
# # #             'da': 'da',
# # #             'fi': 'fi',
# # #             'yo': 'yo',
# # #         }

# # #         # Regex
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         # %s min read rules
# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "en": "%s min read", "en-us": "%s min read", "en-gb": "%s min read", "en-ca": "%s min read", "en-au": "%s min read", "en-nz": "%s min read",
# # #                 "es": "%s min de lectura", "es-ar": "%s min de lectura", "es-mx": "%s min de lectura", "es-cl": "%s min de lectura", "es-co": "%s min de lectura", "es-pe": "%s min de lectura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "fr": "%s min de lecture", "fr-ca": "%s min de lecture",
# # #                 "pt": "%s min de leitura", "pt-br": "%s min de leitura",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen", "nl-be": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "ru": "%s мин. чтения",
# # #                 "hi": "%s मिनट पढ़ें",
# # #                 "ne": "%s मिनेट पढाइ",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "ja": "%s分で読めます",
# # #                 "id": "%s menit baca",
# # #                 "th": "%s นาที อ่าน",
# # #                 "tl": "%s min basahin",
# # #                 "sw": "%s dakika kusoma",
# # #                 "af": "%s min gelees",
# # #                 "sv": "%s min läsning",
# # #                 "no": "%s min lesing",
# # #                 "da": "%s min læsning",
# # #                 "fi": "%s min lukeminen",
# # #                 "yo": "%s min kika",
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-us": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-gb": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-ca": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-au": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-nz": {"one": "%s min read", "other": "%s mins read"},
# # #                 "es": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-ar": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "de": {"one": "%s Min. Lesezeit", "other": "%s Min. Lesezeit"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "fr-ca": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "pt": {"one": "%s min de leitura", "other": "%s min de leitura"},
# # #                 "pt-br": {"one": "%s min de lectura", "other": "%s min de leitura"},
# # #                 "it": {"one": "%s min di lettura", "other": "%s min di lettura"},
# # #                 "nl": {"one": "%s min gelezen", "other": "%s min gelezen"},
# # #                 "nl-be": {"one": "%s min gelezen", "other": "%s min gelezen"},
# # #                 "pl": {"one": "%s min czytania", "few": "%s min czytania", "many": "%s min czytania", "other": "%s min czytania"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "hi": {"one": "%s मिनट पढ़ें", "other": "%s मिनट पढ़ें"},
# # #                 "ne": {"one": "%s मिनेट पढाइ", "other": "%s मिनेट पढाइ"},
# # #                 "ar": {"zero": "قراءة في 0 دقيقة", "one": "قراءة في دقيقة %s", "two": "قراءة في دقيقتين %s", "few": "قراءة في %s دقائق", "many": "قراءة في %s دقيقة", "other": "قراءة في %s دقيقة"},
# # #                 "ja": {"other": "%s分で読めます"},
# # #                 "id": {"other": "%s menit baca"},
# # #                 "th": {"other": "%s นาที อ่าน"},
# # #                 "tl": {"other": "%s min basahin"},
# # #                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
# # #                 "af": {"one": "%s min gelees", "other": "%s min gelees"},
# # #                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
# # #                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
# # #                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
# # #                 "fi": {"other": "%s min lukeminen"},
# # #                 "yo": {"one": "%s min kika", "other": "%s min kika"},
# # #             }
# # #         }

# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {"new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0}
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# # #         # === PLURAL FORMS (FIXED: Indonesian = 1 plural) ===
# # #         self.plural_forms_header = {}
# # #         for code, _ in settings.LANGUAGES:
# # #             base = code.split('-')[0]
# # #             if base in ['ja', 'ko', 'th', 'tl', 'fi', 'id']:  # ← id added
# # #                 self.plural_forms_header[code] = "nplurals=1; plural=0;"
# # #             elif base in ['en', 'es', 'de', 'it', 'nl', 'hi', 'ne', 'sv', 'no', 'da', 'af', 'sw', 'yo']:
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n != 1);"
# # #             elif base == 'fr':
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n > 1);"
# # #             elif base == 'pt':
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n > 1);"
# # #             elif base == 'pl':
# # #                 self.plural_forms_header[code] = "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);"
# # #             elif base == 'ru':
# # #                 self.plural_forms_header[code] = "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);"
# # #             elif base == 'ar':
# # #                 self.plural_forms_header[code] = "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 && n%100<=10?3 : n%100>=11 && n%100<=99?4 : 5);"
# # #             else:
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n != 1);"

# # #     def _get_base_lang(self, lang):
# # #         return self.base_map.get(lang, lang.split('-')[0] if '-' in lang else lang)

# # #     def _get_google_lang(self, lang):
# # #         return self.google_lang_map.get(lang, self.google_lang_map.get(self._get_base_lang(lang), 'en'))

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception as e:
# # #                 logger.warning("Failed to load memory for %s: %s", lang, e)
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             logger.error("Failed to save memory for %s: %s", lang, e)

# # #     def _display_status(self, message):
# # #         logger.info(message)
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         logger.error(message)
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error: {e}")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         return glossary_lookup.get(key)

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned = entry.msgstr
# # #                                 if cleaned:
# # #                                     cleaned = self._normalize_placeholders(cleaned)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                                         existing_po_lookup[key] = self._clean_translated_text(cleaned)
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = self.printf_placeholder_regex.findall(text) + self.icu_placeholder_regex.findall(text)
# # #         ph += self.quoted_printf_regex.findall(text)
# # #         return list(dict.fromkeys([x[0] if isinstance(x, tuple) else x for x in ph]))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             return set(self._collect_placeholders(original)) == set(self._collect_placeholders(translated))
# # #         except Exception:
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         to_protect = self._collect_placeholders(text) + self.html_tag_regex.findall(text)
# # #         to_protect = list(dict.fromkeys(to_protect))
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         return text.strip()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         base_lang = self._get_base_lang(target_lang)
# # #         if msgid in self.translation_rules_plural_templates:
# # #             rule = self.translation_rules_plural_templates[msgid].get(target_lang) or self.translation_rules_plural_templates[msgid].get(base_lang)
# # #             if rule and plural_category and plural_category in rule:
# # #                 return rule[plural_category]
# # #         if msgid in self.translation_rules:
# # #             return self.translation_rules[msgid].get(target_lang) or self.translation_rules[msgid].get(base_lang)
# # #         return None

# # #     # === ROBUST BATCH + RETRY ===
# # #     def _translate_with_retry(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         google_lang = self._get_google_lang(target_lang)
# # #         for attempt in range(3):
# # #             try:
# # #                 res = self.translator_engine.translate(texts, google_lang)
# # #                 if isinstance(res, list) and len(res) == len(texts):
# # #                     return res
# # #                 if isinstance(res, str):
# # #                     parts = res.split(GoogleTranslatorEngine._SEP)
# # #                     if len(parts) == len(texts):
# # #                         return parts
# # #                 logger.info("Translator returned unexpected result, falling back to per-item translate")
# # #                 break
# # #             except Exception as e:
# # #                 logger.warning("Batch translate attempt %d failed for %s: %s", attempt + 1, target_lang, e)
# # #                 time.sleep(1 + attempt)
# # #         # Fallback: per-item
# # #         out = []
# # #         for t in texts:
# # #             for attempt in range(3):
# # #                 try:
# # #                     val = _GoogleTranslator(source='auto', target=google_lang).translate(t)
# # #                     out.append(val)
# # #                     time.sleep(0.8)
# # #                     break
# # #                 except Exception as e:
# # #                     logger.warning("Per-item translate failed (attempt %d) for lang %s: %s", attempt + 1, target_lang, e)
# # #                     time.sleep(1.2)
# # #             else:
# # #                 logger.error("Giving up translating string for lang %s; returning original text", target_lang)
# # #                 out.append(t)
# # #         return out

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         if text in memory:
# # #             return memory[text]
# # #         protected, pmap = self._protect_markers(text)
# # #         google_lang = self._get_google_lang(target_lang)
# # #         try:
# # #             result = self.translator_engine.translate([protected], google_lang)
# # #             trans = result[0] if isinstance(result, list) else str(result)
# # #             time.sleep(0.9)
# # #             trans = self._restore_markers(trans, pmap)
# # #             trans = self._clean_translated_text(trans)
# # #             memory[text] = trans
# # #             return trans
# # #         except Exception as e:
# # #             logger.exception("Fallback translation failed for lang %s: %s", target_lang, e)
# # #             try:
# # #                 direct = _GoogleTranslator(source='auto', target=google_lang).translate(protected)
# # #                 direct = self._restore_markers(direct, pmap)
# # #                 direct = self._clean_translated_text(direct)
# # #                 memory[text] = direct
# # #                 return direct
# # #             except Exception as e2:
# # #                 logger.exception("Direct translator also failed: %s", e2)
# # #                 return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key = (msgid, msgctxt)

# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             memory[msgid] = custom
# # #             return custom, "Custom"

# # #         if key in glossary_lookup:
# # #             gloss = glossary_lookup[key]
# # #             if self._placeholders_are_valid(msgid, gloss):
# # #                 memory[msgid] = gloss
# # #                 return gloss, "Glossary"

# # #         if key in existing_po_lookup:
# # #             existing = existing_po_lookup[key]
# # #             if self._placeholders_are_valid(msgid, existing):
# # #                 memory[msgid] = existing
# # #                 return existing, "Existing"

# # #         trans = self._fallback_translate(memory, msgid, target_lang)
# # #         return trans, "Machine"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang, "nplurals=2; plural=(n != 1);")

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir, existing_translations=None):
# # #         self._display_status("Starting Translation")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path

# # #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# # #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# # #         if not self.target_languages:
# # #             self._display_error("No valid languages")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         os.makedirs(output_dir, exist_ok=True)

# # #         try:
# # #             pot_file = polib.pofile(pot_path)
# # #             glossary = self._parse_glossary_csv(csv_path) if csv_path and os.path.exists(csv_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(zip_path) if zip_path and os.path.exists(zip_path) else {}

# # #             for target_language in self.target_languages:
# # #                 memory = self._load_memory(project_name, target_language)
# # #                 po = polib.POFile()
# # #                 po.metadata = {
# # #                     'Project-Id-Version': '1.0',
# # #                     'PO-Revision-Date': datetime.utcnow().strftime('%Y-%m-%d %H:%M+0000'),
# # #                     'Language': target_language,
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(output_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     if existing_translations and target_language in existing_translations:
# # #                         key = f"{entry.msgctxt}|||{entry.msgid}" if entry.msgctxt else entry.msgid
# # #                         if key in existing_translations[target_language]:
# # #                             po.append(polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr=existing_translations[target_language][key],
# # #                                 msgctxt=entry.msgctxt
# # #                             ))
# # #                             continue

# # #                     if entry.msgid_plural:
# # #                         po.append(polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural={0: self._fallback_translate(memory, entry.msgid, target_language)}
# # #                         ))
# # #                         continue

# # #                     trans, _ = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                     po.append(polib.POEntry(msgid=entry.msgid, msgstr=trans, msgctxt=entry.msgctxt))

# # #                 out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)
# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Error: {e}")
# # #             import traceback
# # #             traceback.print_exc()
# # #             return False



# # # # localization_logic.py
# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator
# # # import re
# # # import time
# # # import json
# # # import logging
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # # === LOGGING SETUP ===
# # # logger = logging.getLogger(__name__)
# # # logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None


# # # class _Translator:
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError


# # # class GoogleTranslatorEngine(_Translator):
# # #     _SEP = "\u2063"

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         try:
# # #             out = translator.translate(joined)
# # #             if isinstance(out, list):
# # #                 return [str(x) for x in out]
# # #             parts = str(out).split(self._SEP)
# # #             return parts if len(parts) == len(texts) else [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]
# # #         except Exception as e:
# # #             logger.warning("GoogleTranslatorEngine batch failed: %s", e)
# # #             return [str(_GoogleTranslator(source='auto', target=target_lang).translate(t)) for t in texts]


# # # # MASTER LIST OF SUPPORTED LANGUAGES (FOR VALIDATION)
# # # SUPPORTED_LANGUAGES = [
# # #     'en', 'en-us', 'en-gb', 'en-ca', 'en-au', 'en-nz', 'en-ng', 'en-za', 'en-gh',
# # #     'es', 'es-ar', 'es-mx', 'es-cl', 'es-co', 'es-pe',
# # #     'fr', 'fr-ca',
# # #     'pt', 'pt-br',
# # #     'de', 'it', 'nl', 'nl-be', 'pl', 'ru', 'ar', 'ar-eg', 'ja', 'ko',
# # #     'id', 'hi', 'ne', 'th', 'tl', 'sw', 'af', 'sv', 'no', 'da', 'fi', 'yo'
# # # ]


# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # Language mappings
# # #         self.lang_map = {code: name for code, name in settings.LANGUAGES}
# # #         self.base_map = {
# # #             'en-us': 'en', 'en-gb': 'en', 'en-ca': 'en', 'en-au': 'en', 'en-nz': 'en',
# # #             'en-ng': 'en', 'en-za': 'en', 'en-gh': 'en',
# # #             'es-ar': 'es', 'es-mx': 'es', 'es-cl': 'es', 'es-co': 'es', 'es-pe': 'es',
# # #             'fr-ca': 'fr',
# # #             'pt-br': 'pt',
# # #             'nl-be': 'nl',
# # #             'ar-eg': 'ar',
# # #         }

# # #         # Google Translator language codes + 'in' alias for Indonesian
# # #         self.google_lang_map = {
# # #             'en': 'en', 'en-us': 'en', 'en-gb': 'en', 'en-ca': 'en', 'en-au': 'en', 'en-nz': 'en',
# # #             'en-ng': 'en', 'en-za': 'en', 'en-gh': 'en',
# # #             'es': 'es', 'es-ar': 'es', 'es-mx': 'es', 'es-cl': 'es', 'es-co': 'es', 'es-pe': 'es',
# # #             'fr': 'fr', 'fr-ca': 'fr',
# # #             'pt': 'pt', 'pt-br': 'pt',
# # #             'de': 'de',
# # #             'it': 'it',
# # #             'nl': 'nl', 'nl-be': 'nl',
# # #             'pl': 'pl',
# # #             'ru': 'ru',
# # #             'ar': 'ar', 'ar-eg': 'ar',
# # #             'ja': 'ja',
# # #             'ko': 'ko',
# # #             'id': 'id', 'in': 'id',
# # #             'hi': 'hi',
# # #             'ne': 'ne',
# # #             'th': 'th',
# # #             'tl': 'tl',
# # #             'sw': 'sw',
# # #             'af': 'af',
# # #             'sv': 'sv',
# # #             'no': 'no',
# # #             'da': 'da',
# # #             'fi': 'fi',
# # #             'yo': 'yo',
# # #         }

# # #         # Regex
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         # === "%s min read" RULES (ALL LANGUAGES) ===
# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "en": "%s min read", "en-us": "%s min read", "en-gb": "%s min read", "en-ca": "%s min read",
# # #                 "en-au": "%s min read", "en-nz": "%s min read", "en-ng": "%s min read", "en-za": "%s min read", "en-gh": "%s min read",
# # #                 "es": "%s min de lectura", "es-ar": "%s min de lectura", "es-mx": "%s min de lectura",
# # #                 "es-cl": "%s min de lectura", "es-co": "%s min de lectura", "es-pe": "%s min de lectura",
# # #                 "fr": "%s min de lecture", "fr-ca": "%s min de lecture",
# # #                 "pt": "%s min de leitura", "pt-br": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen", "nl-be": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "ru": "%s мин. чтения",
# # #                 "hi": "%s मिनट पढ़ें",
# # #                 "ne": "%s मिनेट पढाइ",
# # #                 "ar": "قراءة في %s دقيقة", "ar-eg": "قراءة في %s دقيقة",
# # #                 "ja": "%s分で読めます",
# # #                 "ko": "%s분 읽기",
# # #                 "id": "%s menit baca",
# # #                 "th": "%s นาที อ่าน",
# # #                 "tl": "%s min basahin",
# # #                 "sw": "%s dakika kusoma",
# # #                 "af": "%s min gelees",
# # #                 "sv": "%s min läsning",
# # #                 "no": "%s min lesing",
# # #                 "da": "%s min læsning",
# # #                 "fi": "%s min lukeminen",
# # #                 "yo": "%s min kika",
# # #             }
# # #         }

# # #         # === PLURAL TEMPLATES ===
# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-us": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-gb": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-ca": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-au": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-nz": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-ng": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-za": {"one": "%s min read", "other": "%s mins read"},
# # #                 "en-gh": {"one": "%s min read", "other": "%s mins read"},
# # #                 "es": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-ar": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-mx": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-cl": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-co": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "es-pe": {"one": "%s min de lectura", "other": "%s min de lectura"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "fr-ca": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "pt": {"one": "%s min de leitura", "other": "%s min de leitura"},
# # #                 "pt-br": {"one": "%s min de leitura", "other": "%s min de leitura"},
# # #                 "de": {"one": "%s Min. Lesezeit", "other": "%s Min. Lesezeit"},
# # #                 "it": {"one": "%s min di lettura", "other": "%s min di lettura"},
# # #                 "nl": {"one": "%s min gelezen", "other": "%s min gelezen"},
# # #                 "nl-be": {"one": "%s min gelezen", "other": "%s min gelezen"},
# # #                 "pl": {"one": "%s min czytania", "few": "%s min czytania", "many": "%s min czytania", "other": "%s min czytania"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "hi": {"one": "%s मिनट पढ़ें", "other": "%s मिनट पढ़ें"},
# # #                 "ne": {"one": "%s मिनेट पढाइ", "other": "%s मिनेट पढाइ"},
# # #                 "ar": {"zero": "قراءة في 0 دقيقة", "one": "قراءة في دقيقة %s", "two": "قراءة في دقيقتين %s", "few": "قراءة في %s دقائق", "many": "قراءة في %s دقيقة", "other": "قراءة في %s دقيقة"},
# # #                 "ar-eg": {"zero": "قراءة في 0 دقيقة", "one": "قراءة في دقيقة %s", "two": "قراءة في دقيقتين %s", "few": "قراءة في %s دقائق", "many": "قراءة في %s دقيقة", "other": "قراءة في %s دقيقة"},
# # #                 "ja": {"other": "%s分で読めます"},
# # #                 "ko": {"other": "%s분 읽기"},
# # #                 "id": {"other": "%s menit baca"},
# # #                 "th": {"other": "%s นาที อ่าน"},
# # #                 "tl": {"one": "%s min basahin", "other": "%s min basahin"},
# # #                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
# # #                 "af": {"one": "%s min gelees", "other": "%s min gelees"},
# # #                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
# # #                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
# # #                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
# # #                 "fi": {"other": "%s min lukeminen"},
# # #                 "yo": {"one": "%s min kika", "other": "%s min kika"},
# # #             }
# # #         }

# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {"new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0}
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# # #         # === PLURAL FORMS (ALL LANGUAGES) ===
# # #         self.plural_forms_header = {}
# # #         for code, _ in settings.LANGUAGES:
# # #             base = code.split('-')[0]
# # #             if base in ['ja', 'ko', 'th', 'id', 'fi']:
# # #                 self.plural_forms_header[code] = "nplurals=1; plural=0;"
# # #             elif base in ['tl', 'sw']:
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n > 1);"
# # #             elif base in ['en', 'es', 'de', 'it', 'nl', 'hi', 'ne', 'af', 'sv', 'no', 'da', 'yo']:
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n != 1);"
# # #             elif base == 'fr':
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n > 1);"
# # #             elif base == 'pt':
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n > 1);"
# # #             elif base == 'pl':
# # #                 self.plural_forms_header[code] = "nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);"
# # #             elif base == 'ru':
# # #                 self.plural_forms_header[code] = "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);"
# # #             elif base == 'ar':
# # #                 self.plural_forms_header[code] = "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 && n%100<=10?3 : n%100>=11 && n%100<=99?4 : 5);"
# # #             else:
# # #                 self.plural_forms_header[code] = "nplurals=2; plural=(n != 1);"

# # #     def _get_base_lang(self, lang):
# # #         return self.base_map.get(lang, lang.split('-')[0] if '-' in lang else lang)

# # #     def _get_google_lang(self, lang):
# # #         return self.google_lang_map.get(lang, self.google_lang_map.get(self._get_base_lang(lang), 'en'))

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception as e:
# # #                 logger.warning("Failed to load memory for %s: %s", lang, e)
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             logger.error("Failed to save memory for %s: %s", lang, e)

# # #     def _display_status(self, message):
# # #         logger.info(message)
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         logger.error(message)
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error: {e}")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         return glossary_lookup.get(key)

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned = entry.msgstr
# # #                                 if cleaned:
# # #                                     cleaned = self._normalize_placeholders(cleaned)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned):
# # #                                         existing_po_lookup[key] = self._clean_translated_text(cleaned)
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = self.printf_placeholder_regex.findall(text) + self.icu_placeholder_regex.findall(text)
# # #         ph += self.quoted_printf_regex.findall(text)
# # #         return list(dict.fromkeys([x[0] if isinstance(x, tuple) else x for x in ph]))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             return set(self._collect_placeholders(original)) == set(self._collect_placeholders(translated))
# # #         except Exception:
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         to_protect = self._collect_placeholders(text) + self.html_tag_regex.findall(text)
# # #         to_protect = list(dict.fromkeys(to_protect))
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         return text.strip()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         base_lang = self._get_base_lang(target_lang)
# # #         if msgid in self.translation_rules_plural_templates:
# # #             rule = self.translation_rules_plural_templates[msgid].get(target_lang) or self.translation_rules_plural_templates[msgid].get(base_lang)
# # #             if rule and plural_category and plural_category in rule:
# # #                 return rule[plural_category]
# # #         if msgid in self.translation_rules:
# # #             return self.translation_rules[msgid].get(target_lang) or self.translation_rules[msgid].get(base_lang)
# # #         return None

# # #     def _translate_with_retry(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         google_lang = self._get_google_lang(target_lang)
# # #         for attempt in range(3):
# # #             try:
# # #                 res = self.translator_engine.translate(texts, google_lang)
# # #                 if isinstance(res, list) and len(res) == len(texts):
# # #                     return res
# # #                 if isinstance(res, str):
# # #                     parts = res.split(GoogleTranslatorEngine._SEP)
# # #                     if len(parts) == len(texts):
# # #                         return parts
# # #                 logger.info("Translator returned unexpected result, falling back to per-item translate")
# # #                 break
# # #             except Exception as e:
# # #                 logger.warning("Batch translate attempt %d failed for %s: %s", attempt + 1, target_lang, e)
# # #                 time.sleep(1 + attempt)
# # #         out = []
# # #         for t in texts:
# # #             for attempt in range(3):
# # #                 try:
# # #                     val = _GoogleTranslator(source='auto', target=google_lang).translate(t)
# # #                     out.append(val)
# # #                     time.sleep(0.8)
# # #                     break
# # #                 except Exception as e:
# # #                     logger.warning("Per-item translate failed (attempt %d) for lang %s: %s", attempt + 1, target_lang, e)
# # #                     time.sleep(1.2)
# # #             else:
# # #                 logger.error("Giving up translating string for lang %s; returning original text", target_lang)
# # #                 out.append(t)
# # #         return out

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         if text in memory:
# # #             return memory[text]
# # #         protected, pmap = self._protect_markers(text)
# # #         google_lang = self._get_google_lang(target_lang)
# # #         try:
# # #             result = self.translator_engine.translate([protected], google_lang)
# # #             trans = result[0] if isinstance(result, list) else str(result)
# # #             time.sleep(0.9)
# # #             trans = self._restore_markers(trans, pmap)
# # #             trans = self._clean_translated_text(trans)
# # #             memory[text] = trans
# # #             return trans
# # #         except Exception as e:
# # #             logger.exception("Fallback translation failed for lang %s: %s", target_lang, e)
# # #             try:
# # #                 direct = _GoogleTranslator(source='auto', target=google_lang).translate(protected)
# # #                 direct = self._restore_markers(direct, pmap)
# # #                 direct = self._clean_translated_text(direct)
# # #                 memory[text] = direct
# # #                 return direct
# # #             except Exception as e2:
# # #                 logger.exception("Direct translator also failed: %s", e2)
# # #                 return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key = (msgid, msgctxt)

# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             memory[msgid] = custom
# # #             return custom, "Custom"

# # #         if key in glossary_lookup:
# # #             gloss = glossary_lookup[key]
# # #             if self._placeholders_are_valid(msgid, gloss):
# # #                 memory[msgid] = gloss
# # #                 return gloss, "Glossary"

# # #         if key in existing_po_lookup:
# # #             existing = existing_po_lookup[key]
# # #             if self._placeholders_are_valid(msgid, existing):
# # #                 memory[msgid] = existing
# # #                 return existing, "Existing"

# # #         trans = self._fallback_translate(memory, msgid, target_lang)
# # #         return trans, "Machine"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang, "nplurals=2; plural=(n != 1);")

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir, existing_translations=None):
# # #         self._display_status("Starting Translation")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path

# # #         valid_langs = [lang for lang in target_langs if lang in SUPPORTED_LANGUAGES and lang in [l[0] for l in settings.LANGUAGES]]
# # #         self.target_languages = valid_langs
# # #         if not self.target_languages:
# # #             self._display_error("No valid languages")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         os.makedirs(output_dir, exist_ok=True)

# # #         try:
# # #             pot_file = polib.pofile(pot_path)
# # #             glossary = self._parse_glossary_csv(csv_path) if csv_path and os.path.exists(csv_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(zip_path) if zip_path and os.path.exists(zip_path) else {}

# # #             for target_language in self.target_languages:
# # #                 memory = self._load_memory(project_name, target_language)
# # #                 po = polib.POFile()
# # #                 po.metadata = {
# # #                     'Project-Id-Version': '1.0',
# # #                     'PO-Revision-Date': datetime.utcnow().strftime('%Y-%m-%d %H:%M+0000'),
# # #                     'Language': target_language,
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(output_dir, f"{target_language}-{version}.po")):
# # #                     version += 1

# # #                 for entry in pot_file:
# # #                     if not entry.msgid:
# # #                         continue

# # #                     if existing_translations and target_language in existing_translations:
# # #                         key = f"{entry.msgctxt}|||{entry.msgid}" if entry.msgctxt else entry.msgid
# # #                         if key in existing_translations[target_language]:
# # #                             po.append(polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr=existing_translations[target_language][key],
# # #                                 msgctxt=entry.msgctxt
# # #                             ))
# # #                             continue

# # #                     if entry.msgid_plural:
# # #                         one = self._fallback_translate(memory, entry.msgid, target_language)
# # #                         other = self._fallback_translate(memory, entry.msgid_plural, target_language)
# # #                         po.append(polib.POEntry(
# # #                             msgid=entry.msgid,
# # #                             msgid_plural=entry.msgid_plural,
# # #                             msgstr_plural={0: one, 1: other}
# # #                         ))
# # #                         continue

# # #                     trans, _ = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                     po.append(polib.POEntry(msgid=entry.msgid, msgstr=trans, msgctxt=entry.msgctxt))

# # #                 out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
# # #                 out_mo = out_po.replace('.po', '.mo')
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)
# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Error: {e}")
# # #             import traceback
# # #             traceback.print_exc()
# # #             return False
# # #try only
# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None

# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError

# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# # #     _SEP = "\u2063"  # Invisible Separator

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         out = translator.translate(joined)
# # #         if isinstance(out, list):
# # #             return [str(x) for x in out]
# # #         parts = str(out).split(self._SEP)
# # #         if len(parts) != len(texts):
# # #             parts = []
# # #             for t in texts:
# # #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# # #         return parts

# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)


# # #         # New:HTML entities that must be untouched
# # #         self.NON_TRANSLATABLE_ENTITIES ={
# # #             "&copy;", "&COPY;", "©",
# # #             "&reg;", "&REG;", "®",
# # #             "&trade;", "&TRADE;", "™",
# # #         }

# # #         # Placeholder regexes
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #             }
# # #         }

# # #         self.memory_storage_limit_mb = 100
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0,
# # #             "modified": 0,
# # #             "unchanged": 0,
# # #             "reused": 0,
# # #             "fuzzy": 0,
# # #             "failed": 0,
# # #             "translated": 0,
# # #         }
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()
# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #             "id": "nplurals=1; plural=0;",          # Indonesian – no plural
# # #             "th": "nplurals=1; plural=0;",          # Thai – no plural
# # #             "tl": "nplurals=2; plural=(n != 1);",   # Filipino – 2 forms
# # #             "ko": "nplurals=1; plural=0;",          # Korean – no plural
# # #             "en-gb": "nplurals=2; plural=(n != 1);",# UK English – same as generic en
# # #         }

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         """CSV columns: Original String, Translated String, Context (optional, regex allowed)."""
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# # #         self._display_error("All encoding attempts failed for glossary CSV.")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key = (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #             if orig == msgid and ctx:
# # #                 try:
# # #                     if re.search(ctx, msgctxt or ''):
# # #                         return trans
# # #                 except re.error:
# # #                     continue
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = [
# # #             "Error 500",
# # #             "That’s an error",
# # #             "There was an error",
# # #             "<html", "</html>", "<body>", "</body>",
# # #             "Please try again later",
# # #         ]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         outputs: List[str] = [None] * len(texts)
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #                 #small time delay here
# # #                 time.sleep(0.3)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]

# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         try:
# # #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #             translated = self._restore_markers(translated_protected, placeholder_map)
# # #             translated = self._clean_translated_text(translated)
# # #             if not self._is_valid_translation(translated):
# # #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #                 return text
# # #             self._cache[key] = translated
# # #             self._update_memory(memory, text, translated)
# # #             return translated
# # #         except exceptions.NotValidPayload as e:
# # #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# # #             return text
# # #         except Exception as e:
# # #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# # #             return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''
# # #         key_ctxt = (msgid, msgctxt)

# # #         #----- NEW: PROTECTED ENTITIES -----
# # #         if self._contains_protected_entity(msgid):
# # #             #keep the orginal string, count it as "reused" (no MT call)
# # #             self._counts["reused"]+= 1
# # #             return msgid, "Protected Entity"

# # #         # Custom rules (non-plural)
# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         # Glossary (context-aware)
# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         # Existing PO reuse
# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         # MT fallback
# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc is not None:
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         idx_map: List[str] = []
# # #         if npl == 1:
# # #             idx_map = ["other"]
# # #         elif npl == 2:
# # #             idx_map = ["one", "other"]
# # #         elif npl == 3:
# # #             pref = ["one", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         elif npl == 4:
# # #             pref = ["one", "two", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         else:
# # #             pref = ["zero", "one", "two", "few", "many", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {
# # #                 "msgctxt": e.msgctxt or '',
# # #                 "msgid": e.msgid or '',
# # #                 "msgid_plural": e.msgid_plural or ''
# # #             }
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {
# # #             "msgctxt": entry.msgctxt or '',
# # #             "msgid": entry.msgid,
# # #             "msgid_plural": entry.msgid_plural or '',
# # #             "target_lang": target_lang,
# # #             "status": status,
# # #             "issues": ",".join(issues)
# # #         }
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # #         self._display_status("Starting Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# # #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# # #         if not self.target_languages:
# # #             self._display_error("No valid target languages provided.")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         project_dir = output_dir
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         try:
# # #             if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # #                 self._display_error("POT file not found.")
# # #                 return False

# # #             pot_file = polib.pofile(self.pot_file_path)

# # #             snapshot_path = self._get_snapshot_file_path(project_name)
# # #             prev_snap = {}
# # #             if os.path.exists(snapshot_path):
# # #                 try:
# # #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                         prev_snap = json.load(f)
# # #                 except Exception:
# # #                     prev_snap = {}
# # #             new_snap = self._snapshot_from_pot(pot_file)
# # #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# # #             with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #                 json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #             glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #             entry_status: Dict[polib.POEntry, str] = {}
# # #             for e in pot_file:
# # #                 key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #                 status = diff_map.get(key, "new")
# # #                 entry_status[e] = status
# # #                 self._counts[status] += 1

# # #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# # #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# # #             os.makedirs(report_dir, exist_ok=True)

# # #             for target_language in self.target_languages:
# # #                 self._qa_rows = []
# # #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #                 memory = self._load_memory(project_name, target_language)
# # #                 self._display_status(f"Translating into {target_language}…")
# # #                 po = polib.POFile()
# # #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # #                 po.metadata = {
# # #                     'Project-Id-Version': 'Colab Free',
# # #                     'POT-Creation-Date': now,
# # #                     'PO-Revision-Date': now,
# # #                     'Language': target_language,
# # #                     'MIME-Version': '1.0',
# # #                     'Content-Type': 'text/plain; charset=UTF-8',
# # #                     'Content-Transfer-Encoding': '8bit',
# # #                     'X-Generator': 'Colab Tool',
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 # Determine version based on existing files
# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1
# # #                 existing_po_path = os.path.join(project_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

# # #                 # Reuse existing PO if available and .pot hasn't changed
# # #                 if existing_po_path and self._diff_snapshots(prev_snap, new_snap) is None:
# # #                     po = polib.pofile(existing_po_path)
# # #                     self._counts["reused"] += len(po)
# # #                     self._display_status(f"Reusing existing translation from {existing_po_path}")
# # #                 else:
# # #                     # Process new translation
# # #                     for entry in pot_file:
# # #                         if not entry.msgid:
# # #                             continue
# # #                         status = entry_status.get(entry, "new")
# # #                         try:
# # #                             if entry.msgid_plural:
# # #                                 msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                                 new_entry = polib.POEntry(
# # #                                     msgid=entry.msgid,
# # #                                     msgid_plural=entry.msgid_plural,
# # #                                     msgstr_plural=msgstr_plural,
# # #                                     msgctxt=entry.msgctxt,
# # #                                     occurrences=entry.occurrences,
# # #                                     comment=entry.comment,
# # #                                     tcomment=entry.tcomment
# # #                                 )
# # #                                 if status == "modified":
# # #                                     new_entry.flags.append("fuzzy")
# # #                                     self._counts["fuzzy"] += 1
# # #                                 po.append(new_entry)
# # #                                 for i, s in msgstr_plural.items():
# # #                                     self._qa_check(entry, s, status, target_language)
# # #                                 continue

# # #                             translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr=translated_msgstr,
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # #                                 new_entry.flags.append("fuzzy")
# # #                                 self._counts["fuzzy"] += 1
# # #                             if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                                 self._counts["reused"] += 1
# # #                             po.append(new_entry)
# # #                             self._qa_check(entry, translated_msgstr, status, target_language)
# # #                         except Exception as e:
# # #                             self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr='',
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["failed"] += 1
# # #                             po.append(new_entry)

# # #                 # Set output paths with current version
# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")

# # #                 # Save the PO and MO files
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# # #                 report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# # #                 report = {
# # #                     "language": target_language,
# # #                     "generated_at": timestamp,
# # #                     "counts": dict(self._counts),
# # #                     "rows": self._qa_rows,
# # #                 }
# # #                 try:
# # #                     with open(report_json, 'w', encoding='utf-8') as f:
# # #                         json.dump(report, f, ensure_ascii=False, indent=2)
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write JSON report: {e}")
# # #                 try:
# # #                     if self._qa_rows:
# # #                         headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                         with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                             w = csv.DictWriter(f, fieldnames=headers)
# # #                             w.writeheader()
# # #                             for r in self._qa_rows:
# # #                                 w.writerow({k: r.get(k, "") for k in headers})
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write CSV report: {e}")

# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Unexpected error during setup or file processing: {e}")
# # #             return False



# # #best code till now
# # # import polib
# # # import csv
# # # import zipfile
# # # import os
# # # import shutil
# # # from datetime import datetime
# # # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # # import re
# # # from charset_normalizer import from_path
# # # import time
# # # import json
# # # from typing import Dict, Tuple, List, Optional
# # # from django.conf import settings

# # # try:
# # #     from babel.core import Locale
# # #     from babel.plural import PluralRule
# # # except ImportError:
# # #     Locale = None
# # #     PluralRule = None

# # # class _Translator:
# # #     """Pluggable translator interface."""
# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         raise NotImplementedError

# # # class GoogleTranslatorEngine(_Translator):
# # #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# # #     _SEP = "\u2063"  # Invisible Separator

# # #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# # #         if not texts:
# # #             return []
# # #         joined = self._SEP.join(texts)
# # #         translator = _GoogleTranslator(source='auto', target=target_lang)
# # #         out = translator.translate(joined)
# # #         if isinstance(out, list):
# # #             return [str(x) for x in out]
# # #         parts = str(out).split(self._SEP)
# # #         if len(parts) != len(texts):
# # #             parts = []
# # #             for t in texts:
# # #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# # #         return parts

# # # class ColabLocalizationTool:
# # #     def __init__(self, memory_base_dir: str = None):
# # #         self.pot_file_path = None
# # #         self.zip_file_path = None
# # #         self.csv_file_path = None
# # #         self.target_languages: List[str] = []
# # #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# # #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# # #         os.makedirs(self.memory_base_dir, exist_ok=True)

# # #         # --- NON-TRANSLATABLE ENTITIES (NEVER TOUCH THESE) ---
# # #         self.NON_TRANSLATABLE_ENTITIES = {
# # #             "&copy;", "&COPY;", "©",
# # #             "&reg;", "&REG;", "®",
# # #             "&trade;", "&TRADE;", "™",
# # #             # Add more if needed: "&nbsp;", "&euro;", "€", etc.
# # #         }

# # #         # Placeholder regexes
# # #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# # #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# # #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# # #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# # #         self.translation_rules = {
# # #             "%s min read": {
# # #                 "ja": "%s分で読めます",
# # #                 "it": "%s min di lettura",
# # #                 "nl": "%s min gelezen",
# # #                 "pl": "%s min czytania",
# # #                 "pt": "%s min de leitura",
# # #                 "de": "%s Min. Lesezeit",
# # #                 "ar": "قراءة في %s دقيقة",
# # #                 "fr": "%s min de lecture",
# # #                 "ru": "%s мин. чтения",
# # #                 "en": "%s mins read"
# # #             }
# # #         }

# # #         self.translation_rules_plural_templates = {
# # #             "%s min read": {
# # #                 "en": {"one": "%s min read", "other": "%s mins read"},
# # #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# # #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
# # #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# # #             }
# # #         }

# # #         self.memory_storage_limit_mb = 100
# # #         self._qa_rows: List[Dict] = []
# # #         self._counts = {
# # #             "new": 0,
# # #             "modified": 0,
# # #             "unchanged": 0,
# # #             "reused": 0,
# # #             "fuzzy": 0,
# # #             "failed": 0,
# # #             "translated": 0,
# # #         }
# # #         self._cache: Dict[Tuple[str, str], str] = {}
# # #         self.translator_engine: _Translator = GoogleTranslatorEngine()
# # #         self.plural_forms_header = {
# # #             "en": "nplurals=2; plural=(n != 1);",
# # #             "es": "nplurals=2; plural=(n != 1);",
# # #             "de": "nplurals=2; plural=(n != 1);",
# # #             "fr": "nplurals=2; plural=(n > 1);",
# # #             "pt": "nplurals=2; plural=(n != 1);",
# # #             "hi": "nplurals=2; plural=(n != 1);",
# # #             "ne": "nplurals=2; plural=(n != 1);",
# # #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# # #             "it": "nplurals=2; plural=(n != 1);",
# # #             "ja": "nplurals=1; plural=0;",
# # #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "nl": "nplurals=2; plural=(n != 1);",
# # #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# # #             "zh": "nplurals=1; plural=0;",
# # #             "pt_BR": "nplurals=2; plural=(n > 1);",
# # #             "id": "nplurals=1; plural=0;",
# # #             "th": "nplurals=1; plural=0;",
# # #             "tl": "nplurals=2; plural=(n != 1);",
# # #             "ko": "nplurals=1; plural=0;",
# # #             "en-gb": "nplurals=2; plural=(n != 1);",
# # #         }

# # #     # --- Helper: Check if string contains protected entity ---
# # #     def _contains_protected_entity(self, text: str) -> bool:
# # #         """Return True if any non-translatable entity is in the text."""
# # #         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

# # #     def _get_memory_file_path(self, project_name, lang):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, f"{lang}.json")

# # #     def _get_snapshot_file_path(self, project_name):
# # #         project_dir = os.path.join(self.memory_base_dir, project_name)
# # #         os.makedirs(project_dir, exist_ok=True)
# # #         return os.path.join(project_dir, "_last_snapshot.json")

# # #     def _load_memory(self, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         if os.path.exists(path):
# # #             try:
# # #                 with open(path, 'r', encoding='utf-8') as f:
# # #                     return json.load(f)
# # #             except Exception:
# # #                 return {}
# # #         return {}

# # #     def _save_memory(self, memory, project_name, lang):
# # #         path = self._get_memory_file_path(project_name, lang)
# # #         try:
# # #             with open(path, 'w', encoding='utf-8') as f:
# # #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# # #         except Exception as e:
# # #             self._display_error(f"Failed to save memory file: {e}")

# # #     def _get_memory_translation(self, memory, msgid, target_lang):
# # #         return memory.get(msgid)

# # #     def _update_memory(self, memory, msgid, translation):
# # #         memory[msgid] = translation

# # #     def _display_status(self, message):
# # #         print(f"\n--- STATUS: {message} ---")

# # #     def _display_error(self, message):
# # #         print(f"\n--- ERROR: {message} ---")

# # #     def _parse_glossary_csv(self, csv_file_path):
# # #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# # #         encodings = ['utf-8', 'latin1', 'cp1252']
# # #         for encoding in encodings:
# # #             try:
# # #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# # #                     reader = csv.DictReader(f)
# # #                     for row in reader:
# # #                         orig = (row.get("Original String", "") or "").strip()
# # #                         ctx = (row.get("Context", "") or "").strip()
# # #                         trans = (row.get("Translated String", "") or "").strip()
# # #                         trans = self._normalize_placeholders(trans)
# # #                         glossary_lookup[(orig, ctx)] = trans
# # #                 return glossary_lookup
# # #             except Exception as e:
# # #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# # #         self._display_error("All encoding attempts failed for glossary CSV.")
# # #         return glossary_lookup

# # #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# # #         key =  (msgid, msgctxt or '')
# # #         if key in glossary_lookup:
# # #             return glossary_lookup[key]
# # #         for (orig, ctx), trans in glossary_lookup.items():
# # #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# # #                 return trans
# # #             if orig == msgid and ctx:
# # #                 try:
# # #                     if re.search(ctx, msgctxt or ''):
# # #                         return trans
# # #                 except re.error:
# # #                     continue
# # #         return None

# # #     def _normalize_placeholders(self, msgstr):
# # #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# # #     def _extract_and_parse_existing_pos(self, zip_file_path):
# # #         existing_po_lookup = {}
# # #         if os.path.exists(self.temp_dir):
# # #             shutil.rmtree(self.temp_dir)
# # #         os.makedirs(self.temp_dir)
# # #         try:
# # #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# # #                 for member in zf.namelist():
# # #                     if member.endswith('.po'):
# # #                         zf.extract(member, self.temp_dir)
# # #                         path = os.path.join(self.temp_dir, member)
# # #                         try:
# # #                             po = polib.pofile(path)
# # #                             for entry in po:
# # #                                 key = (entry.msgid, entry.msgctxt or '')
# # #                                 cleaned_msgstr = entry.msgstr
# # #                                 if cleaned_msgstr:
# # #                                     cleaned_msgstr = self._normalize_placeholders(cleaned_msgstr)
# # #                                     if self._placeholders_are_valid(entry.msgid, cleaned_msgstr):
# # #                                         cleaned_msgstr = self._clean_translated_text(cleaned_msgstr)
# # #                                         existing_po_lookup[key] = cleaned_msgstr
# # #                         except Exception as e:
# # #                             self._display_error(f"Error parsing PO: {e}")
# # #         except Exception as e:
# # #             self._display_error(f"Error extracting ZIP: {e}")
# # #         finally:
# # #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# # #         return existing_po_lookup

# # #     def _collect_placeholders(self, text: str) -> List[str]:
# # #         ph = []
# # #         ph += self.printf_placeholder_regex.findall(text)
# # #         ph += self.icu_placeholder_regex.findall(text)
# # #         quoted = self.quoted_printf_regex.findall(text)
# # #         ph += quoted
# # #         normalized = []
# # #         for x in ph:
# # #             if isinstance(x, tuple):
# # #                 normalized.append('{' + x[0] + '}')
# # #             else:
# # #                 normalized.append(x)
# # #         return list(dict.fromkeys(normalized))

# # #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# # #         try:
# # #             orig_ph = self._collect_placeholders(original)
# # #             trans_ph = self._collect_placeholders(translated)
# # #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# # #         except Exception as e:
# # #             self._display_error(f"Placeholder validation failed: {e}")
# # #             return False

# # #     def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
# # #         placeholders = self._collect_placeholders(text)
# # #         tags = self.html_tag_regex.findall(text)
# # #         to_protect = placeholders + tags
# # #         to_protect.sort(key=len, reverse=True)
# # #         placeholder_map = {}
# # #         protected_text = text
# # #         for i, ph in enumerate(to_protect):
# # #             token = f"PH_{i}_TOKEN"
# # #             placeholder_map[token] = ph
# # #             protected_text = protected_text.replace(ph, token)
# # #         return protected_text, placeholder_map

# # #     def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
# # #         for token in list(placeholder_map.keys()):
# # #             escaped = re.escape(token)
# # #             pattern = re.compile(r'\s*'.join(list(escaped)))
# # #             text = pattern.sub(token, text)
# # #         for token, ph in placeholder_map.items():
# # #             text = text.replace(token, ph)
# # #         return text

# # #     def _clean_translated_text(self, text):
# # #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# # #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# # #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# # #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# # #         text = re.sub(r'(“|\()\s+', r'\1', text)
# # #         return text

# # #     def _is_likely_untranslated(self, original_text, translated_text):
# # #         protected_orig, _ = self._protect_markers(original_text)
# # #         protected_trans, _ = self._protect_markers(translated_text)
# # #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# # #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# # #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# # #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# # #         if msgid in self.translation_rules_plural_templates:
# # #             lang_map = self.translation_rules_plural_templates[msgid]
# # #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #             if lang_map and plural_category and plural_category in lang_map:
# # #                 return lang_map[plural_category]
# # #         if msgid in self.translation_rules:
# # #             lang_map = self.translation_rules[msgid]
# # #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# # #         return None

# # #     def _is_valid_translation(self, text):
# # #         error_signs = [
# # #             "Error 500", "That’s an error", "There was an error",
# # #             "<html", "</html>", "<body>", "</body>", "Please try again later",
# # #         ]
# # #         lowered = text.lower()
# # #         return not any(s.lower() in lowered for s in error_signs)

# # #     def _retry(self, func, max_retries=3):
# # #         delay = 1.0
# # #         for i in range(max_retries):
# # #             try:
# # #                 return func()
# # #             except Exception as e:
# # #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# # #                 if i == max_retries - 1:
# # #                     raise
# # #                 time.sleep(delay)
# # #                 delay *= 2

# # #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# # #         outputs: List[str] = [None] * len(texts)
# # #         to_query_idx = []
# # #         to_query = []
# # #         for i, t in enumerate(texts):
# # #             mem = self._get_memory_translation(memory, t, target_lang)
# # #             if mem:
# # #                 outputs[i] = mem
# # #                 continue
# # #             key = (t, target_lang)
# # #             if key in self._cache:
# # #                 outputs[i] = self._cache[key]
# # #             else:
# # #                 to_query_idx.append(i)
# # #                 to_query.append(t)
# # #         if to_query:
# # #             def call():
# # #                 return self.translator_engine.translate(to_query, target_lang)
# # #             translated_list = self._retry(call, max_retries=3)
# # #             for j, out in enumerate(translated_list):
# # #                 idx = to_query_idx[j]
# # #                 outputs[idx] = out
# # #                 self._cache[(texts[idx], target_lang)] = out
# # #                 self._update_memory(memory, texts[idx], out)
# # #                 time.sleep(0.3)
# # #         return [x or "" for x in outputs]

# # #     def _fallback_translate(self, memory, text, target_lang):
# # #         mem = self._get_memory_translation(memory, text, target_lang)
# # #         if mem:
# # #             return mem
# # #         key = (text, target_lang)
# # #         if key in self._cache:
# # #             return self._cache[key]

# # #         protected_text, placeholder_map = self._protect_markers(text)
# # #         try:
# # #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# # #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# # #             translated = self._restore_markers(translated_protected, placeholder_map)
# # #             translated = self._clean_translated_text(translated)
# # #             if not self._is_valid_translation(translated):
# # #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original text as fallback.")
# # #                 return text
# # #             self._cache[key] = translated
# # #             self._update_memory(memory, text, translated)
# # #             return translated
# # #         except exceptions.NotValidPayload as e:
# # #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# # #             return text
# # #         except Exception as e:
# # #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# # #             return text

# # #     def _process_translation(self, memory, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# # #         msgid = pot_entry.msgid
# # #         msgctxt = pot_entry.msgctxt or ''

# # #         # --- PROTECTED ENTITIES: SKIP TRANSLATION ---
# # #         if self._contains_protected_entity(msgid):
# # #             self._counts["reused"] += 1
# # #             return msgid, "Protected Entity"

# # #         # Custom rules
# # #         custom = self._apply_custom_rules(msgid, target_lang)
# # #         if custom:
# # #             self._update_memory(memory, msgid, custom)
# # #             self._counts["translated"] += 1
# # #             return custom, "Custom Rule"

# # #         # Glossary
# # #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# # #         if gloss:
# # #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Glossary (Fuzzy)"
# # #             self._update_memory(memory, msgid, gloss)
# # #             self._counts["reused"] += 1
# # #             return gloss, "Glossary"

# # #         # Existing PO
# # #         key_ctxt = (msgid, msgctxt)
# # #         if key_ctxt in existing_po_lookup:
# # #             existing = existing_po_lookup[key_ctxt]
# # #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# # #                 fb = self._fallback_translate(memory, msgid, target_lang)
# # #                 self._counts["translated"] += 1
# # #                 return fb, "Existing PO (Fuzzy)"
# # #             self._update_memory(memory, msgid, existing)
# # #             self._counts["reused"] += 1
# # #             return existing, "Existing PO"

# # #         # Machine Translation
# # #         fb = self._fallback_translate(memory, msgid, target_lang)
# # #         self._counts["translated"] += 1
# # #         return fb, "Machine Translation"

# # #     def _plural_header_for_lang(self, lang: str) -> str:
# # #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# # #     def _nplurals_from_header(self, header: str) -> int:
# # #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# # #         return int(m.group(1)) if m else 2

# # #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# # #         base = lang.split('_', 1)[0]
# # #         if PluralRule and Locale:
# # #             try:
# # #                 loc = Locale.parse(lang)
# # #             except Exception:
# # #                 try:
# # #                     loc = Locale.parse(base)
# # #                 except Exception:
# # #                     loc = None
# # #             if loc is not None:
# # #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# # #         return ["one", "other"]

# # #     def _pluralize_entry(self, memory, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# # #         # --- PROTECT PLURAL FORMS WITH ENTITIES ---
# # #         if (self._contains_protected_entity(entry.msgid) or
# # #             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
# # #             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
# # #             result: Dict[int, str] = {}
# # #             for i in range(npl):
# # #                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
# # #             self._counts["reused"] += 1
# # #             return result

# # #         # --- Original plural logic ---
# # #         header = self._plural_header_for_lang(target_lang)
# # #         npl = self._nplurals_from_header(header)
# # #         categories = self._plural_categories_for_lang(target_lang)
# # #         if "one" not in categories:
# # #             categories = ["one"] + [c for c in categories if c != "one"]
# # #         if "other" not in categories:
# # #             categories = categories + ["other"]

# # #         templates_by_cat: Dict[str, str] = {}
# # #         for cat in categories:
# # #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# # #             if custom:
# # #                 templates_by_cat[cat] = custom

# # #         if not templates_by_cat:
# # #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# # #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# # #             templates_by_cat["one"] = one_tmpl
# # #             templates_by_cat["other"] = other_tmpl

# # #         idx_map: List[str] = []
# # #         if npl == 1:
# # #             idx_map = ["other"]
# # #         elif npl == 2:
# # #             idx_map = ["one", "other"]
# # #         elif npl == 3:
# # #             pref = ["one", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         elif npl == 4:
# # #             pref = ["one", "two", "few", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref]
# # #         else:
# # #             pref = ["zero", "one", "two", "few", "many", "other"]
# # #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# # #         msgstr_plural: Dict[int, str] = {}
# # #         for i, cat in enumerate(idx_map):
# # #             tmpl = templates_by_cat.get(cat) or templates_by_cat.get("other") or templates_by_cat.get("one") or (entry.msgid_plural or entry.msgid)
# # #             msgstr_plural[i] = tmpl
# # #         return msgstr_plural

# # #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# # #         snap = {}
# # #         for e in pot:
# # #             key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #             snap[key] = {
# # #                 "msgctxt": e.msgctxt or '',
# # #                 "msgid": e.msgid or '',
# # #                 "msgid_plural": e.msgid_plural or ''
# # #             }
# # #         return snap

# # #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# # #         diff = {}
# # #         for k, nv in new.items():
# # #             if k not in old:
# # #                 diff[k] = "new"
# # #             else:
# # #                 ov = old[k]
# # #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# # #                     diff[k] = "modified"
# # #                 else:
# # #                     diff[k] = "unchanged"
# # #         return diff

# # #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# # #         issues = []
# # #         if not translated:
# # #             issues.append("empty")
# # #         if not self._placeholders_are_valid(entry.msgid if not entry.msgid_plural else entry.msgid_plural, translated):
# # #             issues.append("placeholders")
# # #         tags = self.html_tag_regex.findall(translated)
# # #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# # #         closes = sum(1 for t in tags if t.startswith("</"))
# # #         if opens != closes:
# # #             issues.append("html_unbalanced")
# # #         if self._is_likely_untranslated(entry.msgid, translated):
# # #             issues.append("unchanged_like")
# # #         row = {
# # #             "msgctxt": entry.msgctxt or '',
# # #             "msgid": entry.msgid,
# # #             "msgid_plural": entry.msgid_plural or '',
# # #             "target_lang": target_lang,
# # #             "status": status,
# # #             "issues": ",".join(issues)
# # #         }
# # #         self._qa_rows.append(row)
# # #         if "placeholders" in issues or "empty" in issues:
# # #             self._counts["failed"] += 1

# # #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# # #         self._display_status("Starting Localization Tool")

# # #         self.pot_file_path = pot_path
# # #         self.zip_file_path = zip_path
# # #         self.csv_file_path = csv_path
# # #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# # #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# # #         if not self.target_languages:
# # #             self._display_error("No valid target languages provided.")
# # #             return False

# # #         project_name = os.path.splitext(os.path.basename(pot_path))[0]
# # #         project_dir = output_dir
# # #         os.makedirs(project_dir, exist_ok=True)

# # #         try:
# # #             if not self.pot_file_path or not os.path.exists(self.pot_file_path):
# # #                 self._display_error("POT file not found.")
# # #                 return False

# # #             pot_file = polib.pofile(self.pot_file_path)

# # #             snapshot_path = self._get_snapshot_file_path(project_name)
# # #             prev_snap = {}
# # #             if os.path.exists(snapshot_path):
# # #                 try:
# # #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# # #                         prev_snap = json.load(f)
# # #                 except Exception:
# # #                     prev_snap = {}
# # #             new_snap = self._snapshot_from_pot(pot_file)
# # #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# # #             with open(snapshot_path, 'w', encoding='utf-8') as f:
# # #                 json.dump(new_snap, f, ensure_ascii=False, indent=2)

# # #             glossary = self._parse_glossary_csv(self.csv_file_path) if self.csv_file_path and os.path.exists(self.csv_file_path) else {}
# # #             existing = self._extract_and_parse_existing_pos(self.zip_file_path) if self.zip_file_path and os.path.exists(self.zip_file_path) else {}

# # #             entry_status: Dict[polib.POEntry, str] = {}
# # #             for e in pot_file:
# # #                 key = (e.msgctxt or '') + "\u241E" + (e.msgid or '') + "\u241E" + (e.msgid_plural or '')
# # #                 status = diff_map.get(key, "new")
# # #                 entry_status[e] = status
# # #                 self._counts[status] += 1

# # #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# # #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# # #             os.makedirs(report_dir, exist_ok=True)

# # #             for target_language in self.target_languages:
# # #                 self._qa_rows = []
# # #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# # #                 memory = self._load_memory(project_name, target_language)
# # #                 self._display_status(f"Translating into {target_language}…")
# # #                 po = polib.POFile()
# # #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")

# # #                 po.metadata = {
# # #                     'Project-Id-Version': 'Colab Free',
# # #                     'POT-Creation-Date': now,
# # #                     'PO-Revision-Date': now,
# # #                     'Language': target_language,
# # #                     'MIME-Version': '1.0',
# # #                     'Content-Type': 'text/plain; charset=UTF-8',
# # #                     'Content-Transfer-Encoding': '8bit',
# # #                     'X-Generator': 'Colab Tool',
# # #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# # #                 }

# # #                 version = 1
# # #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# # #                     version += 1
# # #                 existing_po_path = os.path.join(project_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

# # #                 if existing_po_path and self._diff_snapshots(prev_snap, new_snap) is None:
# # #                     po = polib.pofile(existing_po_path)
# # #                     self._counts["reused"] += len(po)
# # #                     self._display_status(f"Reusing existing translation from {existing_po_path}")
# # #                 else:
# # #                     for entry in pot_file:
# # #                         if not entry.msgid:
# # #                             continue
# # #                         status = entry_status.get(entry, "new")
# # #                         try:
# # #                             if entry.msgid_plural:
# # #                                 msgstr_plural = self._pluralize_entry(memory, entry, target_language)
# # #                                 new_entry = polib.POEntry(
# # #                                     msgid=entry.msgid,
# # #                                     msgid_plural=entry.msgid_plural,
# # #                                     msgstr_plural=msgstr_plural,
# # #                                     msgctxt=entry.msgctxt,
# # #                                     occurrences=entry.occurrences,
# # #                                     comment=entry.comment,
# # #                                     tcomment=entry.tcomment
# # #                                 )
# # #                                 if status == "modified":
# # #                                     new_entry.flags.append("fuzzy")
# # #                                     self._counts["fuzzy"] += 1
# # #                                 po.append(new_entry)
# # #                                 for i, s in msgstr_plural.items():
# # #                                     self._qa_check(entry, s, status, target_language)
# # #                                 continue

# # #                             translated_msgstr, source = self._process_translation(memory, entry, glossary, existing, target_language)
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr=translated_msgstr,
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             if status == "modified" or "Fuzzy" in source or "Fallback" in source:
# # #                                 new_entry.flags.append("fuzzy")
# # #                                 self._counts["fuzzy"] += 1
# # #                             if status == "unchanged" and source in ("Glossary", "Existing PO"):
# # #                                 self._counts["reused"] += 1
# # #                             po.append(new_entry)
# # #                             self._qa_check(entry, translated_msgstr, status, target_language)
# # #                         except Exception as e:
# # #                             self._display_error(f"Failed to translate string '{entry.msgid[:50]}…'. Error: {e}")
# # #                             new_entry = polib.POEntry(
# # #                                 msgid=entry.msgid,
# # #                                 msgstr='',
# # #                                 msgctxt=entry.msgctxt,
# # #                                 occurrences=entry.occurrences,
# # #                                 comment=entry.comment,
# # #                                 tcomment=entry.tcomment
# # #                             )
# # #                             new_entry.flags.append("fuzzy")
# # #                             self._counts["failed"] += 1
# # #                             po.append(new_entry)

# # #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# # #                 out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")
# # #                 po.save(out_po)
# # #                 po.save_as_mofile(out_mo)

# # #                 report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# # #                 report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# # #                 report = {
# # #                     "language": target_language,
# # #                     "generated_at": timestamp,
# # #                     "counts": dict(self._counts),
# # #                     "rows": self._qa_rows,
# # #                 }
# # #                 try:
# # #                     with open(report_json, 'w', encoding='utf-8') as f:
# # #                         json.dump(report, f, ensure_ascii=False, indent=2)
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write JSON report: {e}")
# # #                 try:
# # #                     if self._qa_rows:
# # #                         headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# # #                         with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# # #                             w = csv.DictWriter(f, fieldnames=headers)
# # #                             w.writeheader()
# # #                             for r in self._qa_rows:
# # #                                 w.writerow({k: r.get(k, "") for k in headers})
# # #                 except Exception as e:
# # #                     self._display_error(f"Failed to write CSV report: {e}")

# # #                 self._save_memory(memory, project_name, target_language)

# # #             self._display_status("Translation complete.")
# # #             return True

# # #         except Exception as e:
# # #             self._display_error(f"Unexpected error during setup or file processing: {e}")
# # #             return False
 


# # # localizationtool/localization_logic.py from 01_copy
# # import polib
# # import csv
# # import zipfile
# # import os
# # import shutil
# # from datetime import datetime
# # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # import re
# # from charset_normalizer import from_path
# # import time
# # import json
# # from typing import Dict, Tuple, List, Optional
# # from django.conf import settings

# # try:
# #     from babel.core import Locale
# #     from babel.plural import PluralRule
# # except ImportError:
# #     Locale = None
# #     PluralRule = None


# # class _Translator:
# #     """Pluggable translator interface."""
# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         raise NotImplementedError


# # class GoogleTranslatorEngine(_Translator):
# #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# #     _SEP = "\u2063"  # Invisible Separator

# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         if not texts:
# #             return []
# #         joined = self._SEP.join(texts)
# #         translator = _GoogleTranslator(source='auto', target=target_lang)
# #         out = translator.translate(joined)
# #         if isinstance(out, list):
# #             return [str(x) for x in out]
# #         parts = str(out).split(self._SEP)
# #         if len(parts) != len(texts):
# #             parts = []
# #             for t in texts:
# #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# #         return parts


# # class ColabLocalizationTool:
# #     def __init__(self, memory_base_dir: str = None):
# #         self.pot_file_path = None
# #         self.zip_file_path = None
# #         self.csv_file_path = None
# #         self.target_languages: List[str] = []
# #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# #         os.makedirs(self.memory_base_dir, exist_ok=True)

# #         # ------------------------------------------------------------------
# #         # NON-TRANSLATABLE ENTITIES – never touch these
# #         # ------------------------------------------------------------------
# #         self.NON_TRANSLATABLE_ENTITIES = {
# #             "&copy;", "&COPY;", "©",
# #             "&reg;", "&REG;", "®",
# #             "&trade;", "&TRADE;", "™",
# #             "&nbsp;", "€", "&euro;", "&lt;", "&gt;", "&amp;"
# #         }

# #         # ------------------------------------------------------------------
# #         # Regexes
# #         # ------------------------------------------------------------------
# #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# #         # ------------------------------------------------------------------
# #         # Fixed translation rules
# #         # ------------------------------------------------------------------
# #         self.translation_rules = {
# #             "%s min read": {
# #                 "ja": "%s分で読めます",
# #                 "it": "%s min di lettura",
# #                 "nl": "%s min gelezen",
# #                 "pl": "%s min czytania",
# #                 "pt": "%s min de leitura",
# #                 "de": "%s Min. Lesezeit",
# #                 "ar": "قراءة في %s دقيقة",
# #                 "fr": "%s min de lecture",
# #                 "ru": "%s мин. чтения",
# #                 "en": "%s mins read"
# #             }
# #         }

# #         self.translation_rules_plural_templates = {
# #             "%s min read": {
# #                 "en": {"one": "%s min read", "other": "%s mins read"},
# #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения",
# #                        "many": "%s мин. чтения", "other": "%s мин. чтения"},
# #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# #             }
# #         }

# #         # ------------------------------------------------------------------
# #         # Misc
# #         # ------------------------------------------------------------------
# #         self.memory_storage_limit_mb = 100
# #         self._qa_rows: List[Dict] = []
# #         self._counts = {
# #             "new": 0, "modified": 0, "unchanged": 0,
# #             "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0,
# #         }
# #         self._cache: Dict[Tuple[str, str], str] = {}
# #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# #         # ------------------------------------------------------------------
# #         # Plural forms (expanded)
# #         # ------------------------------------------------------------------
# #         self.plural_forms_header = {
# #             "en": "nplurals=2; plural=(n != 1);",
# #             "es": "nplurals=2; plural=(n != 1);",
# #             "de": "nplurals=2; plural=(n != 1);",
# #             "fr": "nplurals=2; plural=(n > 1);",
# #             "pt": "nplurals=2; plural=(n != 1);",
# #             "hi": "nplurals=2; plural=(n != 1);",
# #             "ne": "nplurals=2; plural=(n != 1);",
# #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# #             "it": "nplurals=2; plural=(n != 1);",
# #             "ja": "nplurals=1; plural=0;",
# #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "nl": "nplurals=2; plural=(n != 1);",
# #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "zh": "nplurals=1; plural=0;",
# #             "pt_BR": "nplurals=2; plural=(n > 1);",
# #             "id": "nplurals=1; plural=0;",
# #             "th": "nplurals=1; plural=0;",
# #             "tl": "nplurals=2; plural=(n != 1);",
# #             "ko": "nplurals=1; plural=0;",
# #             "en-gb": "nplurals=2; plural=(n != 1);",
# #         }

# #     # ----------------------------------------------------------------------
# #     # Helper: protected-entity detection
# #     # ----------------------------------------------------------------------
# #     def _contains_protected_entity(self, text: str) -> bool:
# #         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

# #     # ----------------------------------------------------------------------
# #     # Memory & snapshot helpers
# #     # ----------------------------------------------------------------------
# #     def _get_memory_file_path(self, project_name, lang):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _get_snapshot_file_path(self, project_name):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, "_last_snapshot.json")

# #     def _get_lang_json_path(self, project_dir, lang):
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _load_memory(self, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         if os.path.exists(path):
# #             try:
# #                 with open(path, 'r', encoding='utf-8') as f:
# #                     return json.load(f)
# #             except Exception as e:
# #                 self._display_error(f"Memory load failed: {e}")
# #                 return {}
# #         return {}

# #     def _save_memory(self, memory, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         try:
# #             with open(path, 'w', encoding='utf-8') as f:
# #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             self._display_error(f"Failed to save memory: {e}")

# #     def _get_memory_translation(self, memory, msgid, target_lang):
# #         return memory.get(msgid)

# #     def _update_memory(self, memory, msgid, translation):
# #         memory[msgid] = translation

# #     # ----------------------------------------------------------------------
# #     # UI helpers
# #     # ----------------------------------------------------------------------
# #     def _display_status(self, message):
# #         print(f"\n--- STATUS: {message} ---")

# #     def _display_error(self, message):
# #         print(f"\n--- ERROR: {message} ---")

# #     # ----------------------------------------------------------------------
# #     # Glossary
# #     # ----------------------------------------------------------------------
# #     def _parse_glossary_csv(self, csv_file_path):
# #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# #         encodings = ['utf-8', 'latin1', 'cp1252']
# #         for encoding in encodings:
# #             try:
# #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# #                     reader = csv.DictReader(f)
# #                     for row in reader:
# #                         orig = (row.get("Original String", "") or "").strip()
# #                         ctx = (row.get("Context", "") or "").strip()
# #                         trans = (row.get("Translated String", "") or "").strip()
# #                         trans = self._normalize_placeholders(trans)
# #                         glossary_lookup[(orig, ctx)] = trans
# #                 return glossary_lookup
# #             except Exception as e:
# #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# #         self._display_error("All encoding attempts failed for glossary CSV.")
# #         return glossary_lookup

# #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# #         key = (msgid, msgctxt or '')
# #         if key in glossary_lookup:
# #             return glossary_lookup[key]
# #         for (orig, ctx), trans in glossary_lookup.items():
# #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# #                 return trans
# #             if orig == msgid and ctx:
# #                 try:
# #                     if re.search(ctx, msgctxt or ''):
# #                         return trans
# #                 except re.error:
# #                     continue
# #         return None

# #     def _normalize_placeholders(self, msgstr):
# #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# #     # ----------------------------------------------------------------------
# #     # Existing PO from ZIP
# #     # ----------------------------------------------------------------------
# #     def _extract_and_parse_existing_pos(self, zip_file_path):
# #         existing_po_lookup = {}
# #         if os.path.exists(self.temp_dir):
# #             shutil.rmtree(self.temp_dir)
# #         os.makedirs(self.temp_dir)
# #         try:
# #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# #                 for member in zf.namelist():
# #                     if member.endswith('.po'):
# #                         zf.extract(member, self.temp_dir)
# #                         path = os.path.join(self.temp_dir, member)
# #                         try:
# #                             po = polib.pofile(path)
# #                             for entry in po:
# #                                 key = (entry.msgid, entry.msgctxt or '')
# #                                 cleaned = entry.msgstr
# #                                 if cleaned:
# #                                     cleaned = self._normalize_placeholders(cleaned)
# #                                     if self._placeholders_are_valid(entry.msgid, cleaned):
# #                                         cleaned = self._clean_translated_text(cleaned)
# #                                         existing_po_lookup[key] = cleaned
# #                         except Exception as e:
# #                             self._display_error(f"Error parsing PO: {e}")
# #         except Exception as e:
# #             self._display_error(f"Error extracting ZIP: {e}")
# #         finally:
# #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# #         return existing_po_lookup

# #     # ----------------------------------------------------------------------
# #     # Placeholder helpers
# #     # ----------------------------------------------------------------------
# #     def _collect_placeholders(self, text: str) -> List[str]:
# #         ph = []
# #         ph += self.printf_placeholder_regex.findall(text)
# #         ph += self.icu_placeholder_regex.findall(text)
# #         quoted = self.quoted_printf_regex.findall(text)
# #         ph += quoted
# #         normalized = []
# #         for x in ph:
# #             if isinstance(x, tuple):
# #                 normalized.append('{' + x[0] + '}')
# #             else:
# #                 normalized.append(x)
# #         return list(dict.fromkeys(normalized))

# #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# #         try:
# #             orig_ph = self._collect_placeholders(original)
# #             trans_ph = self._collect_placeholders(translated)
# #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# #         except Exception as e:
# #             self._display_error(f"Placeholder validation failed: {e}")
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
# #         for token in list(placeholder_map.keys()):
# #             escaped = re.escape(token)
# #             pattern = re.compile(r'\s*'.join(list(escaped)))
# #             text = pattern.sub(token, text)
# #         for token, ph in placeholder_map.items():
# #             text = text.replace(token, ph)
# #         return text

# #     def _clean_translated_text(self, text):
# #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# #         text = re.sub(r'(“|\()\s+', r'\1', text)
# #         return text

# #     def _is_likely_untranslated(self, original_text, translated_text):
# #         protected_orig, _ = self._protect_markers(original_text)
# #         protected_trans, _ = self._protect_markers(translated_text)
# #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# #     # ----------------------------------------------------------------------
# #     # Custom rules
# #     # ----------------------------------------------------------------------
# #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# #         if msgid in self.translation_rules_plural_templates:
# #             lang_map = self.translation_rules_plural_templates[msgid]
# #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #             if lang_map and plural_category and plural_category in lang_map:
# #                 return lang_map[plural_category]
# #         if msgid in self.translation_rules:
# #             lang_map = self.translation_rules[msgid]
# #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #         return None

# #     def _is_valid_translation(self, text):
# #         error_signs = [
# #             "Error 500", "That’s an error", "There was an error",
# #             "<html", "</html>", "<body>", "</body>", "Please try again later",
# #         ]
# #         lowered = text.lower()
# #         return not any(s.lower() in lowered for s in error_signs)

# #     # ----------------------------------------------------------------------
# #     # Retry wrapper
# #     # ----------------------------------------------------------------------
# #     def _retry(self, func, max_retries=3):
# #         delay = 1.0
# #         for i in range(max_retries):
# #             try:
# #                 return func()
# #             except Exception as e:
# #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# #                 if i == max_retries - 1:
# #                     raise
# #                 time.sleep(delay)
# #                 delay *= 2

# #     # ----------------------------------------------------------------------
# #     # Batch translation
# #     # ----------------------------------------------------------------------
# #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# #         outputs: List[str] = [None] * len(texts)
# #         to_query_idx = []
# #         to_query = []
# #         for i, t in enumerate(texts):
# #             mem = self._get_memory_translation(memory, t, target_lang)
# #             if mem:
# #                 outputs[i] = mem
# #                 continue
# #             key = (t, target_lang)
# #             if key in self._cache:
# #                 outputs[i] = self._cache[key]
# #             else:
# #                 to_query_idx.append(i)
# #                 to_query.append(t)
# #         if to_query:
# #             def call():
# #                 return self.translator_engine.translate(to_query, target_lang)
# #             translated_list = self._retry(call, max_retries=3)
# #             for j, out in enumerate(translated_list):
# #                 idx = to_query_idx[j]
# #                 outputs[idx] = out
# #                 self._cache[(texts[idx], target_lang)] = out
# #                 self._update_memory(memory, texts[idx], out)
# #                 time.sleep(0.3)
# #         return [x or "" for x in outputs]

# #     def _fallback_translate(self, memory, text, target_lang):
# #         mem = self._get_memory_translation(memory, text, target_lang)
# #         if mem:
# #             return mem
# #         key = (text, target_lang)
# #         if key in self._cache:
# #             return self._cache[key]

# #         protected_text, placeholder_map = self._protect_markers(text)
# #         try:
# #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# #             translated = self._restore_markers(translated_protected, placeholder_map)
# #             translated = self._clean_translated_text(translated)
# #             if not self._is_valid_translation(translated):
# #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original.")
# #                 return text
# #             self._cache[key] = translated
# #             self._update_memory(memory, text, translated)
# #             return translated
# #         except exceptions.NotValidPayload as e:
# #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# #             return text
# #         except Exception as e:
# #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# #             return text

# #     # ----------------------------------------------------------------------
# #     # Translation decision (singular)
# #     # ----------------------------------------------------------------------
# #     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# #         msgid = pot_entry.msgid
# #         msgctxt = pot_entry.msgctxt or ''

# #         # PRIORITY 1: lang.json (highest)
# #         if msgid in lang_json:
# #             self._counts["reused"] += 1
# #             return lang_json[msgid], "lang.json"

# #         if self._contains_protected_entity(msgid):
# #             self._counts["reused"] += 1
# #             return msgid, "Protected Entity"

# #         custom = self._apply_custom_rules(msgid, target_lang)
# #         if custom:
# #             self._update_memory(memory, msgid, custom)
# #             self._counts["translated"] += 1
# #             return custom, "Custom Rule"

# #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# #         if gloss:
# #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Glossary (Fuzzy)"
# #             self._update_memory(memory, msgid, gloss)
# #             self._counts["reused"] += 1
# #             return gloss, "Glossary"

# #         key_ctxt = (msgid, msgctxt)
# #         if key_ctxt in existing_po_lookup:
# #             existing = existing_po_lookup[key_ctxt]
# #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Existing PO (Fuzzy)"
# #             self._update_memory(memory, msgid, existing)
# #             self._counts["reused"] += 1
# #             return existing, "Existing PO"

# #         fb = self._fallback_translate(memory, msgid, target_lang)
# #         self._counts["translated"] += 1
# #         return fb, "Machine Translation"

# #     # ----------------------------------------------------------------------
# #     # Plural helpers
# #     # ----------------------------------------------------------------------
# #     def _plural_header_for_lang(self, lang: str) -> str:
# #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# #     def _nplurals_from_header(self, header: str) -> int:
# #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# #         return int(m.group(1)) if m else 2

# #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# #         base = lang.split('_', 1)[0]
# #         if PluralRule and Locale:
# #             try:
# #                 loc = Locale.parse(lang)
# #             except Exception:
# #                 try:
# #                     loc = Locale.parse(base)
# #                 except Exception:
# #                     loc = None
# #             if loc is not None:
# #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# #         return ["one", "other"]

# #     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# #         if (self._contains_protected_entity(entry.msgid) or
# #             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
# #             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
# #             result: Dict[int, str] = {}
# #             for i in range(npl):
# #                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
# #             self._counts["reused"] += 1
# #             return result

# #         header = self._plural_header_for_lang(target_lang)
# #         npl = self._nplurals_from_header(header)
# #         categories = self._plural_categories_for_lang(target_lang)
# #         if "one" not in categories:
# #             categories = ["one"] + [c for c in categories if c != "one"]
# #         if "other" not in categories:
# #             categories = categories + ["other"]

# #         templates_by_cat: Dict[str, str] = {}
# #         for cat in categories:
# #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# #             if custom:
# #                 templates_by_cat[cat] = custom

# #         if not templates_by_cat:
# #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# #             templates_by_cat["one"] = one_tmpl
# #             templates_by_cat["other"] = other_tmpl

# #         idx_map: List[str] = []
# #         if npl == 1:
# #             idx_map = ["other"]
# #         elif npl == 2:
# #             idx_map = ["one", "other"]
# #         elif npl == 3:
# #             pref = ["one", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         elif npl == 4:
# #             pref = ["one", "two", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         else:
# #             pref = ["zero", "one", "two", "few", "many", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# #         msgstr_plural: Dict[int, str] = {}
# #         for i, cat in enumerate(idx_map):
# #             tmpl = (templates_by_cat.get(cat) or
# #                     templates_by_cat.get("other") or
# #                     templates_by_cat.get("one") or
# #                     (entry.msgid_plural or entry.msgid))
# #             msgstr_plural[i] = tmpl
# #         return msgstr_plural

# #     # ----------------------------------------------------------------------
# #     # Snapshot & diff
# #     # ----------------------------------------------------------------------
# #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# #         snap = {}
# #         for e in pot:
# #             key = (e.msgctxt or '').strip() + "\u241E" + (e.msgid or '').strip() + "\u241E" + (e.msgid_plural or '').strip()
# #             snap[key] = {
# #                 "msgctxt": (e.msgctxt or '').strip(),
# #                 "msgid": (e.msgid or '').strip(),
# #                 "msgid_plural": (e.msgid_plural or '').strip()
# #             }
# #         return snap

# #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# #         diff = {}
# #         for k, nv in new.items():
# #             if k not in old:
# #                 diff[k] = "new"
# #             else:
# #                 ov = old[k]
# #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# #                     diff[k] = "modified"
# #                 else:
# #                     diff[k] = "unchanged"
# #         return diff

# #     # ----------------------------------------------------------------------
# #     # QA check
# #     # ----------------------------------------------------------------------
# #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# #         issues = []
# #         if not translated:
# #             issues.append("empty")
# #         base = entry.msgid_plural or entry.msgid
# #         if not self._placeholders_are_valid(base, translated):
# #             issues.append("placeholders")
# #         tags = self.html_tag_regex.findall(translated)
# #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# #         closes = sum(1 for t in tags if t.startswith("</"))
# #         if opens != closes:
# #             issues.append("html_unbalanced")
# #         if self._is_likely_untranslated(entry.msgid, translated):
# #             issues.append("unchanged_like")
# #         row = {
# #             "msgctxt": entry.msgctxt or '',
# #             "msgid": entry.msgid,
# #             "msgid_plural": entry.msgid_plural or '',
# #             "target_lang": target_lang,
# #             "status": status,
# #             "issues": ",".join(issues)
# #         }
# #         self._qa_rows.append(row)
# #         if "placeholders" in issues or "empty" in issues:
# #             self._counts["failed"] += 1

# #     # ----------------------------------------------------------------------
# #     # Report helper
# #     # ----------------------------------------------------------------------
# #     def _generate_report(self, target_language, version, timestamp, report_dir, reused_from=None):
# #         report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# #         report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# #         report = {
# #             "language": target_language,
# #             "generated_at": timestamp,
# #             "version": version,
# #             "reused_from": os.path.basename(reused_from) if reused_from else None,
# #             "counts": dict(self._counts),
# #             "rows": self._qa_rows,
# #         }
# #         try:
# #             with open(report_json, 'w', encoding='utf-8') as f:
# #                 json.dump(report, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             self._display_error(f"JSON report failed: {e}")

# #         try:
# #             if self._qa_rows:
# #                 headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# #                 with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# #                     w = csv.DictWriter(f, fieldnames=headers)
# #                     w.writeheader()
# #                     for r in self._qa_rows:
# #                         w.writerow({k: r.get(k, "") for k in headers})
# #         except Exception as e:
# #             self._display_error(f"CSV report failed: {e}")

# #     # ----------------------------------------------------------------------
# #     # MAIN run()
# #     # ----------------------------------------------------------------------
# #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# #         self._display_status("Starting Localization Tool")

# #         self.pot_file_path = pot_path
# #         self.zip_file_path = zip_path
# #         self.csv_file_path = csv_path
# #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# #         if not self.target_languages:
# #             self._display_error("No valid target languages provided.")
# #             return False

# #         # === PROJECT NAME: Strip Django suffix ===
# #         original_filename = getattr(pot_path, 'name', os.path.basename(pot_path))
# #         if '_' in original_filename and original_filename.endswith('.pot'):
# #             original_filename = original_filename.split('_', 1)[0] + '.pot'
# #         project_name = os.path.splitext(original_filename)[0]
# #         self._display_status(f"Project: {project_name} (from {original_filename})")

# #         project_dir = os.path.join(output_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)

# #         try:
# #             if not os.path.exists(self.pot_file_path):
# #                 self._display_error("POT file not found.")
# #                 return False

# #             pot_file = polib.pofile(self.pot_file_path)

# #             # --------------------------------------------------------------
# #             # SNAPSHOT & GLOBAL DIFF
# #             # --------------------------------------------------------------
# #             snapshot_path = self._get_snapshot_file_path(project_name)

# #             # === DEBUG: LOAD SNAPSHOT WITH FULL LOGGING ===
# #             prev_snap = {}
# #             if os.path.exists(snapshot_path):
# #                 self._display_status(f"Snapshot FILE EXISTS: {snapshot_path}")
# #                 try:
# #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# #                         prev_snap = json.load(f)
# #                     self._display_status(f"Snapshot LOADED: {len(prev_snap)} entries")
# #                 except Exception as e:
# #                     self._display_error(f"Snapshot LOAD FAILED: {e}")
# #                     prev_snap = {}
# #             else:
# #                 self._display_status(f"NO SNAPSHOT FOUND: {snapshot_path}")

# #             new_snap = self._snapshot_from_pot(pot_file)
# #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# #             for status in diff_map.values():
# #                 self._counts[status] += 1

# #             # === DEBUG: SAVE & VERIFY SNAPSHOT ===
# #             try:
# #                 os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
# #                 with open(snapshot_path, 'w', encoding='utf-8') as f:
# #                     json.dump(new_snap, f, ensure_ascii=False, indent=2)
# #                 self._display_status(f"Snapshot SAVED: {snapshot_path} ({len(new_snap)} entries)")

# #                 # Verify write
# #                 with open(snapshot_path, 'r', encoding='utf-8') as f:
# #                     test_load = json.load(f)
# #                 if len(test_load) == len(new_snap):
# #                     self._display_status("Snapshot write VERIFIED")
# #                 else:
# #                     self._display_error("Snapshot CORRUPTED after save!")
# #             except Exception as e:
# #                 self._display_error(f"FAILED TO SAVE SNAPSHOT: {e}")
# #                 self._display_error(f"Path: {snapshot_path}")

# #             # --------------------------------------------------------------
# #             # Load glossary & existing PO from ZIP
# #             # --------------------------------------------------------------
# #             glossary = (self._parse_glossary_csv(self.csv_file_path)
# #                         if self.csv_file_path and os.path.exists(self.csv_file_path) else {})
# #             existing_from_zip = (self._extract_and_parse_existing_pos(self.zip_file_path)
# #                                  if self.zip_file_path and os.path.exists(self.zip_file_path) else {})

# #             # --------------------------------------------------------------
# #             # Report folder
# #             # --------------------------------------------------------------
# #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# #             os.makedirs(report_dir, exist_ok=True)

# #             # --------------------------------------------------------------
# #             # PER-LANGUAGE LOOP
# #             # --------------------------------------------------------------
# #             for target_language in self.target_languages:
# #                 self._qa_rows = []
# #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# #                 memory = self._load_memory(project_name, target_language)
# #                 self._display_status(f"Processing {target_language}…")

# #                 # === LOAD lang.json ===
# #                 lang_json_path = self._get_lang_json_path(project_dir, target_language)
# #                 lang_json = {}
# #                 if os.path.exists(lang_json_path):
# #                     try:
# #                         with open(lang_json_path, 'r', encoding='utf-8') as f:
# #                             lang_json = json.load(f)
# #                         self._display_status(f"Loaded {len(lang_json)} strings from {target_language}.json")
# #                     except Exception as e:
# #                         self._display_error(f"Failed to load {target_language}.json: {e}")
# #                 else:
# #                     self._display_status(f"No {target_language}.json — starting fresh")

# #                 version = 1
# #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# #                     version += 1
# #                 existing_po_path = os.path.join(project_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

# #                 # === DEBUG SNAPSHOT COMPARISON ===
# #                 self._display_status(f"Snapshot: prev={len(prev_snap)} entries, new={len(new_snap)} entries")

# #                 # === FULL REUSE WITH ROBUST COMPARISON ===
# #                 if existing_po_path:
# #                     def normalize(snap):
# #                         return {k.strip(): {kk: vv.strip() for kk, vv in v.items()} for k, v in snap.items()}
# #                     if normalize(prev_snap) == normalize(new_snap):
# #                         try:
# #                             po = polib.pofile(existing_po_path)
# #                             entries_count = len([e for e in po if e.msgid])
# #                             self._display_status(f"FULL REUSE: Copying {entries_count} entries from {os.path.basename(existing_po_path)}")

# #                             for entry in po:
# #                                 if not entry.msgid:
# #                                     continue
# #                                 self._counts["reused"] += 1
# #                                 status = "unchanged"
# #                                 if entry.msgid_plural:
# #                                     for form in entry.msgstr_plural.values():
# #                                         self._qa_check(entry, form, status, target_language)
# #                                 else:
# #                                     self._qa_check(entry, entry.msgstr, status, target_language)

# #                             out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                             out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")
# #                             po.save(out_po)
# #                             po.save_as_mofile(out_mo)

# #                             self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                             self._save_memory(memory, project_name, target_language)
# #                             self._display_status(f"Reused entire PO → {out_po}")
# #                             continue

# #                         except Exception as e:
# #                             self._display_error(f"Reuse failed: {e}. Regenerating...")

# #                 # === NORMAL PROCESSING ===
# #                 self._display_status("POT changed or no reuse → translating entries...")
# #                 po = polib.POFile()
# #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
# #                 po.metadata = {
# #                     'Project-Id-Version': 'Colab Free',
# #                     'POT-Creation-Date': now,
# #                     'PO-Revision-Date': now,
# #                     'Language': target_language,
# #                     'MIME-Version': '1.0',
# #                     'Content-Type': 'text/plain; charset=UTF-8',
# #                     'Content-Transfer-Encoding': '8bit',
# #                     'X-Generator': 'Colab Tool',
# #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# #                 }

# #                 for entry in pot_file:
# #                     if not entry.msgid:
# #                         continue

# #                     key = (entry.msgctxt or '').strip() + "\u241E" + (entry.msgid or '').strip() + "\u241E" + (entry.msgid_plural or '').strip()
# #                     status = diff_map.get(key, "new")

# #                     try:
# #                         if entry.msgid_plural:
# #                             msgstr_plural = self._pluralize_entry(memory, lang_json, entry, target_language)
# #                             new_entry = polib.POEntry(
# #                                 msgid=entry.msgid,
# #                                 msgid_plural=entry.msgid_plural,
# #                                 msgstr_plural=msgstr_plural,
# #                                 msgctxt=entry.msgctxt,
# #                                 occurrences=entry.occurrences,
# #                                 comment=entry.comment,
# #                                 tcomment=entry.tcomment
# #                             )
# #                             if status == "modified":
# #                                 new_entry.flags.append("fuzzy")
# #                                 self._counts["fuzzy"] += 1
# #                             po.append(new_entry)
# #                             for s in msgstr_plural.values():
# #                                 self._qa_check(entry, s, status, target_language)
# #                             continue

# #                         translated_msgstr, source = self._process_translation(
# #                             memory, lang_json, entry, glossary, existing_from_zip, target_language
# #                         )
# #                         new_entry = polib.POEntry(
# #                             msgid=entry.msgid,
# #                             msgstr=translated_msgstr,
# #                             msgctxt=entry.msgctxt,
# #                             occurrences=entry.occurrences,
# #                             comment=entry.comment,
# #                             tcomment=entry.tcomment
# #                         )
# #                         if status == "modified" or "Fuzzy" in source:
# #                             new_entry.flags.append("fuzzy")
# #                             self._counts["fuzzy"] += 1
# #                         if status == "unchanged" and source in ("lang.json", "Glossary", "Existing PO", "Protected Entity"):
# #                             self._counts["reused"] += 1
# #                         po.append(new_entry)
# #                         self._qa_check(entry, translated_msgstr, status, target_language)

# #                     except Exception as e:
# #                         self._display_error(f"Failed to process '{entry.msgid[:50]}…': {e}")
# #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr='', flags=['fuzzy']))
# #                         self._counts["failed"] += 1

# #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                 out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")
# #                 po.save(out_po)
# #                 po.save_as_mofile(out_mo)

# #                 # === UPDATE lang.json ===
# #                 current_translations = {}
# #                 for entry in po:
# #                     if entry.msgid and entry.msgstr:
# #                         current_translations[entry.msgid] = entry.msgstr
# #                     if entry.msgid_plural and entry.msgstr_plural:
# #                         for i, msg in entry.msgstr_plural.items():
# #                             key = entry.msgid_plural if i > 0 else entry.msgid
# #                             if msg:
# #                                 current_translations[key] = msg

# #                 lang_json.update(current_translations)

# #                 try:
# #                     with open(lang_json_path, 'w', encoding='utf-8') as f:
# #                         json.dump(lang_json, f, ensure_ascii=False, indent=2, sort_keys=True)
# #                     self._display_status(f"Updated {target_language}.json → {len(current_translations)} strings")
# #                 except Exception as e:
# #                     self._display_error(f"Failed to save {target_language}.json: {e}")

# #                 self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                 self._save_memory(memory, project_name, target_language)

# #             self._display_status("Translation complete with smart reuse.")
# #             return True

# #         except Exception as e:
# #             self._display_error(f"Unexpected error: {e}")
# #             return False



# # localizationtool/localization_logic.py best of the best
# # import polib
# # import csv
# # import zipfile
# # import os
# # import shutil
# # from datetime import datetime
# # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # import re
# # from charset_normalizer import from_path
# # import time
# # import json
# # from typing import Dict, Tuple, List, Optional
# # from django.conf import settings

# # try:
# #     from babel.core import Locale
# #     from babel.plural import PluralRule
# # except ImportError:
# #     Locale = None
# #     PluralRule = None


# # class _Translator:
# #     """Pluggable translator interface."""
# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         raise NotImplementedError


# # class GoogleTranslatorEngine(_Translator):
# #     """Batch-friendly wrapper around deep_translator.GoogleTranslator."""
# #     _SEP = "\u2063"  # Invisible Separator

# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         if not texts:
# #             return []
# #         joined = self._SEP.join(texts)
# #         translator = _GoogleTranslator(source='auto', target=target_lang)
# #         out = translator.translate(joined)
# #         if isinstance(out, list):
# #             return [str(x) for x in out]
# #         parts = str(out).split(self._SEP)
# #         if len(parts) != len(texts):
# #             parts = []
# #             for t in texts:
# #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# #         return parts


# # class ColabLocalizationTool:
# #     def __init__(self, memory_base_dir: str = None):
# #         self.pot_file_path = None
# #         self.zip_file_path = None
# #         self.csv_file_path = None
# #         self.target_languages: List[str] = []
# #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# #         os.makedirs(self.memory_base_dir, exist_ok=True)

# #         # ------------------------------------------------------------------
# #         # NON-TRANSLATABLE ENTITIES – never touch these
# #         # ------------------------------------------------------------------
# #         self.NON_TRANSLATABLE_ENTITIES = {
# #             "&copy;", "&COPY;", "©",
# #             "&reg;", "&REG;", "®",
# #             "&trade;", "&TRADE;", "™",
# #             "&nbsp;", "€", "&euro;", "&lt;", "&gt;", "&amp;"
# #         }

# #         # ------------------------------------------------------------------
# #         # Regexes
# #         # ------------------------------------------------------------------
# #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# #         self.icu_placeholder_regex = re.compile(r"\{\s*([\w\d]+)(?:\s*,[^}]*)?\}")
# #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# #         # ------------------------------------------------------------------
# #         # Fixed translation rules
# #         # ------------------------------------------------------------------
# #         self.translation_rules = {
# #             "%s min read": {
# #                 "ja": "%s分で読めます",
# #                 "it": "%s min di lettura",
# #                 "nl": "%s min gelezen",
# #                 "pl": "%s min czytania",
# #                 "pt": "%s min de leitura",
# #                 "de": "%s Min. Lesezeit",
# #                 "ar": "قراءة في %s دقيقة",
# #                 "fr": "%s min de lecture",
# #                 "ru": "%s мин. чтения",
# #                 "en": "%s mins read"
# #             }
# #         }

# #         self.translation_rules_plural_templates = {
# #             "%s min read": {
# #                 "en": {"one": "%s min read", "other": "%s mins read"},
# #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения",
# #                        "many": "%s мин. чтения", "other": "%s мин. чтения"},
# #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# #             }
# #         }

# #         # ------------------------------------------------------------------
# #         # Misc
# #         # ------------------------------------------------------------------
# #         self.memory_storage_limit_mb = 100
# #         self._qa_rows: List[Dict] = []
# #         self._counts = {
# #             "new": 0, "modified": 0, "unchanged": 0,
# #             "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0,
# #         }
# #         self._cache: Dict[Tuple[str, str], str] = {}
# #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# #         # ------------------------------------------------------------------
# #         # Plural forms (expanded)
# #         # ------------------------------------------------------------------
# #         self.plural_forms_header = {
# #             "en": "nplurals=2; plural=(n != 1);",
# #             "es": "nplurals=2; plural=(n != 1);",
# #             "de": "nplurals=2; plural=(n != 1);",
# #             "fr": "nplurals=2; plural=(n > 1);",
# #             "pt": "nplurals=2; plural=(n != 1);",
# #             "hi": "nplurals=2; plural=(n != 1);",
# #             "ne": "nplurals=2; plural=(n != 1);",
# #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# #             "it": "nplurals=2; plural=(n != 1);",
# #             "ja": "nplurals=1; plural=0;",
# #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "nl": "nplurals=2; plural=(n != 1);",
# #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "zh": "nplurals=1; plural=0;",
# #             "pt_BR": "nplurals=2; plural=(n > 1);",
# #             "id": "nplurals=1; plural=0;",
# #             "th": "nplurals=1; plural=0;",
# #             "tl": "nplurals=2; plural=(n != 1);",
# #             "ko": "nplurals=1; plural=0;",
# #             "en-gb": "nplurals=2; plural=(n != 1);",
# #         }

# #     # ----------------------------------------------------------------------
# #     # Helper: protected-entity detection
# #     # ----------------------------------------------------------------------
# #     def _contains_protected_entity(self, text: str) -> bool:
# #         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

# #     # ----------------------------------------------------------------------
# #     # Memory & snapshot helpers
# #     # ----------------------------------------------------------------------
# #     def _get_memory_file_path(self, project_name, lang):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _get_snapshot_file_path(self, project_name):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, "_last_snapshot.json")

# #     def _get_lang_json_path(self, project_dir, lang):
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _load_memory(self, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         if os.path.exists(path):
# #             try:
# #                 with open(path, 'r', encoding='utf-8') as f:
# #                     return json.load(f)
# #             except Exception as e:
# #                 self._display_error(f"Memory load failed: {e}")
# #                 return {}
# #         return {}

# #     def _save_memory(self, memory, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         try:
# #             with open(path, 'w', encoding='utf-8') as f:
# #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             self._display_error(f"Failed to save memory: {e}")

# #     def _get_memory_translation(self, memory, msgid, target_lang):
# #         return memory.get(msgid)

# #     def _update_memory(self, memory, msgid, translation):
# #         memory[msgid] = translation

# #     # ----------------------------------------------------------------------
# #     # UI helpers
# #     # ----------------------------------------------------------------------
# #     def _display_status(self, message):
# #         print(f"\n--- STATUS: {message} ---")

# #     def _display_error(self, message):
# #         print(f"\n--- ERROR: {message} ---")

# #     # ----------------------------------------------------------------------
# #     # Glossary
# #     # ----------------------------------------------------------------------
# #     def _parse_glossary_csv(self, csv_file_path):
# #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# #         encodings = ['utf-8', 'latin1', 'cp1252']
# #         for encoding in encodings:
# #             try:
# #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# #                     reader = csv.DictReader(f)
# #                     for row in reader:
# #                         orig = (row.get("Original String", "") or "").strip()
# #                         ctx = (row.get("Context", "") or "").strip()
# #                         trans = (row.get("Translated String", "") or "").strip()
# #                         trans = self._normalize_placeholders(trans)
# #                         glossary_lookup[(orig, ctx)] = trans
# #                 return glossary_lookup
# #             except Exception as e:
# #                 self._display_error(f"Glossary parse error with {encoding}: {e}")
# #         self._display_error("All encoding attempts failed for glossary CSV.")
# #         return glossary_lookup

# #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# #         key = (msgid, msgctxt or '')
# #         if key in glossary_lookup:
# #             return glossary_lookup[key]
# #         for (orig, ctx), trans in glossary_lookup.items():
# #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# #                 return trans
# #             if orig == msgid and ctx:
# #                 try:
# #                     if re.search(ctx, msgctxt or ''):
# #                         return trans
# #                 except re.error:
# #                     continue
# #         return None

# #     def _normalize_placeholders(self, msgstr):
# #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# #     # ----------------------------------------------------------------------
# #     # Existing PO from ZIP
# #     # ----------------------------------------------------------------------
# #     def _extract_and_parse_existing_pos(self, zip_file_path):
# #         existing_po_lookup = {}
# #         if os.path.exists(self.temp_dir):
# #             shutil.rmtree(self.temp_dir)
# #         os.makedirs(self.temp_dir)
# #         try:
# #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# #                 for member in zf.namelist():
# #                     if member.endswith('.po'):
# #                         zf.extract(member, self.temp_dir)
# #                         path = os.path.join(self.temp_dir, member)
# #                         try:
# #                             po = polib.pofile(path)
# #                             for entry in po:
# #                                 key = (entry.msgid, entry.msgctxt or '')
# #                                 cleaned = entry.msgstr
# #                                 if cleaned:
# #                                     cleaned = self._normalize_placeholders(cleaned)
# #                                     if self._placeholders_are_valid(entry.msgid, cleaned):
# #                                         cleaned = self._clean_translated_text(cleaned)
# #                                         existing_po_lookup[key] = cleaned
# #                         except Exception as e:
# #                             self._display_error(f"Error parsing PO: {e}")
# #         except Exception as e:
# #             self._display_error(f"Error extracting ZIP: {e}")
# #         finally:
# #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# #         return existing_po_lookup

# #     # ----------------------------------------------------------------------
# #     # Placeholder helpers
# #     # ----------------------------------------------------------------------
# #     def _collect_placeholders(self, text: str) -> List[str]:
# #         ph = []
# #         ph += self.printf_placeholder_regex.findall(text)
# #         ph += self.icu_placeholder_regex.findall(text)
# #         quoted = self.quoted_printf_regex.findall(text)
# #         ph += quoted
# #         normalized = []
# #         for x in ph:
# #             if isinstance(x, tuple):
# #                 normalized.append('{' + x[0] + '}')
# #             else:
# #                 normalized.append(x)
# #         return list(dict.fromkeys(normalized))

# #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# #         try:
# #             orig_ph = self._collect_placeholders(original)
# #             trans_ph = self._collect_placeholders(translated)
# #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# #         except Exception as e:
# #             self._display_error(f"Placeholder validation failed: {e}")
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
# #         for token in list(placeholder_map.keys()):
# #             escaped = re.escape(token)
# #             pattern = re.compile(r'\s*'.join(list(escaped)))
# #             text = pattern.sub(token, text)
# #         for token, ph in placeholder_map.items():
# #             text = text.replace(token, ph)
# #         return text

# #     def _clean_translated_text(self, text):
# #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# #         text = re.sub(r'(“|\()\s+', r'\1', text)
# #         return text

# #     def _is_likely_untranslated(self, original_text, translated_text):
# #         protected_orig, _ = self._protect_markers(original_text)
# #         protected_trans, _ = self._protect_markers(translated_text)
# #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# #     # ----------------------------------------------------------------------
# #     # Custom rules
# #     # ----------------------------------------------------------------------
# #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# #         if msgid in self.translation_rules_plural_templates:
# #             lang_map = self.translation_rules_plural_templates[msgid]
# #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #             if lang_map and plural_category and plural_category in lang_map:
# #                 return lang_map[plural_category]
# #         if msgid in self.translation_rules:
# #             lang_map = self.translation_rules[msgid]
# #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #         return None

# #     def _is_valid_translation(self, text):
# #         error_signs = [
# #             "Error 500", "That’s an error", "There was an error",
# #             "<html", "</html>", "<body>", "</body>", "Please try again later",
# #         ]
# #         lowered = text.lower()
# #         return not any(s.lower() in lowered for s in error_signs)

# #     # ----------------------------------------------------------------------
# #     # Retry wrapper
# #     # ----------------------------------------------------------------------
# #     def _retry(self, func, max_retries=3):
# #         delay = 1.0
# #         for i in range(max_retries):
# #             try:
# #                 return func()
# #             except Exception as e:
# #                 self._display_error(f"Attempt {i+1}/{max_retries} failed: {e}")
# #                 if i == max_retries - 1:
# #                     raise
# #                 time.sleep(delay)
# #                 delay *= 2

# #     # ----------------------------------------------------------------------
# #     # Batch translation
# #     # ----------------------------------------------------------------------
# #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# #         outputs: List[str] = [None] * len(texts)
# #         to_query_idx = []
# #         to_query = []
# #         for i, t in enumerate(texts):
# #             mem = self._get_memory_translation(memory, t, target_lang)
# #             if mem:
# #                 outputs[i] = mem
# #                 continue
# #             key = (t, target_lang)
# #             if key in self._cache:
# #                 outputs[i] = self._cache[key]
# #             else:
# #                 to_query_idx.append(i)
# #                 to_query.append(t)
# #         if to_query:
# #             def call():
# #                 return self.translator_engine.translate(to_query, target_lang)
# #             translated_list = self._retry(call, max_retries=3)
# #             for j, out in enumerate(translated_list):
# #                 idx = to_query_idx[j]
# #                 outputs[idx] = out
# #                 self._cache[(texts[idx], target_lang)] = out
# #                 self._update_memory(memory, texts[idx], out)
# #                 time.sleep(0.3)
# #         return [x or "" for x in outputs]

# #     def _fallback_translate(self, memory, text, target_lang):
# #         mem = self._get_memory_translation(memory, text, target_lang)
# #         if mem:
# #             return mem
# #         key = (text, target_lang)
# #         if key in self._cache:
# #             return self._cache[key]

# #         protected_text, placeholder_map = self._protect_markers(text)
# #         try:
# #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# #             translated = self._restore_markers(translated_protected, placeholder_map)
# #             translated = self._clean_translated_text(translated)
# #             if not self._is_valid_translation(translated):
# #                 self._display_error(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original.")
# #                 return text
# #             self._cache[key] = translated
# #             self._update_memory(memory, text, translated)
# #             return translated
# #         except exceptions.NotValidPayload as e:
# #             self._display_error(f"Invalid payload for '{text}'. Error: {e}")
# #             return text
# #         except Exception as e:
# #             self._display_error(f"Translation failed for '{text}' → '{target_lang}': {e}")
# #             return text

# #     # ----------------------------------------------------------------------
# #     # Translation decision (singular)
# #     # ----------------------------------------------------------------------
# #     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# #         msgid = pot_entry.msgid
# #         msgctxt = pot_entry.msgctxt or ''

# #         # PRIORITY 1: lang.json (highest)
# #         if msgid in lang_json:
# #             self._counts["reused"] += 1
# #             return lang_json[msgid], "lang.json"

# #         if self._contains_protected_entity(msgid):
# #             self._counts["reused"] += 1
# #             return msgid, "Protected Entity"

# #         custom = self._apply_custom_rules(msgid, target_lang)
# #         if custom:
# #             self._update_memory(memory, msgid, custom)
# #             self._counts["translated"] += 1
# #             return custom, "Custom Rule"

# #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# #         if gloss:
# #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Glossary (Fuzzy)"
# #             self._update_memory(memory, msgid, gloss)
# #             self._counts["reused"] += 1
# #             return gloss, "Glossary"

# #         key_ctxt = (msgid, msgctxt)
# #         if key_ctxt in existing_po_lookup:
# #             existing = existing_po_lookup[key_ctxt]
# #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Existing PO (Fuzzy)"
# #             self._update_memory(memory, msgid, existing)
# #             self._counts["reused"] += 1
# #             return existing, "Existing PO"

# #         fb = self._fallback_translate(memory, msgid, target_lang)
# #         self._counts["translated"] += 1
# #         return fb, "Machine Translation"

# #     # ----------------------------------------------------------------------
# #     # Plural helpers
# #     # ----------------------------------------------------------------------
# #     def _plural_header_for_lang(self, lang: str) -> str:
# #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# #     def _nplurals_from_header(self, header: str) -> int:
# #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# #         return int(m.group(1)) if m else 2

# #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# #         base = lang.split('_', 1)[0]
# #         if PluralRule and Locale:
# #             try:
# #                 loc = Locale.parse(lang)
# #             except Exception:
# #                 try:
# #                     loc = Locale.parse(base)
# #                 except Exception:
# #                     loc = None
# #             if loc is not None:
# #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# #         return ["one", "other"]

# #     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# #         if (self._contains_protected_entity(entry.msgid) or
# #             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
# #             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
# #             result: Dict[int, str] = {}
# #             for i in range(npl):
# #                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
# #             self._counts["reused"] += 1
# #             return result

# #         header = self._plural_header_for_lang(target_lang)
# #         npl = self._nplurals_from_header(header)
# #         categories = self._plural_categories_for_lang(target_lang)
# #         if "one" not in categories:
# #             categories = ["one"] + [c for c in categories if c != "one"]
# #         if "other" not in categories:
# #             categories = categories + ["other"]

# #         templates_by_cat: Dict[str, str] = {}
# #         for cat in categories:
# #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# #             if custom:
# #                 templates_by_cat[cat] = custom

# #         if not templates_by_cat:
# #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# #             templates_by_cat["one"] = one_tmpl
# #             templates_by_cat["other"] = other_tmpl

# #         idx_map: List[str] = []
# #         if npl == 1:
# #             idx_map = ["other"]
# #         elif npl == 2:
# #             idx_map = ["one", "other"]
# #         elif npl == 3:
# #             pref = ["one", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         elif npl == 4:
# #             pref = ["one", "two", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         else:
# #             pref = ["zero", "one", "two", "few", "many", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# #         msgstr_plural: Dict[int, str] = {}
# #         for i, cat in enumerate(idx_map):
# #             tmpl = (templates_by_cat.get(cat) or
# #                     templates_by_cat.get("other") or
# #                     templates_by_cat.get("one") or
# #                     (entry.msgid_plural or entry.msgid))
# #             msgstr_plural[i] = tmpl
# #         return msgstr_plural

# #     # ----------------------------------------------------------------------
# #     # Snapshot & diff
# #     # ----------------------------------------------------------------------
# #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# #         snap = {}
# #         for e in pot:
# #             key = (e.msgctxt or '').strip() + "\u241E" + (e.msgid or '').strip() + "\u241E" + (e.msgid_plural or '').strip()
# #             snap[key] = {
# #                 "msgctxt": (e.msgctxt or '').strip(),
# #                 "msgid": (e.msgid or '').strip(),
# #                 "msgid_plural": (e.msgid_plural or '').strip()
# #             }
# #         return snap

# #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# #         diff = {}
# #         for k, nv in new.items():
# #             if k not in old:
# #                 diff[k] = "new"
# #             else:
# #                 ov = old[k]
# #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# #                     diff[k] = "modified"
# #                 else:
# #                     diff[k] = "unchanged"
# #         return diff

# #     # ----------------------------------------------------------------------
# #     # QA check
# #     # ----------------------------------------------------------------------
# #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# #         issues = []
# #         if not translated:
# #             issues.append("empty")
# #         base = entry.msgid_plural or entry.msgid
# #         if not self._placeholders_are_valid(base, translated):
# #             issues.append("placeholders")
# #         tags = self.html_tag_regex.findall(translated)
# #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# #         closes = sum(1 for t in tags if t.startswith("</"))
# #         if opens != closes:
# #             issues.append("html_unbalanced")
# #         if self._is_likely_untranslated(entry.msgid, translated):
# #             issues.append("unchanged_like")
# #         row = {
# #             "msgctxt": entry.msgctxt or '',
# #             "msgid": entry.msgid,
# #             "msgid_plural": entry.msgid_plural or '',
# #             "target_lang": target_lang,
# #             "status": status,
# #             "issues": ",".join(issues)
# #         }
# #         self._qa_rows.append(row)
# #         if "placeholders" in issues or "empty" in issues:
# #             self._counts["failed"] += 1

# #     # ----------------------------------------------------------------------
# #     # Report helper
# #     # ----------------------------------------------------------------------
# #     def _generate_report(self, target_language, version, timestamp, report_dir, reused_from=None):
# #         report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# #         report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# #         report = {
# #             "language": target_language,
# #             "generated_at": timestamp,
# #             "version": version,
# #             "reused_from": os.path.basename(reused_from) if reused_from else None,
# #             "counts": dict(self._counts),
# #             "rows": self._qa_rows,
# #         }
# #         try:
# #             with open(report_json, 'w', encoding='utf-8') as f:
# #                 json.dump(report, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             self._display_error(f"JSON report failed: {e}")

# #         try:
# #             if self._qa_rows:
# #                 headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# #                 with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# #                     w = csv.DictWriter(f, fieldnames=headers)
# #                     w.writeheader()
# #                     for r in self._qa_rows:
# #                         w.writerow({k: r.get(k, "") for k in headers})
# #         except Exception as e:
# #             self._display_error(f"CSV report failed: {e}")

# #     # ----------------------------------------------------------------------
# #     # MAIN run()
# #     # ----------------------------------------------------------------------
# #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# #         self._display_status("Starting Localization Tool")

# #         self.pot_file_path = pot_path
# #         self.zip_file_path = zip_path
# #         self.csv_file_path = csv_path
# #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# #         if not self.target_languages:
# #             self._display_error("No valid target languages provided.")
# #             return False

# #         # === PROJECT NAME: Strip Django suffix ===
# #         original_filename = getattr(pot_path, 'name', os.path.basename(pot_path))
# #         if '_' in original_filename and original_filename.endswith('.pot'):
# #             original_filename = original_filename.split('_', 1)[0] + '.pot'
# #         project_name = os.path.splitext(original_filename)[0]
# #         self._display_status(f"Project: {project_name} (from {original_filename})")

# #         project_dir = os.path.join(output_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)

# #         try:
# #             if not os.path.exists(self.pot_file_path):
# #                 self._display_error("POT file not found.")
# #                 return False

# #             pot_file = polib.pofile(self.pot_file_path)

# #             # --------------------------------------------------------------
# #             # SNAPSHOT & GLOBAL DIFF
# #             # --------------------------------------------------------------
# #             snapshot_path = self._get_snapshot_file_path(project_name)

# #             prev_snap = {}
# #             if os.path.exists(snapshot_path):
# #                 self._display_status(f"Snapshot FILE EXISTS: {snapshot_path}")
# #                 try:
# #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# #                         prev_snap = json.load(f)
# #                     self._display_status(f"Snapshot LOADED: {len(prev_snap)} entries")
# #                 except Exception as e:
# #                     self._display_error(f"Snapshot LOAD FAILED: {e}")
# #                     prev_snap = {}
# #             else:
# #                 self._display_status(f"NO SNAPSHOT FOUND: {snapshot_path}")

# #             new_snap = self._snapshot_from_pot(pot_file)
# #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# #             for status in diff_map.values():
# #                 self._counts[status] += 1

# #             # === SAVE & VERIFY SNAPSHOT ===
# #             try:
# #                 os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
# #                 with open(snapshot_path, 'w', encoding='utf-8') as f:
# #                     json.dump(new_snap, f, ensure_ascii=False, indent=2)
# #                 self._display_status(f"Snapshot SAVED: {snapshot_path} ({len(new_snap)} entries)")

# #                 with open(snapshot_path, 'r', encoding='utf-8') as f:
# #                     test_load = json.load(f)
# #                 if len(test_load) == len(new_snap):
# #                     self._display_status("Snapshot write VERIFIED")
# #                 else:
# #                     self._display_error("Snapshot CORRUPTED after save!")
# #             except Exception as e:
# #                 self._display_error(f"FAILED TO SAVE SNAPSHOT: {e}")

# #             # --------------------------------------------------------------
# #             # Load glossary & existing PO from ZIP
# #             # --------------------------------------------------------------
# #             glossary = (self._parse_glossary_csv(self.csv_file_path)
# #                         if self.csv_file_path and os.path.exists(self.csv_file_path) else {})
# #             existing_from_zip = (self._extract_and_parse_existing_pos(self.zip_file_path)
# #                                  if self.zip_file_path and os.path.exists(self.zip_file_path) else {})

# #             # --------------------------------------------------------------
# #             # Report folder
# #             # --------------------------------------------------------------
# #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# #             os.makedirs(report_dir, exist_ok=True)

# #             # --------------------------------------------------------------
# #             # PER-LANGUAGE LOOP
# #             # --------------------------------------------------------------
# #             for target_language in self.target_languages:
# #                 self._qa_rows = []
# #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# #                 memory = self._load_memory(project_name, target_language)
# #                 self._display_status(f"Processing {target_language}…")

# #                 # === LOAD lang.json ===
# #                 lang_json_path = self._get_lang_json_path(project_dir, target_language)
# #                 lang_json = {}
# #                 if os.path.exists(lang_json_path):
# #                     try:
# #                         with open(lang_json_path, 'r', encoding='utf-8') as f:
# #                             lang_json = json.load(f)
# #                         self._display_status(f"Loaded {len(lang_json)} strings from {target_language}.json")
# #                     except Exception as e:
# #                         self._display_error(f"Failed to load {target_language}.json: {e}")
# #                 else:
# #                     self._display_status(f"No {target_language}.json — starting fresh")

# #                 version = 1
# #                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
# #                     version += 1
# #                 existing_po_path = os.path.join(project_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

# #                 # === FULL REUSE WITH ROBUST COMPARISON ===
# #                 if existing_po_path:
# #                     def normalize(snap):
# #                         return {k.strip(): {kk: vv.strip() for kk, vv in v.items()} for k, v in snap.items()}
# #                     if normalize(prev_snap) == normalize(new_snap):
# #                         try:
# #                             po = polib.pofile(existing_po_path)
# #                             entries_count = len([e for e in po if e.msgid])
# #                             self._display_status(f"FULL REUSE: Copying {entries_count} entries from {os.path.basename(existing_po_path)}")

# #                             for entry in po:
# #                                 if not entry.msgid:
# #                                     continue
# #                                 self._counts["reused"] += 1
# #                                 status = "unchanged"
# #                                 if entry.msgid_plural:
# #                                     for form in entry.msgstr_plural.values():
# #                                         self._qa_check(entry, form, status, target_language)
# #                                 else:
# #                                     self._qa_check(entry, entry.msgstr, status, target_language)

# #                             out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                             out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")
# #                             po.save(out_po)
# #                             po.save_as_mofile(out_mo)

# #                             self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                             self._save_memory(memory, project_name, target_language)
# #                             self._display_status(f"Reused entire PO → {out_po}")
# #                             continue

# #                         except Exception as e:
# #                             self._display_error(f"Reuse failed: {e}. Regenerating...")

# #                 # === NORMAL PROCESSING ===
# #                 self._display_status("POT changed or no reuse → translating entries...")
# #                 po = polib.POFile()
# #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
# #                 po.metadata = {
# #                     'Project-Id-Version': 'Colab Free',
# #                     'POT-Creation-Date': now,
# #                     'PO-Revision-Date': now,
# #                     'Language': target_language,
# #                     'MIME-Version': '1.0',
# #                     'Content-Type': 'text/plain; charset=UTF-8',
# #                     'Content-Transfer-Encoding': '8bit',
# #                     'X-Generator': 'Colab Tool',
# #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# #                 }

# #                 for entry in pot_file:
# #                     if not entry.msgid:
# #                         continue

# #                     key = (entry.msgctxt or '').strip() + "\u241E" + (entry.msgid or '').strip() + "\u241E" + (entry.msgid_plural or '').strip()
# #                     status = diff_map.get(key, "new")

# #                     try:
# #                         if entry.msgid_plural:
# #                             msgstr_plural = self._pluralize_entry(memory, lang_json, entry, target_language)
# #                             new_entry = polib.POEntry(
# #                                 msgid=entry.msgid,
# #                                 msgid_plural=entry.msgid_plural,
# #                                 msgstr_plural=msgstr_plural,
# #                                 msgctxt=entry.msgctxt,
# #                                 occurrences=entry.occurrences,
# #                                 comment=entry.comment,
# #                                 tcomment=entry.tcomment
# #                             )
# #                             if status == "modified":
# #                                 new_entry.flags.append("fuzzy")
# #                                 self._counts["fuzzy"] += 1
# #                             po.append(new_entry)
# #                             for s in msgstr_plural.values():
# #                                 self._qa_check(entry, s, status, target_language)
# #                             continue

# #                         translated_msgstr, source = self._process_translation(
# #                             memory, lang_json, entry, glossary, existing_from_zip, target_language
# #                         )
# #                         new_entry = polib.POEntry(
# #                             msgid=entry.msgid,
# #                             msgstr=translated_msgstr,
# #                             msgctxt=entry.msgctxt,
# #                             occurrences=entry.occurrences,
# #                             comment=entry.comment,
# #                             tcomment=entry.tcomment
# #                         )
# #                         if status == "modified" or "Fuzzy" in source:
# #                             new_entry.flags.append("fuzzy")
# #                             self._counts["fuzzy"] += 1
# #                         if status == "unchanged" and source in ("lang.json", "Glossary", "Existing PO", "Protected Entity"):
# #                             self._counts["reused"] += 1
# #                         po.append(new_entry)
# #                         self._qa_check(entry, translated_msgstr, status, target_language)

# #                     except Exception as e:
# #                         self._display_error(f"Failed to process '{entry.msgid[:50]}…': {e}")
# #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr='', flags=['fuzzy']))
# #                         self._counts["failed"] += 1

# #                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
# #                 out_mo = os.path.join(project_dir, f"{target_language}-{version}.mo")
# #                 po.save(out_po)
# #                 po.save_as_mofile(out_mo)

# #                 # === UPDATE lang.json ===
# #                 current_translations = {}
# #                 for entry in po:
# #                     if entry.msgid and entry.msgstr:
# #                         current_translations[entry.msgid] = entry.msgstr
# #                     if entry.msgid_plural and entry.msgstr_plural:
# #                         for i, msg in entry.msgstr_plural.items():
# #                             key = entry.msgid_plural if i > 0 else entry.msgid
# #                             if msg:
# #                                 current_translations[key] = msg

# #                 lang_json.update(current_translations)

# #                 try:
# #                     with open(lang_json_path, 'w', encoding='utf-8') as f:
# #                         json.dump(lang_json, f, ensure_ascii=False, indent=2, sort_keys=True)
# #                     self._display_status(f"Updated {target_language}.json → {len(current_translations)} strings")
# #                 except Exception as e:
# #                     self._display_error(f"Failed to save {target_language}.json: {e}")

# #                 self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                 self._save_memory(memory, project_name, target_language)

# #             self._display_status("Translation complete with smart reuse.")
# #             return True

# #         except Exception as e:
# #             self._display_error(f"Unexpected error: {e}")
# #             return False




# # localizationtool/localization_logic.py best code till now txt file read gardian na
# # import polib
# # import csv
# # import zipfile
# # import os
# # import shutil
# # from datetime import datetime
# # from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# # import re
# # from charset_normalizer import from_path
# # import time
# # import json
# # from typing import Dict, Tuple, List, Optional
# # from django.conf import settings

# # try:
# #     from babel.core import Locale
# #     from babel.plural import PluralRule
# # except ImportError:
# #     Locale = None
# #     PluralRule = None


# # class _Translator:
# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         raise NotImplementedError


# # class GoogleTranslatorEngine(_Translator):
# #     _SEP = "INVISIBLE_SEPARATOR"

# #     def translate(self, texts: List[str], target_lang: str) -> List[str]:
# #         if not texts:
# #             return []
# #         joined = self._SEP.join(texts)
# #         translator = _GoogleTranslator(source='auto', target=target_lang)
# #         out = translator.translate(joined)
# #         if isinstance(out, list):
# #             return [str(x) for x in out]
# #         parts = str(out).split(self._SEP)
# #         if len(parts) != len(texts):
# #             parts = []
# #             for t in texts:
# #                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
# #         return parts


# # class ColabLocalizationTool:
# #     def __init__(self, memory_base_dir: str = None):
# #         self.pot_file_path = None
# #         self.zip_file_path = None
# #         self.csv_file_path = None
# #         self.target_languages: List[str] = []
# #         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
# #         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
# #         os.makedirs(self.memory_base_dir, exist_ok=True)

# #         self.NON_TRANSLATABLE_ENTITIES = {
# #             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
# #             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
# #             "&trade;", "&TRADE;", "TRADEMARK",
# #             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
# #         }

# #         self.printf_placeholder_regex = re.compile(r"%\d+\$[sdif]|%[sdif]|%[a-zA-Z_]\w*|%%")
# #         self.icu_placeholder_regex = re.compile(r"\{[^}]*\}")
# #         self.html_tag_regex = re.compile(r"</?[a-zA-Z][^>]*>")
# #         self.quoted_printf_regex = re.compile(r'(&ldquo;%[^&]+?&rdquo;)')

# #         self.translation_rules = {
# #             "%s min read": {
# #                 "ja": "%s分で読めます",
# #                 "it": "%s min di lettura",
# #                 "nl": "%s min gelezen",
# #                 "pl": "%s min czytania",
# #                 "pt": "%s min de leitura",
# #                 "de": "%s Min. Lesezeit",
# #                 "ar": "قراءة في %s دقيقة",
# #                 "fr": "%s min de lecture",
# #                 "ru": "%s мин. чтения",
# #                 "en": "%s mins read",
# #                 # NEW LANGUAGES
# #                 "sw": "%s dakika kusoma",     # Swahili
# #                 "da": "%s min læsning",       # Danish
# #                 "fi": "%s min lukeminen",     # Finnish
# #                 "is": "%s mín lestur",        # Icelandic
# #                 "no": "%s min lesing",        # Norwegian
# #                 "sv": "%s min läsning",       # Swedish
# #                 "zh-CH": "%s 分钟阅读",
# #             }
# #         }

# #         self.translation_rules_plural_templates = {
# #             "%s min read": {
# #                 "en": {"one": "%s min read", "other": "%s mins read"},
# #                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
# #                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения",
# #                        "many": "%s мин. чтения", "other": "%s мин. чтения"},
# #                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
# #                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
# #                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
# #                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
# #                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
# #                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
# #                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
# #                 "zh-CN": {"other": "%s 分钟阅读"},  
# #             }
# #         }

# #         self.memory_storage_limit_mb = 100
# #         self._qa_rows: List[Dict] = []
# #         self._counts = {
# #             "new": 0, "modified": 0, "unchanged": 0,
# #             "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0,
# #         }
# #         self._cache: Dict[Tuple[str, str], str] = {}
# #         self.translator_engine: _Translator = GoogleTranslatorEngine()

# #         self.plural_forms_header = {
# #             "en": "nplurals=2; plural=(n != 1);",
# #             "es": "nplurals=2; plural=(n != 1);",
# #             "de": "nplurals=2; plural=(n != 1);",
# #             "fr": "nplurals=2; plural=(n > 1);",
# #             "pt": "nplurals=2; plural=(n != 1);",
# #             "hi": "nplurals=2; plural=(n != 1);",
# #             "ne": "nplurals=2; plural=(n != 1);",
# #             "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
# #             "it": "nplurals=2; plural=(n != 1);",
# #             "ja": "nplurals=1; plural=0;",
# #             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "nl": "nplurals=2; plural=(n != 1);",
# #             "uk": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
# #             "zh": "nplurals=1; plural=0;",
# #             "pt_BR": "nplurals=2; plural=(n > 1);",
# #             "id": "nplurals=1; plural=0;",
# #             "th": "nplurals=1; plural=0;",
# #             "tl": "nplurals=2; plural=(n != 1);",
# #             "ko": "nplurals=1; plural=0;",
# #             "en-gb": "nplurals=2; plural=(n != 1);",
# #             "sw": "nplurals=2; plural=(n != 1);",  # Swahili
# #             "da": "nplurals=2; plural=(n != 1);",  # Danish
# #             "fi": "nplurals=2; plural=(n != 1);",  # Finnish
# #             "is": "nplurals=2; plural=(n != 1);",  # Icelandic
# #             "no": "nplurals=2; plural=(n != 1);",  # Norwegian
# #             "sv": "nplurals=2; plural=(n != 1);",  # Swedish
# #             "zh-CN": "nplurals=1; plural=0;",

# #         }

# #     def _contains_protected_entity(self, text: str) -> bool:
# #         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

# #     def _get_memory_file_path(self, project_name, lang):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _get_snapshot_file_path(self, project_name):
# #         project_dir = os.path.join(self.memory_base_dir, project_name)
# #         os.makedirs(project_dir, exist_ok=True)
# #         return os.path.join(project_dir, "_last_snapshot.json")

# #     def _get_lang_json_path(self, project_dir, lang):
# #         return os.path.join(project_dir, f"{lang}.json")

# #     def _load_memory(self, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         if os.path.exists(path):
# #             try:
# #                 with open(path, 'r', encoding='utf-8') as f:
# #                     return json.load(f)
# #             except Exception as e:
# #                 print(f"Memory load failed: {e}")
# #                 return {}
# #         return {}

# #     def _save_memory(self, memory, project_name, lang):
# #         path = self._get_memory_file_path(project_name, lang)
# #         try:
# #             with open(path, 'w', encoding='utf-8') as f:
# #                 json.dump(memory, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             print(f"Failed to save memory: {e}")

# #     def _get_memory_translation(self, memory, msgid, target_lang):
# #         return memory.get(msgid)

# #     def _update_memory(self, memory, msgid, translation):
# #         memory[msgid] = translation

# #     def _display_status(self, message):
# #         print(f"\n--- STATUS: {message} ---")

# #     def _display_error(self, message):
# #         print(f"\n--- ERROR: {message} ---")

# #     def _parse_glossary_csv(self, csv_file_path):
# #         glossary_lookup: Dict[Tuple[str, str], str] = {}
# #         encodings = ['utf-8', 'latin1', 'cp1252']
# #         for encoding in encodings:
# #             try:
# #                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
# #                     reader = csv.DictReader(f)
# #                     for row in reader:
# #                         orig = (row.get("Original String", "") or "").strip()
# #                         ctx = (row.get("Context", "") or "").strip()
# #                         trans = (row.get("Translated String", "") or "").strip()
# #                         trans = self._normalize_placeholders(trans)
# #                         glossary_lookup[(orig, ctx)] = trans
# #                 return glossary_lookup
# #             except Exception as e:
# #                 print(f"Glossary parse error with {encoding}: {e}")
# #         print("All encoding attempts failed for glossary CSV.")
# #         return glossary_lookup

# #     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
# #         key = (msgid, msgctxt or '')
# #         if key in glossary_lookup:
# #             return glossary_lookup[key]
# #         for (orig, ctx), trans in glossary_lookup.items():
# #             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
# #                 return trans
# #             if orig == msgid and ctx:
# #                 try:
# #                     if re.search(ctx, msgctxt or ''):
# #                         return trans
# #                 except re.error:
# #                     continue
# #         return None

# #     def _normalize_placeholders(self, msgstr):
# #         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

# #     def _extract_and_parse_existing_pos(self, zip_file_path):
# #         existing_po_lookup = {}
# #         if os.path.exists(self.temp_dir):
# #             shutil.rmtree(self.temp_dir)
# #         os.makedirs(self.temp_dir)
# #         try:
# #             with zipfile.ZipFile(zip_file_path, 'r') as zf:
# #                 for member in zf.namelist():
# #                     if member.endswith('.po'):
# #                         zf.extract(member, self.temp_dir)
# #                         path = os.path.join(self.temp_dir, member)
# #                         try:
# #                             po = polib.pofile(path)
# #                             for entry in po:
# #                                 key = (entry.msgid, entry.msgctxt or '')
# #                                 cleaned = entry.msgstr
# #                                 if cleaned:
# #                                     cleaned = self._normalize_placeholders(cleaned)
# #                                     if self._placeholders_are_valid(entry.msgid, cleaned):
# #                                         cleaned = self._clean_translated_text(cleaned)
# #                                         existing_po_lookup[key] = cleaned
# #                         except Exception as e:
# #                             print(f"Error parsing PO: {e}")
# #         except Exception as e:
# #             print(f"Error extracting ZIP: {e}")
# #         finally:
# #             shutil.rmtree(self.temp_dir, ignore_errors=True)
# #         return existing_po_lookup

# #     def _collect_placeholders(self, text: str) -> List[str]:
# #         ph = []
# #         ph += self.printf_placeholder_regex.findall(text)
# #         ph += self.icu_placeholder_regex.findall(text)
# #         quoted = self.quoted_printf_regex.findall(text)
# #         ph += quoted
# #         normalized = []
# #         for x in ph:
# #             if isinstance(x, tuple):
# #                 normalized.append('{' + x[0] + '}')
# #             else:
# #                 normalized.append(x)
# #         return list(dict.fromkeys(normalized))

# #     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
# #         try:
# #             orig_ph = self._collect_placeholders(original)
# #             trans_ph = self._collect_placeholders(translated)
# #             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
# #         except Exception as e:
# #             print(f"Placeholder validation failed: {e}")
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
# #         for token in list(placeholder_map.keys()):
# #             escaped = re.escape(token)
# #             pattern = re.compile(r'\s*'.join(list(escaped)))
# #             text = pattern.sub(token, text)
# #         for token, ph in placeholder_map.items():
# #             text = text.replace(token, ph)
# #         return text

# #     def _clean_translated_text(self, text):
# #         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
# #         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
# #         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
# #         text = re.sub(r'(\s+)(”|\))', r'\2', text)
# #         text = re.sub(r'(“|\()\s+', r'\1', text)
# #         return text

# #     def _is_likely_untranslated(self, original_text, translated_text):
# #         protected_orig, _ = self._protect_markers(original_text)
# #         protected_trans, _ = self._protect_markers(translated_text)
# #         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
# #         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
# #         return raw_orig.strip().lower() == raw_trans.strip().lower()

# #     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
# #         if msgid in self.translation_rules_plural_templates:
# #             lang_map = self.translation_rules_plural_templates[msgid]
# #             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #             if lang_map and plural_category and plural_category in lang_map:
# #                 return lang_map[plural_category]
# #         if msgid in self.translation_rules:
# #             lang_map = self.translation_rules[msgid]
# #             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
# #         return None

# #     def _is_valid_translation(self, text):
# #         error_signs = [
# #             "Error 500", "That’s an error", "There was an error",
# #             "<html", "</html>", "<body>", "</body>", "Please try again later",
# #         ]
# #         lowered = text.lower()
# #         return not any(s.lower() in lowered for s in error_signs)

# #     def _retry(self, func, max_retries=3):
# #         delay = 1.0
# #         for i in range(max_retries):
# #             try:
# #                 return func()
# #             except Exception as e:
# #                 print(f"Attempt {i+1}/{max_retries} failed: {e}")
# #                 if i == max_retries - 1:
# #                     raise
# #                 time.sleep(delay)
# #                 delay *= 2

# #     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
# #         outputs: List[str] = [None] * len(texts)
# #         to_query_idx = []
# #         to_query = []
# #         for i, t in enumerate(texts):
# #             mem = self._get_memory_translation(memory, t, target_lang)
# #             if mem:
# #                 outputs[i] = mem
# #                 continue
# #             key = (t, target_lang)
# #             if key in self._cache:
# #                 outputs[i] = self._cache[key]
# #             else:
# #                 to_query_idx.append(i)
# #                 to_query.append(t)
# #         if to_query:
# #             def call():
# #                 return self.translator_engine.translate(to_query, target_lang)
# #             translated_list = self._retry(call, max_retries=3)
# #             for j, out in enumerate(translated_list):
# #                 idx = to_query_idx[j]
# #                 outputs[idx] = out
# #                 self._cache[(texts[idx], target_lang)] = out
# #                 self._update_memory(memory, texts[idx], out)
# #                 time.sleep(0.3)
# #         return [x or "" for x in outputs]

# #     def _fallback_translate(self, memory, text, target_lang):
# #         mem = self._get_memory_translation(memory, text, target_lang)
# #         if mem:
# #             return mem
# #         key = (text, target_lang)
# #         if key in self._cache:
# #             return self._cache[key]

# #         protected_text, placeholder_map = self._protect_markers(text)
# #         try:
# #             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
# #             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
# #             translated = self._restore_markers(translated_protected, placeholder_map)
# #             translated = self._clean_translated_text(translated)
# #             if not self._is_valid_translation(translated):
# #                 print(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original.")
# #                 return text
# #             self._cache[key] = translated
# #             self._update_memory(memory, text, translated)
# #             return translated
# #         except exceptions.NotValidPayload as e:
# #             print(f"Invalid payload for '{text}'. Error: {e}")
# #             return text
# #         except Exception as e:
# #             print(f"Translation failed for '{text}' → '{target_lang}': {e}")
# #             return text

# #     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
# #         msgid = pot_entry.msgid
# #         msgctxt = pot_entry.msgctxt or ''

# #         if msgid in lang_json:
# #             self._counts["reused"] += 1
# #             return lang_json[msgid], "lang.json"

# #         if self._contains_protected_entity(msgid):
# #             self._counts["reused"] += 1
# #             return msgid, "Protected Entity"

# #         custom = self._apply_custom_rules(msgid, target_lang)
# #         if custom:
# #             self._update_memory(memory, msgid, custom)
# #             self._counts["translated"] += 1
# #             return custom, "Custom Rule"

# #         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
# #         if gloss:
# #             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Glossary (Fuzzy)"
# #             self._update_memory(memory, msgid, gloss)
# #             self._counts["reused"] += 1
# #             return gloss, "Glossary"

# #         key_ctxt = (msgid, msgctxt)
# #         if key_ctxt in existing_po_lookup:
# #             existing = existing_po_lookup[key_ctxt]
# #             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
# #                 fb = self._fallback_translate(memory, msgid, target_lang)
# #                 self._counts["translated"] += 1
# #                 return fb, "Existing PO (Fuzzy)"
# #             self._update_memory(memory, msgid, existing)
# #             self._counts["reused"] += 1
# #             return existing, "Existing PO"

# #         fb = self._fallback_translate(memory, msgid, target_lang)
# #         self._counts["translated"] += 1
# #         return fb, "Machine Translation"

# #     def _plural_header_for_lang(self, lang: str) -> str:
# #         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

# #     def _nplurals_from_header(self, header: str) -> int:
# #         m = re.search(r"nplurals\s*=\s*(\d+)", header)
# #         return int(m.group(1)) if m else 2

# #     def _plural_categories_for_lang(self, lang: str) -> List[str]:
# #         base = lang.split('_', 1)[0]
# #         if PluralRule and Locale:
# #             try:
# #                 loc = Locale.parse(lang)
# #             except Exception:
# #                 try:
# #                     loc = Locale.parse(base)
# #                 except Exception:
# #                     loc = None
# #             if loc is not None:
# #                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
# #         return ["one", "other"]

# #     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
# #         if (self._contains_protected_entity(entry.msgid) or
# #             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
# #             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
# #             result: Dict[int, str] = {}
# #             for i in range(npl):
# #                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
# #             self._counts["reused"] += 1
# #             return result

# #         header = self._plural_header_for_lang(target_lang)
# #         npl = self._nplurals_from_header(header)
# #         categories = self._plural_categories_for_lang(target_lang)
# #         if "one" not in categories:
# #             categories = ["one"] + [c for c in categories if c != "one"]
# #         if "other" not in categories:
# #             categories = categories + ["other"]

# #         templates_by_cat: Dict[str, str] = {}
# #         for cat in categories:
# #             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
# #             if custom:
# #                 templates_by_cat[cat] = custom

# #         if not templates_by_cat:
# #             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
# #             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
# #             templates_by_cat["one"] = one_tmpl
# #             templates_by_cat["other"] = other_tmpl

# #         idx_map: List[str] = []
# #         if npl == 1:
# #             idx_map = ["other"]
# #         elif npl == 2:
# #             idx_map = ["one", "other"]
# #         elif npl == 3:
# #             pref = ["one", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         elif npl == 4:
# #             pref = ["one", "two", "few", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref]
# #         else:
# #             pref = ["zero", "one", "two", "few", "many", "other"]
# #             idx_map = [c if c in categories else "other" for c in pref[:npl]]

# #         msgstr_plural: Dict[int, str] = {}
# #         for i, cat in enumerate(idx_map):
# #             tmpl = (templates_by_cat.get(cat) or
# #                     templates_by_cat.get("other") or
# #                     templates_by_cat.get("one") or
# #                     (entry.msgid_plural or entry.msgid))
# #             msgstr_plural[i] = tmpl
# #         return msgstr_plural

# #     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
# #         snap = {}
# #         for e in pot:
# #             key = (e.msgctxt or '').strip() + "RECORD_SEPARATOR" + (e.msgid or '').strip() + "RECORD_SEPARATOR" + (e.msgid_plural or '').strip()
# #             snap[key] = {
# #                 "msgctxt": (e.msgctxt or '').strip(),
# #                 "msgid": (e.msgid or '').strip(),
# #                 "msgid_plural": (e.msgid_plural or '').strip()
# #             }
# #         return snap

# #     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
# #         diff = {}
# #         for k, nv in new.items():
# #             if k not in old:
# #                 diff[k] = "new"
# #             else:
# #                 ov = old[k]
# #                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
# #                     diff[k] = "modified"
# #                 else:
# #                     diff[k] = "unchanged"
# #         return diff

# #     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
# #         issues = []
# #         if not translated:
# #             issues.append("empty")
# #         base = entry.msgid_plural or entry.msgid
# #         if not self._placeholders_are_valid(base, translated):
# #             issues.append("placeholders")
# #         tags = self.html_tag_regex.findall(translated)
# #         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
# #         closes = sum(1 for t in tags if t.startswith("</"))
# #         if opens != closes:
# #             issues.append("html_unbalanced")
# #         if self._is_likely_untranslated(entry.msgid, translated):
# #             issues.append("unchanged_like")
# #         row = {
# #             "msgctxt": entry.msgctxt or '',
# #             "msgid": entry.msgid,
# #             "msgid_plural": entry.msgid_plural or '',
# #             "target_lang": target_lang,
# #             "status": status,
# #             "issues": ",".join(issues)
# #         }
# #         self._qa_rows.append(row)
# #         if "placeholders" in issues or "empty" in issues:
# #             self._counts["failed"] += 1

# #     def _generate_report(self, target_language, version, timestamp, report_dir, reused_from=None):
# #         report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
# #         report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
# #         report = {
# #             "language": target_language,
# #             "generated_at": timestamp,
# #             "version": version,
# #             "reused_from": os.path.basename(reused_from) if reused_from else None,
# #             "counts": dict(self._counts),
# #             "rows": self._qa_rows,
# #         }
# #         try:
# #             with open(report_json, 'w', encoding='utf-8') as f:
# #                 json.dump(report, f, ensure_ascii=False, indent=2)
# #         except Exception as e:
# #             print(f"JSON report failed: {e}")

# #         try:
# #             if self._qa_rows:
# #                 headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
# #                 with open(report_csv, 'w', encoding='utf-8', newline='') as f:
# #                     w = csv.DictWriter(f, fieldnames=headers)
# #                     w.writeheader()
# #                     for r in self._qa_rows:
# #                         w.writerow({k: r.get(k, "") for k in headers})
# #         except Exception as e:
# #             print(f"CSV report failed: {e}")

# #     def run(self, pot_path, zip_path, csv_path, target_langs, output_dir):
# #         self._display_status("Starting Localization Tool")

# #         self.pot_file_path = pot_path
# #         self.zip_file_path = zip_path
# #         self.csv_file_path = csv_path
# #         valid_langs = [lang[0] for lang in settings.LANGUAGES]
# #         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
# #         if not self.target_languages:
# #             self._display_error("No valid target languages provided.")
# #             return False

# #         project_name = os.path.basename(output_dir)
# #         self._display_status(f"Project: {project_name}")

# #         try:
# #             if not os.path.exists(self.pot_file_path):
# #                 self._display_error("POT file not found.")
# #                 return False

# #             pot_file = polib.pofile(self.pot_file_path)

# #             snapshot_path = self._get_snapshot_file_path(project_name)
# #             prev_snap = {}
# #             if os.path.exists(snapshot_path):
# #                 try:
# #                     with open(snapshot_path, 'r', encoding='utf-8') as f:
# #                         prev_snap = json.load(f)
# #                 except Exception as e:
# #                     print(f"Snapshot LOAD FAILED: {e}")
# #             new_snap = self._snapshot_from_pot(pot_file)
# #             diff_map = self._diff_snapshots(prev_snap, new_snap)

# #             for status in diff_map.values():
# #                 self._counts[status] += 1

# #             try:
# #                 os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
# #                 with open(snapshot_path, 'w', encoding='utf-8') as f:
# #                     json.dump(new_snap, f, ensure_ascii=False, indent=2)
# #             except Exception as e:
# #                 print(f"FAILED TO SAVE SNAPSHOT: {e}")

# #             glossary = (self._parse_glossary_csv(self.csv_file_path)
# #                         if self.csv_file_path and os.path.exists(self.csv_file_path) else {})
# #             existing_from_zip = (self._extract_and_parse_existing_pos(self.zip_file_path)
# #                                  if self.zip_file_path and os.path.exists(self.zip_file_path) else {})

# #             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
# #             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
# #             os.makedirs(report_dir, exist_ok=True)

# #             for target_language in self.target_languages:
# #                 self._qa_rows = []
# #                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

# #                 memory = self._load_memory(project_name, target_language)
# #                 lang_json_path = self._get_lang_json_path(output_dir, target_language)
# #                 lang_json = {}
# #                 if os.path.exists(lang_json_path):
# #                     try:
# #                         with open(lang_json_path, 'r', encoding='utf-8') as f:
# #                             lang_json = json.load(f)
# #                     except Exception as e:
# #                         print(f"Failed to load {target_language}.json: {e}")

# #                 version = 1
# #                 while os.path.exists(os.path.join(output_dir, f"{target_language}-{version}.po")):
# #                     version += 1
# #                 existing_po_path = os.path.join(output_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

# #                 if existing_po_path:
# #                     if prev_snap == new_snap:
# #                         try:
# #                             po = polib.pofile(existing_po_path)
# #                             out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
# #                             out_mo = out_po.replace('.po', '.mo')
# #                             po.save(out_po)
# #                             po.save_as_mofile(out_mo)
# #                             self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                             self._save_memory(memory, project_name, target_language)
# #                             continue
# #                         except Exception as e:
# #                             print(f"Reuse failed: {e}")

# #                 po = polib.POFile()
# #                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
# #                 po.metadata = {
# #                     'Project-Id-Version': project_name,
# #                     'POT-Creation-Date': now,
# #                     'PO-Revision-Date': now,
# #                     'Language': target_language,
# #                     'MIME-Version': '1.0',
# #                     'Content-Type': 'text/plain; charset=UTF-8',
# #                     'Content-Transfer-Encoding': '8bit',
# #                     'X-Generator': 'Colab Tool',
# #                     'Plural-Forms': self._plural_header_for_lang(target_language)
# #                 }

# #                 for entry in pot_file:
# #                     if not entry.msgid:
# #                         continue

# #                     key = (entry.msgctxt or '').strip() + "RECORD_SEPARATOR" + (entry.msgid or '').strip() + "RECORD_SEPARATOR" + (entry.msgid_plural or '').strip()
# #                     status = diff_map.get(key, "new")

# #                     try:
# #                         if entry.msgid_plural:
# #                             msgstr_plural = self._pluralize_entry(memory, lang_json, entry, target_language)
# #                             new_entry = polib.POEntry(
# #                                 msgid=entry.msgid,
# #                                 msgid_plural=entry.msgid_plural,
# #                                 msgstr_plural=msgstr_plural,
# #                                 msgctxt=entry.msgctxt,
# #                                 occurrences=entry.occurrences,
# #                                 comment=entry.comment,
# #                                 tcomment=entry.tcomment
# #                             )
# #                             if status == "modified":
# #                                 new_entry.flags.append("fuzzy")
# #                                 self._counts["fuzzy"] += 1
# #                             po.append(new_entry)
# #                             for s in msgstr_plural.values():
# #                                 self._qa_check(entry, s, status, target_language)
# #                             continue

# #                         translated_msgstr, source = self._process_translation(
# #                             memory, lang_json, entry, glossary, existing_from_zip, target_language
# #                         )
# #                         new_entry = polib.POEntry(
# #                             msgid=entry.msgid,
# #                             msgstr=translated_msgstr,
# #                             msgctxt=entry.msgctxt,
# #                             occurrences=entry.occurrences,
# #                             comment=entry.comment,
# #                             tcomment=entry.tcomment
# #                         )
# #                         if status == "modified" or "Fuzzy" in source:
# #                             new_entry.flags.append("fuzzy")
# #                             self._counts["fuzzy"] += 1
# #                         po.append(new_entry)
# #                         self._qa_check(entry, translated_msgstr, status, target_language)

# #                     except Exception as e:
# #                         print(f"Failed to process '{entry.msgid[:50]}…': {e}")
# #                         po.append(polib.POEntry(msgid=entry.msgid, msgstr='', flags=['fuzzy']))
# #                         self._counts["failed"] += 1

# #                 out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
# #                 out_mo = out_po.replace('.po', '.mo')
# #                 po.save(out_po)
# #                 po.save_as_mofile(out_mo)

# #                 current_translations = {}
# #                 for entry in po:
# #                     if entry.msgid and entry.msgstr:
# #                         current_translations[entry.msgid] = entry.msgstr
# #                     if entry.msgid_plural and entry.msgstr_plural:
# #                         for i, msg in entry.msgstr_plural.items():
# #                             key = entry.msgid_plural if i > 0 else entry.msgid
# #                             if msg:
# #                                 current_translations[key] = msg

# #                 lang_json.update(current_translations)
# #                 try:
# #                     with open(lang_json_path, 'w', encoding='utf-8') as f:
# #                         json.dump(lang_json, f, ensure_ascii=False, indent=2, sort_keys=True)
# #                 except Exception as e:
# #                     print(f"Failed to save {target_language}.json: {e}")

# #                 self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
# #                 self._save_memory(memory, project_name, target_language)

# #             self._display_status("Translation complete.")
# #             return True

# #         except Exception as e:
# #             self._display_error(f"Unexpected error: {e}")
# #             return False


# # localizationtool/localization_logic.py this code is best
# import polib
# import csv
# import zipfile
# import os
# import shutil
# from datetime import datetime
# from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# import re
# import time
# import json
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings

# try:
#     from babel.core import Locale
#     from babel.plural import PluralRule
# except ImportError:
#     Locale = None
#     PluralRule = None


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "INVISIBLE_SEPARATOR"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         translator = _GoogleTranslator(source='auto', target=target_lang)
#         out = translator.translate(joined)
#         if isinstance(out, list):
#             return [str(x) for x in out]
#         parts = str(out).split(self._SEP)
#         if len(parts) != len(texts):
#             parts = []
#             for t in texts:
#                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
#         return parts


# class ColabLocalizationTool:
#     def __init__(self, memory_base_dir: str = None):
#         self.pot_file_path = None
#         self.zip_file_path = None
#         self.csv_file_path = None
#         self.target_languages: List[str] = []
#         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")
#         self.memory_base_dir = memory_base_dir or os.path.join(settings.MEDIA_ROOT, "translation_memory")
#         os.makedirs(self.memory_base_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
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

#         self.translation_rules_plural_templates = {
#             "%s min read": {
#                 "en": {"one": "%s min read", "other": "%s mins read"},
#                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
#                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
#                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
#                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
#                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
#                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
#                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
#                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
#                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
#                 "zh-CN": {"other": "%s 分钟阅读"},
#             }
#         }

#         self.memory_storage_limit_mb = 100
#         self._qa_rows: List[Dict] = []
#         self._counts = {"new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0}
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine: _Translator = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);", "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);", "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);", "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);", "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
#             "it": "nplurals=2; plural=(n != 1);", "ja": "nplurals=1; plural=0;",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "nl": "nplurals=2; plural=(n != 1);", "zh": "nplurals=1; plural=0;",
#             "id": "nplurals=1; plural=0;", "th": "nplurals=1; plural=0;",
#             "tl": "nplurals=2; plural=(n != 1);", "ko": "nplurals=1; plural=0;",
#             "en-gb": "nplurals=2; plural=(n != 1);", "sw": "nplurals=2; plural=(n != 1);",
#             "da": "nplurals=2; plural=(n != 1);", "fi": "nplurals=2; plural=(n != 1);",
#             "is": "nplurals=2; plural=(n != 1);", "no": "nplurals=2; plural=(n != 1);",
#             "sv": "nplurals=2; plural=(n != 1);", "zh-CN": "nplurals=1; plural=0;",
#         }

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _get_memory_file_path(self, project_name, lang):
#         project_dir = os.path.join(self.memory_base_dir, project_name)
#         os.makedirs(project_dir, exist_ok=True)
#         return os.path.join(project_dir, f"{lang}.json")

#     def _get_snapshot_file_path(self, project_name):
#         project_dir = os.path.join(self.memory_base_dir, project_name)
#         os.makedirs(project_dir, exist_ok=True)
#         return os.path.join(project_dir, "_last_snapshot.json")

#     def _get_lang_json_path(self, project_dir, lang):
#         return os.path.join(project_dir, f"{lang}.json")

#     def _load_memory(self, project_name, lang):
#         path = self._get_memory_file_path(project_name, lang)
#         if os.path.exists(path):
#             try:
#                 with open(path, 'r', encoding='utf-8') as f:
#                     return json.load(f)
#             except Exception as e:
#                 print(f"Memory load failed: {e}")
#                 return {}
#         return {}

#     def _save_memory(self, memory, project_name, lang):
#         path = self._get_memory_file_path(project_name, lang)
#         try:
#             with open(path, 'w', encoding='utf-8') as f:
#                 json.dump(memory, f, ensure_ascii=False, indent=2)
#         except Exception as e:
#             print(f"Failed to save memory: {e}")

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _parse_glossary_csv(self, csv_file_path):
#         glossary_lookup: Dict[Tuple[str, str], str] = {}
#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         trans = self._normalize_placeholders(trans)
#                         glossary_lookup[(orig, ctx)] = trans
#                 return glossary_lookup
#             except Exception as e:
#                 print(f"Glossary parse error with {encoding}: {e}")
#         print("All encoding attempts failed for glossary CSV.")
#         return glossary_lookup

#     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
#         key = (msgid, msgctxt or '')
#         if key in glossary_lookup:
#             return glossary_lookup[key]
#         for (orig, ctx), trans in glossary_lookup.items():
#             if orig == msgid and ctx and (msgctxt or '').find(ctx) >= 0:
#                 return trans
#             if orig == msgid and ctx:
#                 try:
#                     if re.search(ctx, msgctxt or ''):
#                         return trans
#                 except re.error:
#                     continue
#         return None

#     def _normalize_placeholders(self, msgstr):
#         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

#     def _extract_and_parse_existing_pos(self, zip_file_path):
#         existing_po_lookup = {}
#         if os.path.exists(self.temp_dir):
#             shutil.rmtree(self.temp_dir)
#         os.makedirs(self.temp_dir)
#         try:
#             with zipfile.ZipFile(zip_file_path, 'r') as zf:
#                 for member in zf.namelist():
#                     if member.endswith('.po'):
#                         zf.extract(member, self.temp_dir)
#                         path = os.path.join(self.temp_dir, member)
#                         try:
#                             po = polib.pofile(path)
#                             for entry in po:
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = entry.msgstr
#                                 if cleaned:
#                                     cleaned = self._normalize_placeholders(cleaned)
#                                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                                         cleaned = self._clean_translated_text(cleaned)
#                                         existing_po_lookup[key] = cleaned
#                         except Exception as e:
#                             print(f"Error parsing PO: {e}")
#         except Exception as e:
#             print(f"Error extracting ZIP: {e}")
#         finally:
#             shutil.rmtree(self.temp_dir, ignore_errors=True)
#         return existing_po_lookup

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = []
#         ph += self.printf_placeholder_regex.findall(text)
#         ph += self.icu_placeholder_regex.findall(text)
#         quoted = self.quoted_printf_regex.findall(text)
#         ph += quoted
#         normalized = []
#         for x in ph:
#             if isinstance(x, tuple):
#                 normalized.append('{' + x[0] + '}')
#             else:
#                 normalized.append(x)
#         return list(dict.fromkeys(normalized))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             orig_ph = self._collect_placeholders(original)
#             trans_ph = self._collect_placeholders(translated)
#             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
#         except Exception as e:
#             print(f"Placeholder validation failed: {e}")
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
#         for token in list(placeholder_map.keys()):
#             escaped = re.escape(token)
#             pattern = re.compile(r'\s*'.join(list(escaped)))
#             text = pattern.sub(token, text)
#         for token, ph in placeholder_map.items():
#             text = text.replace(token, ph)
#         return text

#     def _clean_translated_text(self, text):
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text

#     def _is_likely_untranslated(self, original_text, translated_text):
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
#         return raw_orig.strip().lower() == raw_trans.strip().lower()

#     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
#         if msgid in self.translation_rules_plural_templates:
#             lang_map = self.translation_rules_plural_templates[msgid]
#             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
#             if lang_map and plural_category and plural_category in lang_map:
#                 return lang_map[plural_category]
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
#         return None

#     def _is_valid_translation(self, text):
#         error_signs = ["Error 500", "That’s an error", "There was an error", "<html", "</html>", "<body>", "</body>", "Please try again later"]
#         lowered = text.lower()
#         return not any(s.lower() in lowered for s in error_signs)

#     def _retry(self, func, max_retries=3):
#         delay = 1.0
#         for i in range(max_retries):
#             try:
#                 return func()
#             except Exception as e:
#                 print(f"Attempt {i+1}/{max_retries} failed: {e}")
#                 if i == max_retries - 1:
#                     raise
#                 time.sleep(delay)
#                 delay *= 2

#     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
#         outputs: List[str] = [None] * len(texts)
#         to_query_idx = []
#         to_query = []
#         for i, t in enumerate(texts):
#             mem = memory.get(t)
#             if mem:
#                 outputs[i] = mem
#                 continue
#             key = (t, target_lang)
#             if key in self._cache:
#                 outputs[i] = self._cache[key]
#             else:
#                 to_query_idx.append(i)
#                 to_query.append(t)
#         if to_query:
#             def call():
#                 return self.translator_engine.translate(to_query, target_lang)
#             translated_list = self._retry(call, max_retries=3)
#             for j, out in enumerate(translated_list):
#                 idx = to_query_idx[j]
#                 outputs[idx] = out
#                 self._cache[(texts[idx], target_lang)] = out
#                 memory[texts[idx]] = out
#                 time.sleep(0.3)
#         return [x or "" for x in outputs]

#     def _fallback_translate(self, memory, text, target_lang):
#         mem = memory.get(text)
#         if mem:
#             return mem
#         key = (text, target_lang)
#         if key in self._cache:
#             return self._cache[key]

#         protected_text, placeholder_map = self._protect_markers(text)
#         try:
#             translated_protected = self._translate_batch(memory, [protected_text], target_lang)[0]
#             translated_protected = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", translated_protected)
#             translated = self._restore_markers(translated_protected, placeholder_map)
#             translated = self._clean_translated_text(translated)
#             if not self._is_valid_translation(translated):
#                 print(f"Invalid translation detected for '{text}' in '{target_lang}'. Using original.")
#                 return text
#             self._cache[key] = translated
#             memory[text] = translated
#             return translated
#         except exceptions.NotValidPayload as e:
#             print(f"Invalid payload for '{text}'. Error: {e}")
#             return text
#         except Exception as e:
#             print(f"Translation failed for '{text}' → '{target_lang}': {e}")
#             return text

#     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''

#         if msgid in lang_json:
#             self._counts["reused"] += 1
#             return lang_json[msgid], "lang.json"

#         if self._contains_protected_entity(msgid):
#             self._counts["reused"] += 1
#             return msgid, "Protected Entity"

#         custom = self._apply_custom_rules(msgid, target_lang)
#         if custom:
#             memory[msgid] = custom
#             self._counts["translated"] += 1
#             return custom, "Custom Rule"

#         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_lang)
#                 self._counts["translated"] += 1
#                 return fb, "Glossary (Fuzzy)"
#             memory[msgid] = gloss
#             self._counts["reused"] += 1
#             return gloss, "Glossary"

#         key_ctxt = (msgid, msgctxt)
#         if key_ctxt in existing_po_lookup:
#             existing = existing_po_lookup[key_ctxt]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_lang)
#                 self._counts["translated"] += 1
#                 return fb, "Existing PO (Fuzzy)"
#             memory[msgid] = existing
#             self._counts["reused"] += 1
#             return existing, "Existing PO"

#         fb = self._fallback_translate(memory, msgid, target_lang)
#         self._counts["translated"] += 1
#         return fb, "Machine Translation"

#     def _plural_header_for_lang(self, lang: str) -> str:
#         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split('_', 1)[0]) or "nplurals=2; plural=(n != 1);"

#     def _nplurals_from_header(self, header: str) -> int:
#         m = re.search(r"nplurals\s*=\s*(\d+)", header)
#         return int(m.group(1)) if m else 2

#     def _plural_categories_for_lang(self, lang: str) -> List[str]:
#         base = lang.split('_', 1)[0]
#         if PluralRule and Locale:
#             try:
#                 loc = Locale.parse(lang)
#             except Exception:
#                 try:
#                     loc = Locale.parse(base)
#                 except Exception:
#                     loc = None
#             if loc is not None:
#                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
#         return ["one", "other"]

#     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
#         if (self._contains_protected_entity(entry.msgid) or
#             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
#             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
#             result: Dict[int, str] = {}
#             for i in range(npl):
#                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
#             self._counts["reused"] += 1
#             return result

#         header = self._plural_header_for_lang(target_lang)
#         npl = self._nplurals_from_header(header)
#         categories = self._plural_categories_for_lang(target_lang)
#         if "one" not in categories:
#             categories = ["one"] + [c for c in categories if c != "one"]
#         if "other" not in categories:
#             categories = categories + ["other"]

#         templates_by_cat: Dict[str, str] = {}
#         for cat in categories:
#             custom = self._apply_custom_rules(entry.msgid, target_lang, plural_category=cat)
#             if custom:
#                 templates_by_cat[cat] = custom

#         if not templates_by_cat:
#             one_tmpl = self._fallback_translate(memory, entry.msgid, target_lang)
#             other_tmpl = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
#             templates_by_cat["one"] = one_tmpl
#             templates_by_cat["other"] = other_tmpl

#         idx_map: List[str] = []
#         if npl == 1:
#             idx_map = ["other"]
#         elif npl == 2:
#             idx_map = ["one", "other"]
#         elif npl == 3:
#             pref = ["one", "few", "other"]
#             idx_map = [c if c in categories else "other" for c in pref]
#         elif npl == 4:
#             pref = ["one", "two", "few", "other"]
#             idx_map = [c if c in categories else "other" for c in pref]
#         else:
#             pref = ["zero", "one", "two", "few", "many", "other"]
#             idx_map = [c if c in categories else "other" for c in pref[:npl]]

#         msgstr_plural: Dict[int, str] = {}
#         for i, cat in enumerate(idx_map):
#             tmpl = (templates_by_cat.get(cat) or
#                     templates_by_cat.get("other") or
#                     templates_by_cat.get("one") or
#                     (entry.msgid_plural or entry.msgid))
#             msgstr_plural[i] = tmpl
#         return msgstr_plural

#     def _snapshot_from_pot(self, pot: polib.POFile) -> Dict[str, Dict]:
#         snap = {}
#         for e in pot:
#             key = (e.msgctxt or '').strip() + "RECORD_SEPARATOR" + (e.msgid or '').strip() + "RECORD_SEPARATOR" + (e.msgid_plural or '').strip()
#             snap[key] = {
#                 "msgctxt": (e.msgctxt or '').strip(),
#                 "msgid": (e.msgid or '').strip(),
#                 "msgid_plural": (e.msgid_plural or '').strip()
#             }
#         return snap

#     def _diff_snapshots(self, old: Dict[str, Dict], new: Dict[str, Dict]) -> Dict[str, str]:
#         diff = {}
#         for k, nv in new.items():
#             if k not in old:
#                 diff[k] = "new"
#             else:
#                 ov = old[k]
#                 if nv["msgid"] != ov["msgid"] or nv["msgid_plural"] != ov["msgid_plural"]:
#                     diff[k] = "modified"
#                 else:
#                     diff[k] = "unchanged"
#         return diff

#     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
#         issues = []
#         if not translated:
#             issues.append("empty")
#         base = entry.msgid_plural or entry.msgid
#         if not self._placeholders_are_valid(base, translated):
#             issues.append("placeholders")
#         tags = self.html_tag_regex.findall(translated)
#         opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
#         closes = sum(1 for t in tags if t.startswith("</"))
#         if opens != closes:
#             issues.append("html_unbalanced")
#         if self._is_likely_untranslated(entry.msgid, translated):
#             issues.append("unchanged_like")
#         row = {
#             "msgctxt": entry.msgctxt or '',
#             "msgid": entry.msgid,
#             "msgid_plural": entry.msgid_plural or '',
#             "target_lang": target_lang,
#             "status": status,
#             "issues": ",".join(issues)
#         }
#         self._qa_rows.append(row)
#         if "placeholders" in issues or "empty" in issues:
#             self._counts["failed"] += 1

#     def _generate_report(self, target_language, version, timestamp, report_dir, reused_from=None):
#         report_json = os.path.join(report_dir, f"report-{target_language}-{timestamp}.json")
#         report_csv = os.path.join(report_dir, f"report-{target_language}-{timestamp}.csv")
#         report = {
#             "language": target_language,
#             "generated_at": timestamp,
#             "version": version,
#             "reused_from": os.path.basename(reused_from) if reused_from else None,
#             "counts": dict(self._counts),
#             "rows": self._qa_rows,
#         }
#         try:
#             with open(report_json, 'w', encoding='utf-8') as f:
#                 json.dump(report, f, ensure_ascii=False, indent=2)
#         except Exception as e:
#             print(f"JSON report failed: {e}")

#         try:
#             if self._qa_rows:
#                 headers = ["msgctxt", "msgid", "msgid_plural", "target_lang", "status", "issues"]
#                 with open(report_csv, 'w', encoding='utf-8', newline='') as f:
#                     w = csv.DictWriter(f, fieldnames=headers)
#                     w.writeheader()
#                     for r in self._qa_rows:
#                         w.writerow({k: r.get(k, "") for k in headers})
#         except Exception as e:
#             print(f"CSV report failed: {e}")

#     # FULLY FIXED run() — accepts None safely for zip_path and csv_path
#     def run(self, pot_path, zip_path=None, csv_path=None, target_langs=None, output_dir=None):
#         self._display_status("Starting Localization Tool")

#         self.pot_file_path = pot_path
#         self.zip_file_path = zip_path
#         self.csv_file_path = csv_path
#         valid_langs = [lang[0] for lang in settings.LANGUAGES]
#         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
#         if not self.target_languages:
#             self._display_error("No valid target languages provided.")
#             return False

#         project_name = os.path.basename(output_dir) if output_dir else "unknown"
#         self._display_status(f"Project: {project_name}")

#         try:
#             if not os.path.exists(pot_path):
#                 self._display_error("POT file not found.")
#                 return False

#             pot_file = polib.pofile(pot_path)

#             snapshot_path = self._get_snapshot_file_path(project_name)
#             prev_snap = {}
#             if os.path.exists(snapshot_path):
#                 try:
#                     with open(snapshot_path, 'r', encoding='utf-8') as f:
#                         prev_snap = json.load(f)
#                 except Exception as e:
#                     print(f"Snapshot LOAD FAILED: {e}")
#             new_snap = self._snapshot_from_pot(pot_file)
#             diff_map = self._diff_snapshots(prev_snap, new_snap)

#             for status in diff_map.values():
#                 self._counts[status] += 1

#             try:
#                 os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
#                 with open(snapshot_path, 'w', encoding='utf-8') as f:
#                     json.dump(new_snap, f, ensure_ascii=False, indent=2)
#             except Exception as e:
#                 print(f"FAILED TO SAVE SNAPSHOT: {e}")

#             # Safe loading — None values are handled
#             glossary = {}
#             if csv_path and os.path.exists(csv_path):
#                 glossary = self._parse_glossary_csv(csv_path)

#             existing_from_zip = {}
#             if zip_path and os.path.exists(zip_path):
#                 existing_from_zip = self._extract_and_parse_existing_pos(zip_path)

#             timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
#             report_dir = os.path.join(settings.MEDIA_ROOT, "reports", project_name)
#             os.makedirs(report_dir, exist_ok=True)

#             for target_language in self.target_languages:
#                 self._qa_rows = []
#                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

#                 memory = self._load_memory(project_name, target_language)
#                 lang_json_path = self._get_lang_json_path(output_dir, target_language)
#                 lang_json = {}
#                 if os.path.exists(lang_json_path):
#                     try:
#                         with open(lang_json_path, 'r', encoding='utf-8') as f:
#                             lang_json = json.load(f)
#                     except Exception as e:
#                         print(f"Failed to load {target_language}.json: {e}")

#                 version = 1
#                 while os.path.exists(os.path.join(output_dir, f"{target_language}-{version}.po")):
#                     version += 1
#                 existing_po_path = os.path.join(output_dir, f"{target_language}-{version - 1}.po") if version > 1 else None

#                 if existing_po_path and prev_snap == new_snap:
#                     try:
#                         po = polib.pofile(existing_po_path)
#                         out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
#                         out_mo = out_po.replace('.po', '.mo')
#                         po.save(out_po)
#                         po.save_as_mofile(out_mo)
#                         self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
#                         self._save_memory(memory, project_name, target_language)
#                         continue
#                     except Exception as e:
#                         print(f"Reuse failed: {e}")

#                 po = polib.POFile()
#                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
#                 po.metadata = {
#                     'Project-Id-Version': project_name,
#                     'POT-Creation-Date': now,
#                     'PO-Revision-Date': now,
#                     'Language': target_language,
#                     'MIME-Version': '1.0',
#                     'Content-Type': 'text/plain; charset=UTF-8',
#                     'Content-Transfer-Encoding': '8bit',
#                     'X-Generator': 'Colab Tool',
#                     'Plural-Forms': self._plural_header_for_lang(target_language)
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     key = (entry.msgctxt or '').strip() + "RECORD_SEPARATOR" + (entry.msgid or '').strip() + "RECORD_SEPARATOR" + (entry.msgid_plural or '').strip()
#                     status = diff_map.get(key, "new")

#                     try:
#                         if entry.msgid_plural:
#                             msgstr_plural = self._pluralize_entry(memory, lang_json, entry, target_language)
#                             new_entry = polib.POEntry(
#                                 msgid=entry.msgid,
#                                 msgid_plural=entry.msgid_plural,
#                                 msgstr_plural=msgstr_plural,
#                                 msgctxt=entry.msgctxt,
#                                 occurrences=entry.occurrences,
#                                 comment=entry.comment,
#                                 tcomment=entry.tcomment
#                             )
#                             if status == "modified":
#                                 new_entry.flags.append("fuzzy")
#                                 self._counts["fuzzy"] += 1
#                             po.append(new_entry)
#                             for s in msgstr_plural.values():
#                                 self._qa_check(entry, s, status, target_language)
#                             continue

#                         translated_msgstr, source = self._process_translation(
#                             memory, lang_json, entry, glossary, existing_from_zip, target_language
#                         )
#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgstr=translated_msgstr,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         if status == "modified" or "Fuzzy" in source:
#                             new_entry.flags.append("fuzzy")
#                             self._counts["fuzzy"] += 1
#                         po.append(new_entry)
#                         self._qa_check(entry, translated_msgstr, status, target_language)

#                     except Exception as e:
#                         print(f"Failed to process '{entry.msgid[:50]}…': {e}")
#                         po.append(polib.POEntry(msgid=entry.msgid, msgstr='', flags=['fuzzy']))
#                         self._counts["failed"] += 1

#                 out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 current_translations = {}
#                 for entry in po:
#                     if entry.msgid and entry.msgstr:
#                         current_translations[entry.msgid] = entry.msgstr
#                     if entry.msgid_plural and entry.msgstr_plural:
#                         for i, msg in entry.msgstr_plural.items():
#                             key = entry.msgid_plural if i > 0 else entry.msgid
#                             if msg:
#                                 current_translations[key] = msg

#                 lang_json.update(current_translations)
#                 try:
#                     with open(lang_json_path, 'w', encoding='utf-8') as f:
#                         json.dump(lang_json, f, ensure_ascii=False, indent=2, sort_keys=True)
#                 except Exception as e:
#                     print(f"Failed to save {target_language}.json: {e}")

#                 self._generate_report(target_language, version, timestamp, report_dir, existing_po_path)
#                 self._save_memory(memory, project_name, target_language)

#             self._display_status("Translation complete.")
#             return True

#         except Exception as e:
#             self._display_error(f"Unexpected error: {e}")
#             return False




# # localizationtool/localization_logic.py
# # FINAL VERSION — FLAT GLOBAL JED JSON + NO DUPLICATES + FULL REUSE + ROBUST LOADING (2025-12-15)
# import polib
# import csv
# import zipfile
# import os
# import shutil
# from datetime import datetime
# from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# import re
# import time
# import json
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path

# try:
#     from babel.core import Locale
#     from babel.plural import PluralRule
# except ImportError:
#     Locale = None
#     PluralRule = None


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "INVISIBLE_SEPARATOR"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         translator = _GoogleTranslator(source='auto', target=target_lang)
#         out = translator.translate(joined)
#         if isinstance(out, list):
#             return [str(x) for x in out]
#         parts = str(out).split(self._SEP)
#         if len(parts) != len(texts):
#             parts = []
#             for t in texts:
#                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
#         return parts


# class ColabLocalizationTool:
#     def __init__(self, memory_base_dir: str = None):
#         self.pot_file_path = None
#         self.zip_file_path = None
#         self.csv_file_path = None
#         self.target_languages: List[str] = []
#         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")

#         # GLOBAL JED JSON FOLDER
#         self.jed_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.jed_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
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

#         self.translation_rules_plural_templates = {
#             "%s min read": {
#                 "en": {"one": "%s min read", "other": "%s mins read"},
#                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
#                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
#                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
#                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
#                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
#                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
#                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
#                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
#                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
#                 "zh-CN": {"other": "%s 分钟阅读"},
#             }
#         }

#         self._qa_rows: List[Dict] = []
#         self._counts = {"new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0}
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine: _Translator = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);", "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);", "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);", "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);", "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
#             "it": "nplurals=2; plural=(n != 1);", "ja": "nplurals=1; plural=0;",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "nl": "nplurals=2; plural=(n != 1);", "zh": "nplurals=1; plural=0;",
#             "id": "nplurals=1; plural=0;", "th": "nplurals=1; plural=0;",
#             "tl": "nplurals=2; plural=(n != 1);", "ko": "nplurals=1; plural=0;",
#             "en-gb": "nplurals=2; plural=(n != 1);", "sw": "nplurals=2; plural=(n != 1);",
#             "da": "nplurals=2; plural=(n != 1);", "fi": "nplurals=2; plural=(n != 1);",
#             "is": "nplurals=2; plural=(n != 1);", "no": "nplurals=2; plural=(n != 1);",
#             "sv": "nplurals=2; plural=(n != 1);", "zh-CN": "nplurals=1; plural=0;",
#         }

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _parse_glossary_csv(self, csv_file_path):
#         glossary_lookup: Dict[Tuple[str, str], str] = {}
#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         trans = self._normalize_placeholders(trans)
#                         glossary_lookup[(orig, ctx)] = trans
#                 return glossary_lookup
#             except Exception as e:
#                 print(f"Glossary parse error with {encoding}: {e}")
#         return glossary_lookup

#     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
#         key = (msgid, msgctxt or '')
#         if key in glossary_lookup:
#             return glossary_lookup[key]
#         return None

#     def _normalize_placeholders(self, msgstr):
#         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

#     def _extract_and_parse_existing_pos(self, zip_file_path):
#         existing_po_lookup = {}
#         if os.path.exists(self.temp_dir):
#             shutil.rmtree(self.temp_dir)
#         os.makedirs(self.temp_dir)

#         try:
#             with zipfile.ZipFile(zip_file_path, 'r') as zf:
#                 for member in zf.namelist():
#                     if member.endswith('.po') and not member.startswith('__MACOSX/'):
#                         zf.extract(member, self.temp_dir)
#                         path = os.path.join(self.temp_dir, member)

#                         try:
#                             detection = from_path(path).best()
#                             encoding = detection.encoding if detection and detection.encoding else 'utf-8'
#                             if encoding in ('ascii', None):
#                                 encoding = 'utf-8'

#                             po = polib.pofile(path, encoding=encoding)

#                             for entry in po:
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = entry.msgstr.strip()
#                                 if cleaned:
#                                     cleaned = self._normalize_placeholders(cleaned)
#                                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                                         cleaned = self._clean_translated_text(cleaned)
#                                         existing_po_lookup[key] = cleaned

#                             print(f"Loaded {member} → encoding: {encoding}")

#                         except Exception as e:
#                             print(f"Failed to parse {member} (tried {encoding}): {e}")
#                             for fallback in ['windows-1252', 'iso-8859-1', 'cp1252', 'latin1']:
#                                 try:
#                                     po = polib.pofile(path, encoding=fallback)
#                                     print(f"Success with fallback: {fallback}")
#                                     for entry in po:
#                                         key = (entry.msgid, entry.msgctxt or '')
#                                         cleaned = entry.msgstr.strip()
#                                         if cleaned:
#                                             cleaned = self._normalize_placeholders(cleaned)
#                                             if self._placeholders_are_valid(entry.msgid, cleaned):
#                                                 cleaned = self._clean_translated_text(cleaned)
#                                                 existing_po_lookup[key] = cleaned
#                                     break
#                                 except:
#                                     continue

#         except Exception as e:
#             print(f"Error extracting ZIP: {e}")
#         finally:
#             shutil.rmtree(self.temp_dir, ignore_errors=True)

#         return existing_po_lookup

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = []
#         ph += self.printf_placeholder_regex.findall(text)
#         ph += self.icu_placeholder_regex.findall(text)
#         quoted = self.quoted_printf_regex.findall(text)
#         ph += quoted
#         normalized = []
#         for x in ph:
#             if isinstance(x, tuple):
#                 normalized.append('{' + x[0] + '}')
#             else:
#                 normalized.append(x)
#         return list(dict.fromkeys(normalized))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             orig_ph = self._collect_placeholders(original)
#             trans_ph = self._collect_placeholders(translated)
#             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
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

#     def _clean_translated_text(self, text):
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text

#     def _is_likely_untranslated(self, original_text, translated_text):
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
#         return raw_orig.strip().lower() == raw_trans.strip().lower()

#     def _apply_custom_rules(self, msgid, target_lang, plural_category: Optional[str] = None):
#         if msgid in self.translation_rules_plural_templates:
#             lang_map = self.translation_rules_plural_templates[msgid]
#             lang_map = lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
#             if lang_map and plural_category and plural_category in lang_map:
#                 return lang_map[plural_category]
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_lang) or lang_map.get(target_lang.split("_", 1)[0])
#         return None

#     def _is_valid_translation(self, text):
#         error_signs = ["Error 500", "That’s an error", "<html", "</html>"]
#         return not any(s.lower() in text.lower() for s in error_signs)

#     def _retry(self, func, max_retries=3):
#         delay = 1.0
#         for i in range(max_retries):
#             try:
#                 return func()
#             except Exception as e:
#                 print(f"Attempt {i+1} failed: {e}")
#                 if i == max_retries - 1:
#                     raise
#                 time.sleep(delay)
#                 delay *= 2

#     def _translate_batch(self, memory, texts: List[str], target_lang: str) -> List[str]:
#         outputs = [None] * len(texts)
#         to_query = []
#         to_query_idx = []
#         for i, t in enumerate(texts):
#             if t in memory:
#                 outputs[i] = memory[t]
#             elif (t, target_lang) in self._cache:
#                 outputs[i] = self._cache[(t, target_lang)]
#             else:
#                 to_query.append(t)
#                 to_query_idx.append(i)
#         if to_query:
#             translated = self._retry(lambda: self.translator_engine.translate(to_query, target_lang))
#             for idx, trans in zip(to_query_idx, translated):
#                 outputs[idx] = trans
#                 self._cache[(texts[idx], target_lang)] = trans
#                 memory[texts[idx]] = trans
#                 time.sleep(0.3)
#         return [x or "" for x in outputs]

#     def _fallback_translate(self, memory, text, target_lang):
#         if text in memory:
#             return memory[text]
#         if (text, target_lang) in self._cache:
#             return self._cache[(text, target_lang)]
#         protected, map_ = self._protect_markers(text)
#         try:
#             trans = self._translate_batch(memory, [protected], target_lang)[0]
#             trans = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", trans)
#             result = self._restore_markers(trans, map_)
#             result = self._clean_translated_text(result)
#             if self._is_valid_translation(result):
#                 self._cache[(text, target_lang)] = result
#                 memory[text] = result
#                 return result
#             return text
#         except:
#             return text

#     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_lang):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         full_key = f"{msgctxt}||{msgid}"

#         # 1. GLOBAL MEMORY — with context first
#         if full_key in memory:
#             self._counts["reused"] += 1
#             return memory[full_key], "Global JSON (with context)"

#         # 2. Fallback: same string without context
#         if msgid in memory:
#             self._counts["reused"] += 1
#             return memory[msgid], "Global JSON (fallback)"

#         # 3. Old per-theme JSON
#         if msgid in lang_json:
#             self._counts["reused"] += 1
#             return lang_json[msgid], "lang.json"

#         # 4. Protected
#         if self._contains_protected_entity(msgid):
#             self._counts["reused"] += 1
#             return msgid, "Protected"

#         # 5. Custom rules
#         custom = self._apply_custom_rules(msgid, target_lang)
#         if custom:
#             memory[full_key] = custom
#             memory[msgid] = custom
#             self._counts["translated"] += 1
#             return custom, "Custom Rule"

#         # 6. Glossary
#         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_lang)
#                 self._counts["translated"] += 1
#                 return fb, "Glossary (Fuzzy)"
#             memory[full_key] = gloss
#             memory[msgid] = gloss
#             self._counts["reused"] += 1
#             return gloss, "Glossary"

#         # 7. ZIP .po files
#         key = (msgid, msgctxt)
#         if key in existing_po_lookup:
#             existing = existing_po_lookup[key]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_lang)
#                 self._counts["translated"] += 1
#                 return fb, "Existing PO (Fuzzy)"
#             memory[full_key] = existing
#             memory[msgid] = existing
#             self._counts["reused"] += 1
#             return existing, "Existing PO"

#         # 8. Google Translate
#         fb = self._fallback_translate(memory, msgid, target_lang)
#         memory[full_key] = fb
#         memory[msgid] = fb
#         self._counts["translated"] += 1
#         return fb, "Google Translate"

#     def _plural_header_for_lang(self, lang: str) -> str:
#         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split("_", 1)[0]) or "nplurals=2; plural=(n != 1);"

#     def _nplurals_from_header(self, header: str) -> int:
#         m = re.search(r"nplurals\s*=\s*(\d+)", header)
#         return int(m.group(1)) if m else 2

#     def _plural_categories_for_lang(self, lang: str) -> List[str]:
#         base = lang.split('_', 1)[0]
#         if PluralRule and Locale:
#             try:
#                 loc = Locale.parse(lang)
#             except:
#                 try:
#                     loc = Locale.parse(base)
#                 except:
#                     return ["one", "other"]
#             if loc:
#                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
#         return ["one", "other"]

#     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_lang: str) -> Dict[int, str]:
#         if (self._contains_protected_entity(entry.msgid) or
#             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
#             npl = self._nplurals_from_header(self._plural_header_for_lang(target_lang))
#             result = {}
#             for i in range(npl):
#                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
#             self._counts["reused"] += 1
#             return result

#         header = self._plural_header_for_lang(target_lang)
#         npl = self._nplurals_from_header(header)
#         categories = self._plural_categories_for_lang(target_lang)
#         if "one" not in categories:
#             categories = ["one"] + [c for c in categories if c != "one"]
#         if "other" not in categories:
#             categories.append("other")

#         templates = {}
#         for cat in categories:
#             custom = self._apply_custom_rules(entry.msgid, target_lang, cat)
#             if custom:
#                 templates[cat] = custom

#         if not templates:
#             one = self._fallback_translate(memory, entry.msgid, target_lang)
#             other = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_lang)
#             templates["one"] = one
#             templates["other"] = other

#         idx_map = ["other"] * npl
#         if npl >= 2:
#             idx_map[1] = "one"
#         if npl >= 3:
#             idx_map[2] = "few" if "few" in categories else "other"
#         if npl >= 4:
#             idx_map[3] = "many" if "many" in categories else "other"

#         result = {}
#         for i, cat in enumerate(idx_map):
#             result[i] = templates.get(cat) or templates.get("other") or templates.get("one") or (entry.msgid_plural if i > 0 else entry.msgid)
#         return result

#     def _qa_check(self, entry: polib.POEntry, translated: str, status: str, target_lang: str):
#         issues = []
#         if not translated:
#             issues.append("empty")
#         base = entry.msgid_plural or entry.msgid
#         if not self._placeholders_are_valid(base, translated):
#             issues.append("placeholders")
#         if self._is_likely_untranslated(entry.msgid, translated):
#             issues.append("unchanged_like")
#         if issues:
#             self._counts["failed"] += 1

#     def _generate_report(self, target_language, version, timestamp, report_dir, reused_from=None):
#         pass

#     def run(self, pot_path, zip_path=None, csv_path=None, target_langs=None, output_dir=None):
#         self._display_status("Starting Localization Tool")

#         # PROJECT NAME = POT FILENAME (so same POT = same memory forever)
#         project_name = os.path.splitext(os.path.basename(pot_path))[0]
#         self._display_status(f"Project: {project_name}")

#         self.pot_file_path = pot_path
#         valid_langs = [lang[0] for lang in settings.LANGUAGES]
#         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
#         if not self.target_languages:
#             self._display_error("No valid target languages provided.")
#             return False

#         try:
#             if not os.path.exists(pot_path):
#                 self._display_error("POT file not found.")
#                 return False

#             pot_file = polib.pofile(pot_path)

#             glossary = {}
#             if csv_path and os.path.exists(csv_path):
#                 glossary = self._parse_glossary_csv(csv_path)

#             existing_from_zip = {}
#             if zip_path and os.path.exists(zip_path):
#                 existing_from_zip = self._extract_and_parse_existing_pos(zip_path)

#             for target_language in self.target_languages:
#                 self._qa_rows = []
#                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

#                 # GLOBAL JED MEMORY — ROBUST LOADING
#                 jed_path = os.path.join(self.jed_dir, f"{target_language}.json")
#                 translations_memory = {}

#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             full_jed = json.load(f)
#                         translations_memory = {k: v for k, v in full_jed.items() if k != ""}
#                         self._display_status(f"Loaded {len(translations_memory)} existing translations for {target_language}")
#                     except Exception as e:
#                         self._display_error(f"Failed to load {jed_path}: {e} — starting fresh")
#                         translations_memory = {}
#                 else:
#                     self._display_status(f"No {target_language}.json found — creating new")

#                 version = 1
#                 while os.path.exists(os.path.join(output_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
#                 po.metadata = {
#                     'Project-Id-Version': project_name,
#                     'POT-Creation-Date': now,
#                     'PO-Revision-Date': now,
#                     'Language': target_language,
#                     'MIME-Version': '1.0',
#                     'Content-Type': 'text/plain; charset=UTF-8',
#                     'Content-Transfer-Encoding': '8bit',
#                     'X-Generator': 'Colab Tool',
#                     'Plural-Forms': self._plural_header_for_lang(target_language)
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     translated_msgstr, source = self._process_translation(
#                         translations_memory, {}, entry, glossary, existing_from_zip, target_language
#                     )

#                     new_entry = polib.POEntry(
#                         msgid=entry.msgid,
#                         msgstr=translated_msgstr,
#                         msgctxt=entry.msgctxt,
#                         occurrences=entry.occurrences,
#                         comment=entry.comment,
#                         tcomment=entry.tcomment
#                     )
#                     po.append(new_entry)
#                     self._qa_check(entry, translated_msgstr, "new", target_language)

#                     # UPDATE ONLY IF NEW
#                     if "reused" not in source and "Protected" not in source:
#                         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#                         if entry.msgid_plural:
#                             plurals = self._pluralize_entry(translations_memory, {}, entry, target_language)
#                             npl = self._nplurals_from_header(self._plural_header_for_lang(target_language))
#                             translations_memory[full_key] = [plurals.get(i, "") for i in range(npl)]
#                             translations_memory[entry.msgid] = [plurals.get(i, "") for i in range(npl)]
#                         else:
#                             translations_memory[full_key] = [translated_msgstr]
#                             translations_memory[entry.msgid] = [translated_msgstr]

#                 # Save .po/.mo
#                 out_po = os.path.join(output_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 # SAVE CLEAN FLAT JSON
#                 final_jed = translations_memory.copy()
#                 final_jed[""] = {
#                     "lang": target_language,
#                     "plural_forms": self._plural_header_for_lang(target_language)
#                 }
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(final_jed, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} completed (v{version}) — Reused: {self._counts['reused']}, Translated: {self._counts['translated']}")

#             self._display_status("Translation complete.")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Unexpected error: {e}\n{traceback.format_exc()}")
#             return False



#code test till now 
# import polib
# import csv
# import zipfile
# import os
# import shutil
# from datetime import datetime
# from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# import re
# import time
# import json
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path

# try:
#     from babel.core import Locale
#     from babel.plural import PluralRule
# except ImportError:
#     Locale = None
#     PluralRule = None


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "INVISIBLE_SEPARATOR"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         translator = _GoogleTranslator(source='auto', target=target_lang)
#         out = translator.translate(joined)
#         if isinstance(out, list):
#             return [str(x) for x in out]
#         parts = str(out).split(self._SEP)
#         if len(parts) != len(texts):
#             parts = []
#             for t in texts:
#                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
#         return parts


# class ColabLocalizationTool:
#     def __init__(self, memory_base_dir: str = None):
#         self.pot_file_path = None
#         self.zip_file_path = None
#         self.csv_file_path = None
#         self.target_languages: List[str] = []
#         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")

#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
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

#         self.translation_rules_plural_templates = {
#             "%s min read": {
#                 "en": {"one": "%s min read", "other": "%s mins read"},
#                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
#                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
#                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
#                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
#                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
#                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
#                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
#                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
#                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
#                 "zh-CN": {"other": "%s 分钟阅读"},
#             }
#         }

#         self._qa_rows: List[Dict] = []
#         self._counts = {"new": 0, "modified": 0, "unchanged": 0, "reused": 0, "fuzzy": 0, "failed": 0, "translated": 0}
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine: _Translator = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);", "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);", "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);", "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);", "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
#             "it": "nplurals=2; plural=(n != 1);", "ja": "nplurals=1; plural=0;",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "nl": "nplurals=2; plural=(n != 1);", "zh": "nplurals=1; plural=0;",
#             "id": "nplurals=1; plural=0;", "th": "nplurals=1; plural=0;",
#             "tl": "nplurals=2; plural=(n != 1);", "ko": "nplurals=1; plural=0;",
#             "en-gb": "nplurals=2; plural=(n != 1);", "sw": "nplurals=2; plural=(n != 1);",
#             "da": "nplurals=2; plural=(n != 1);", "fi": "nplurals=2; plural=(n != 1);",
#             "is": "nplurals=2; plural=(n != 1);", "no": "nplurals=2; plural=(n != 1);",
#             "sv": "nplurals=2; plural=(n != 1);", "zh-CN": "nplurals=1; plural=0;",
#         }

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _parse_glossary_csv(self, csv_file_path):
#         glossary_lookup: Dict[Tuple[str, str], str] = {}
#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         trans = self._normalize_placeholders(trans)
#                         glossary_lookup[(orig, ctx)] = trans
#                 return glossary_lookup
#             except Exception as e:
#                 print(f"Glossary parse error with {encoding}: {e}")
#         return glossary_lookup

#     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
#         key = (msgid, msgctxt or '')
#         if key in glossary_lookup:
#             return glossary_lookup[key]
#         return None

#     def _normalize_placeholders(self, msgstr):
#         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

#     def _extract_and_parse_existing_pos(self, zip_file_path):
#         existing_po_lookup = {}
#         if os.path.exists(self.temp_dir):
#             shutil.rmtree(self.temp_dir)
#         os.makedirs(self.temp_dir)

#         try:
#             with zipfile.ZipFile(zip_file_path, 'r') as zf:
#                 for member in zf.namelist():
#                     if member.endswith('.po') and not member.startswith('__MACOSX/'):
#                         zf.extract(member, self.temp_dir)
#                         path = os.path.join(self.temp_dir, member)

#                         try:
#                             detection = from_path(path).best()
#                             encoding = detection.encoding if detection and detection.encoding else 'utf-8'
#                             if encoding in ('ascii', None):
#                                 encoding = 'utf-8'

#                             po = polib.pofile(path, encoding=encoding)

#                             for entry in po:
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = entry.msgstr.strip()
#                                 if cleaned:
#                                     cleaned = self._normalize_placeholders(cleaned)
#                                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                                         cleaned = self._clean_translated_text(cleaned)
#                                         existing_po_lookup[key] = cleaned

#                             print(f"Loaded {member} → encoding: {encoding}")

#                         except Exception as e:
#                             print(f"Failed to parse {member} (tried {encoding}): {e}")
#                             for fallback in ['windows-1252', 'iso-8859-1', 'cp1252', 'latin1']:
#                                 try:
#                                     po = polib.pofile(path, encoding=fallback)
#                                     print(f"Success with fallback: {fallback}")
#                                     for entry in po:
#                                         key = (entry.msgid, entry.msgctxt or '')
#                                         cleaned = entry.msgstr.strip()
#                                         if cleaned:
#                                             cleaned = self._normalize_placeholders(cleaned)
#                                             if self._placeholders_are_valid(entry.msgid, cleaned):
#                                                 cleaned = self._clean_translated_text(cleaned)
#                                                 existing_po_lookup[key] = cleaned
#                                     break
#                                 except:
#                                     continue

#         except Exception as e:
#             print(f"Error extracting ZIP: {e}")
#         finally:
#             shutil.rmtree(self.temp_dir, ignore_errors=True)

#         return existing_po_lookup

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = []
#         ph += self.printf_placeholder_regex.findall(text)
#         ph += self.icu_placeholder_regex.findall(text)
#         quoted = self.quoted_printf_regex.findall(text)
#         ph += quoted
#         normalized = []
#         for x in ph:
#             if isinstance(x, tuple):
#                 normalized.append('{' + x[0] + '}')
#             else:
#                 normalized.append(x)
#         return list(dict.fromkeys(normalized))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             orig_ph = self._collect_placeholders(original)
#             trans_ph = self._collect_placeholders(translated)
#             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
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

#     def _clean_translated_text(self, text):
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text

#     def _is_likely_untranslated(self, original_text, translated_text):
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
#         return raw_orig.strip().lower() == raw_trans.strip().lower()

#     def _apply_custom_rules(self, msgid, target_language, plural_category: Optional[str] = None):
#         if msgid in self.translation_rules_plural_templates:
#             lang_map = self.translation_rules_plural_templates[msgid]
#             lang_map = lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#             if lang_map and plural_category and plural_category in lang_map:
#                 return lang_map[plural_category]
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#         return None

#     def _is_valid_translation(self, text):
#         error_signs = ["Error 500", "That’s an error", "<html", "</html>"]
#         return not any(s.lower() in text.lower() for s in error_signs)

#     def _retry(self, func, max_retries=3):
#         delay = 1.0
#         for i in range(max_retries):
#             try:
#                 return func()
#             except Exception as e:
#                 print(f"Attempt {i+1} failed: {e}")
#                 if i == max_retries - 1:
#                     raise
#                 time.sleep(delay)
#                 delay *= 2

#     def _translate_batch(self, memory, texts: List[str], target_language: str) -> List[str]:
#         outputs = [None] * len(texts)
#         to_query = []
#         to_query_idx = []
#         for i, t in enumerate(texts):
#             if t in memory:
#                 outputs[i] = memory[t]
#             elif (t, target_language) in self._cache:
#                 outputs[i] = self._cache[(t, target_language)]
#             else:
#                 to_query.append(t)
#                 to_query_idx.append(i)
#         if to_query:
#             translated = self._retry(lambda: self.translator_engine.translate(to_query, target_language))
#             for idx, trans in zip(to_query_idx, translated):
#                 outputs[idx] = trans
#                 self._cache[(texts[idx], target_language)] = trans
#                 memory[texts[idx]] = trans
#                 time.sleep(0.3)
#         return [x or "" for x in outputs]

#     def _fallback_translate(self, memory, text, target_language):
#         if text in memory:
#             return memory[text]
#         if (text, target_language) in self._cache:
#             return self._cache[(text, target_language)]
#         protected, map_ = self._protect_markers(text)
#         try:
#             trans = self._translate_batch(memory, [protected], target_language)[0]
#             trans = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", trans)
#             result = self._restore_markers(trans, map_)
#             result = self._clean_translated_text(result)
#             if self._is_valid_translation(result):
#                 self._cache[(text, target_language)] = result
#                 memory[text] = result
#                 return result
#             return text
#         except:
#             return text

#     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_language):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         full_key = f"{msgctxt}||{msgid}"

#         if full_key in memory and isinstance(memory[full_key], str):
#             self._counts["reused"] += 1
#             return memory[full_key], "Global JSON (with context)"

#         if msgid in memory and isinstance(memory[msgid], str):
#             self._counts["reused"] += 1
#             return memory[msgid], "Global JSON (fallback)"

#         if msgid in lang_json:
#             self._counts["reused"] += 1
#             return lang_json[msgid], "lang.json"

#         if self._contains_protected_entity(msgid):
#             self._counts["reused"] += 1
#             return msgid, "Protected"

#         custom = self._apply_custom_rules(msgid, target_language)
#         if custom:
#             memory[full_key] = custom
#             memory[msgid] = custom
#             self._counts["translated"] += 1
#             return custom, "Custom Rule"

#         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated"] += 1
#                 return fb, "Glossary (Fuzzy)"
#             memory[full_key] = gloss
#             memory[msgid] = gloss
#             self._counts["reused"] += 1
#             return gloss, "Glossary"

#         key = (msgid, msgctxt)
#         if key in existing_po_lookup:
#             existing = existing_po_lookup[key]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated"] += 1
#                 return fb, "Existing PO (Fuzzy)"
#             memory[full_key] = existing
#             memory[msgid] = existing
#             self._counts["reused"] += 1
#             return existing, "Existing PO"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         memory[full_key] = fb
#         memory[msgid] = fb
#         self._counts["translated"] += 1
#         return fb, "Google Translate"

#     def _plural_header_for_lang(self, lang: str) -> str:
#         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split("_", 1)[0]) or "nplurals=2; plural=(n != 1);"

#     def _nplurals_from_header(self, header: str) -> int:
#         m = re.search(r"nplurals\s*=\s*(\d+)", header)
#         return int(m.group(1)) if m else 2

#     def _plural_categories_for_lang(self, lang: str) -> List[str]:
#         base = lang.split('_', 1)[0]
#         if PluralRule and Locale:
#             try:
#                 loc = Locale.parse(lang)
#             except:
#                 try:
#                     loc = Locale.parse(base)
#                 except:
#                     return ["one", "other"]
#             if loc:
#                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
#         return ["one", "other"]

#     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         msgid = entry.msgid
#         full_key = f"{entry.msgctxt or ''}||{msgid}"

#         npl = self._nplurals_from_header(self._plural_header_for_lang(target_language))

#         # REUSE FROM MEMORY (list)
#         for key in [full_key, msgid]:
#             if key in memory and isinstance(memory[key], list) and len(memory[key]) == npl:
#                 result = {i: memory[key][i] for i in range(npl)}
#                 self._counts["reused"] += 1
#                 return result

#         if (self._contains_protected_entity(entry.msgid) or
#             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
#             result = {}
#             for i in range(npl):
#                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
#             self._counts["reused"] += 1
#             return result

#         header = self._plural_header_for_lang(target_language)
#         categories = self._plural_categories_for_lang(target_language)
#         if "one" not in categories:
#             categories = ["one"] + [c for c in categories if c != "one"]
#         if "other" not in categories:
#             categories.append("other")

#         templates = {}
#         for cat in categories:
#             custom = self._apply_custom_rules(entry.msgid, target_language, cat)
#             if custom:
#                 templates[cat] = custom

#         if not templates:
#             one = self._fallback_translate(memory, entry.msgid, target_language)
#             other = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)
#             templates["one"] = one
#             templates["other"] = other

#         idx_map = ["other"] * npl
#         if npl >= 2:
#             idx_map[1] = "one"
#         if npl >= 3:
#             idx_map[2] = "few" if "few" in categories else "other"
#         if npl >= 4:
#             idx_map[3] = "many" if "many" in categories else "other"

#         result = {}
#         for i, cat in enumerate(idx_map):
#             result[i] = templates.get(cat) or templates.get("other") or templates.get("one") or (entry.msgid_plural if i > 0 else entry.msgid)

#         # Save as list in memory
#         plurals_list = [result[i] for i in range(npl)]
#         memory[full_key] = plurals_list
#         memory[msgid] = plurals_list

#         return result

#     def _single_qa_check(self, entry: polib.POEntry, translated: str, status: str, target_language: str):
#         issues = []
#         if not translated:
#             issues.append("empty")
#         base = entry.msgid_plural or entry.msgid
#         if not self._placeholders_are_valid(base, translated):
#             issues.append("placeholders")
#         if self._is_likely_untranslated(entry.msgid, translated):
#             issues.append("unchanged_like")
#         if issues:
#             self._counts["failed"] += 1

#     def _qa_check(self, entry: polib.POEntry, translated, status: str, target_language: str):
#         if isinstance(translated, list):
#             for t in translated:
#                 self._single_qa_check(entry, t, status, target_language)
#         else:
#             self._single_qa_check(entry, translated, status, target_language)



#     def run(self, pot_path, zip_path=None, csv_path=None, target_langs=None, output_dir=None):
#         self._display_status("Starting Localization Tool")

#         project_name = os.path.splitext(os.path.basename(pot_path))[0]
#         self._display_status(f"Project: {project_name}")

#         translations_base = os.path.join(settings.MEDIA_ROOT, "translations")
#         os.makedirs(translations_base, exist_ok=True)
#         project_dir = os.path.join(translations_base, project_name)
#         os.makedirs(project_dir, exist_ok=True)

#         self.pot_file_path = pot_path
#         valid_langs = [lang[0] for lang in settings.LANGUAGES]
#         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
#         if not self.target_languages:
#             self._display_error("No valid target languages provided.")
#             return True

#         try:
#             if not os.path.exists(pot_path):
#                 self._display_error("POT file not found.")
#                 return True

#             pot_file = polib.pofile(pot_path)

#             glossary = {}
#             if csv_path and os.path.exists(csv_path):
#                 glossary = self._parse_glossary_csv(csv_path)

#             existing_from_zip = {}
#             if zip_path and os.path.exists(zip_path):
#                 existing_from_zip = self._extract_and_parse_existing_pos(zip_path)

#             for target_language in self.target_languages:
#                 self._qa_rows = []
#                 self._counts.update({"reused": 0, "fuzzy": 0, "failed": 0, "translated": 0})

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}

#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             full_jed = json.load(f)
#                         translations_memory = {k: v for k, v in full_jed.items() if k != ""}
#                         self._display_status(f"Loaded {len(translations_memory)} strings from {target_language}.json")
#                     except Exception as e:
#                         self._display_error(f"Failed to load {jed_path}: {e} — starting fresh")
#                         translations_memory = {}

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
#                 po.metadata = {
#                     'Project-Id-Version': project_name,
#                     'POT-Creation-Date': now,
#                     'PO-Revision-Date': now,
#                     'Language': target_language,
#                     'MIME-Version': '1.0',
#                     'Content-Type': 'text/plain; charset=UTF-8',
#                     'Content-Transfer-Encoding': '8bit',
#                     'X-Generator': 'Colab Tool',
#                     'Plural-Forms': self._plural_header_for_lang(target_language)
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     source = "New"

#                     if entry.msgid_plural:
#                         plurals_dict = self._pluralize_entry(translations_memory, {}, entry, target_language)
#                         plurals_list = [plurals_dict.get(i, "") for i in range(self._nplurals_from_header(self._plural_header_for_lang(target_language)))]
#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr="",  # Critical
#                             msgstr_plural=plurals_dict,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, plurals_list, "new", target_language)
#                     else:
#                         translated_msgstr, source = self._process_translation(
#                             translations_memory, {}, entry, glossary, existing_from_zip, target_language
#                         )
#                         # FINAL FIX: Force string even if memory has list
#                         if isinstance(translated_msgstr, list):
#                             translated_msgstr = translated_msgstr[0] if translated_msgstr else ""

#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgstr=translated_msgstr,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, translated_msgstr, "new", target_language)

#                     if source != "Global JSON (with context)" and source != "Global JSON (fallback)":
#                         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#                         if entry.msgid_plural:
#                             translations_memory[full_key] = plurals_list
#                             translations_memory[entry.msgid] = plurals_list
#                         else:
#                             translations_memory[full_key] = [translated_msgstr]
#                             translations_memory[entry.msgid] = [translated_msgstr]

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 final_jed = translations_memory.copy()
#                 final_jed[""] = {
#                     "lang": target_language,
#                     "plural_forms": self._plural_header_for_lang(target_language)
#                 }
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(final_jed, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} completed (v{version}) - Reused: {self._counts['reused']}, Translated: {self._counts['translated']}")

#             self._display_status("Translation complete.")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Unexpected error: {e}\n{traceback.format_exc()}")
#             return False




# localizationtool/localization_logic.py best code aile samma ko
# FINAL VERSION — MAXIMUM JSON REUSE + DETAILED STATISTICS + NO ERRORS (2025-12-17)

# import polib
# import csv
# import zipfile
# import os
# import shutil
# from datetime import datetime
# from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# import re
# import time
# import json
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path

# try:
#     from babel.core import Locale
#     from babel.plural import PluralRule
# except ImportError:
#     Locale = None
#     PluralRule = None


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "INVISIBLE_SEPARATOR"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         translator = _GoogleTranslator(source='auto', target=target_lang)
#         out = translator.translate(joined)
#         if isinstance(out, list):
#             return [str(x) for x in out]
#         parts = str(out).split(self._SEP)
#         if len(parts) != len(texts):
#             parts = []
#             for t in texts:
#                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
#         return parts


# class ColabLocalizationTool:
#     def __init__(self, memory_base_dir: str = None):
#         self.pot_file_path = None
#         self.zip_file_path = None
#         self.csv_file_path = None
#         self.target_languages: List[str] = []
#         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")

#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
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

#         self.translation_rules_plural_templates = {
#             "%s min read": {
#                 "en": {"one": "%s min read", "other": "%s mins read"},
#                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
#                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
#                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
#                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
#                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
#                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
#                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
#                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
#                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
#                 "zh-CN": {"other": "%s 分钟阅读"},
#             }
#         }

#         self._qa_rows: List[Dict] = []
#         self._counts = {
#             "total": 0,
#             "reused_json": 0,
#             "reused_glossary": 0,
#             "reused_zip": 0,
#             "translated_google": 0,
#             "protected": 0,
#             "failed": 0,
#         }
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine: _Translator = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);", "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);", "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);", "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);", "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
#             "it": "nplurals=2; plural=(n != 1);", "ja": "nplurals=1; plural=0;",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "nl": "nplurals=2; plural=(n != 1);", "zh": "nplurals=1; plural=0;",
#             "id": "nplurals=1; plural=0;", "th": "nplurals=1; plural=0;",
#             "tl": "nplurals=2; plural=(n != 1);", "ko": "nplurals=1; plural=0;",
#             "en-gb": "nplurals=2; plural=(n != 1);", "sw": "nplurals=2; plural=(n != 1);",
#             "da": "nplurals=2; plural=(n != 1);", "fi": "nplurals=2; plural=(n != 1);",
#             "is": "nplurals=2; plural=(n != 1);", "no": "nplurals=2; plural=(n != 1);",
#             "sv": "nplurals=2; plural=(n != 1);", "zh-CN": "nplurals=1; plural=0;",
#         }

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _parse_glossary_csv(self, csv_file_path):
#         glossary_lookup: Dict[Tuple[str, str], str] = {}
#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         trans = self._normalize_placeholders(trans)
#                         glossary_lookup[(orig, ctx)] = trans
#                 return glossary_lookup
#             except Exception as e:
#                 print(f"Glossary parse error with {encoding}: {e}")
#         return glossary_lookup

#     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
#         key = (msgid, msgctxt or '')
#         if key in glossary_lookup:
#             return glossary_lookup[key]
#         return None

#     def _normalize_placeholders(self, msgstr):
#         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

#     def _extract_and_parse_existing_pos(self, zip_file_path):
#         existing_po_lookup = {}
#         if os.path.exists(self.temp_dir):
#             shutil.rmtree(self.temp_dir)
#         os.makedirs(self.temp_dir)

#         try:
#             with zipfile.ZipFile(zip_file_path, 'r') as zf:
#                 for member in zf.namelist():
#                     if member.endswith('.po') and not member.startswith('__MACOSX/'):
#                         zf.extract(member, self.temp_dir)
#                         path = os.path.join(self.temp_dir, member)

#                         try:
#                             detection = from_path(path).best()
#                             encoding = detection.encoding if detection and detection.encoding else 'utf-8'
#                             if encoding in ('ascii', None):
#                                 encoding = 'utf-8'

#                             po = polib.pofile(path, encoding=encoding)

#                             for entry in po:
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = entry.msgstr.strip()
#                                 if cleaned:
#                                     cleaned = self._normalize_placeholders(cleaned)
#                                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                                         cleaned = self._clean_translated_text(cleaned)
#                                         existing_po_lookup[key] = cleaned

#                             print(f"Loaded {member} → encoding: {encoding}")

#                         except Exception as e:
#                             print(f"Failed to parse {member} (tried {encoding}): {e}")
#                             for fallback in ['windows-1252', 'iso-8859-1', 'cp1252', 'latin1']:
#                                 try:
#                                     po = polib.pofile(path, encoding=fallback)
#                                     print(f"Success with fallback: {fallback}")
#                                     for entry in po:
#                                         key = (entry.msgid, entry.msgctxt or '')
#                                         cleaned = entry.msgstr.strip()
#                                         if cleaned:
#                                             cleaned = self._normalize_placeholders(cleaned)
#                                             if self._placeholders_are_valid(entry.msgid, cleaned):
#                                                 cleaned = self._clean_translated_text(cleaned)
#                                                 existing_po_lookup[key] = cleaned
#                                     break
#                                 except:
#                                     continue

#         except Exception as e:
#             print(f"Error extracting ZIP: {e}")
#         finally:
#             shutil.rmtree(self.temp_dir, ignore_errors=True)

#         return existing_po_lookup

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = []
#         ph += self.printf_placeholder_regex.findall(text)
#         ph += self.icu_placeholder_regex.findall(text)
#         quoted = self.quoted_printf_regex.findall(text)
#         ph += quoted
#         normalized = []
#         for x in ph:
#             if isinstance(x, tuple):
#                 normalized.append('{' + x[0] + '}')
#             else:
#                 normalized.append(x)
#         return list(dict.fromkeys(normalized))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             orig_ph = self._collect_placeholders(original)
#             trans_ph = self._collect_placeholders(translated)
#             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
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

#     def _clean_translated_text(self, text):
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text

#     def _is_likely_untranslated(self, original_text, translated_text):
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
#         return raw_orig.strip().lower() == raw_trans.strip().lower()

#     def _apply_custom_rules(self, msgid, target_language, plural_category: Optional[str] = None):
#         if msgid in self.translation_rules_plural_templates:
#             lang_map = self.translation_rules_plural_templates[msgid]
#             lang_map = lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#             if lang_map and plural_category and plural_category in lang_map:
#                 return lang_map[plural_category]
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#         return None

#     def _is_valid_translation(self, text):
#         error_signs = ["Error 500", "That’s an error", "<html", "</html>"]
#         return not any(s.lower() in text.lower() for s in error_signs)

#     def _retry(self, func, max_retries=3):
#         delay = 1.0
#         for i in range(max_retries):
#             try:
#                 return func()
#             except Exception as e:
#                 print(f"Attempt {i+1} failed: {e}")
#                 if i == max_retries - 1:
#                     raise
#                 time.sleep(delay)
#                 delay *= 2

#     def _translate_batch(self, memory, texts: List[str], target_language: str) -> List[str]:
#         outputs = [None] * len(texts)
#         to_query = []
#         to_query_idx = []
#         for i, t in enumerate(texts):
#             if t in memory:
#                 outputs[i] = memory[t]
#             elif (t, target_language) in self._cache:
#                 outputs[i] = self._cache[(t, target_language)]
#             else:
#                 to_query.append(t)
#                 to_query_idx.append(i)
#         if to_query:
#             translated = self._retry(lambda: self.translator_engine.translate(to_query, target_language))
#             for idx, trans in zip(to_query_idx, translated):
#                 outputs[idx] = trans
#                 self._cache[(texts[idx], target_language)] = trans
#                 memory[texts[idx]] = trans
#                 time.sleep(0.3)
#         return [x or "" for x in outputs]

#     def _fallback_translate(self, memory, text, target_language):
#         if text in memory:
#             return memory[text]
#         if (text, target_language) in self._cache:
#             return self._cache[(text, target_language)]
#         protected, map_ = self._protect_markers(text)
#         try:
#             trans = self._translate_batch(memory, [protected], target_language)[0]
#             trans = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", trans)
#             result = self._restore_markers(trans, map_)
#             result = self._clean_translated_text(result)
#             if self._is_valid_translation(result):
#                 self._cache[(text, target_language)] = result
#                 memory[text] = result
#                 return result
#             return text
#         except:
#             return text

#     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_language):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         full_key = f"{msgctxt}||{msgid}"

#         self._counts["total"] += 1

#         # MAXIMUM JSON REUSE
#         if full_key in memory:
#             value = memory[full_key]
#             if isinstance(value, str):
#                 self._counts["reused_json"] += 1
#                 return value, "Global JSON (with context)"
#             elif isinstance(value, list) and value:
#                 self._counts["reused_json"] += 1
#                 return value[0], "Global JSON (plural → singular)"

#         if msgid in memory:
#             value = memory[msgid]
#             if isinstance(value, str):
#                 self._counts["reused_json"] += 1
#                 return value, "Global JSON (fallback)"
#             elif isinstance(value, list) and value:
#                 self._counts["reused_json"] += 1
#                 return value[0], "Global JSON (plural fallback → singular)"

#         if self._contains_protected_entity(msgid):
#             self._counts["protected"] += 1
#             return msgid, "Protected"

#         custom = self._apply_custom_rules(msgid, target_language)
#         if custom:
#             memory[full_key] = custom
#             memory[msgid] = custom
#             self._counts["reused_json"] += 1
#             return custom, "Custom Rule"

#         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 memory[full_key] = fb
#                 memory[msgid] = fb
#                 return fb, "Glossary (Fuzzy → Google)"
#             memory[full_key] = gloss
#             memory[msgid] = gloss
#             self._counts["reused_glossary"] += 1
#             return gloss, "Glossary"

#         key = (msgid, msgctxt)
#         if key in existing_po_lookup:
#             existing = existing_po_lookup[key]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 memory[full_key] = fb
#                 memory[msgid] = fb
#                 return fb, "ZIP PO (Fuzzy → Google)"
#             memory[full_key] = existing
#             memory[msgid] = existing
#             self._counts["reused_zip"] += 1
#             return existing, "ZIP PO"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         memory[full_key] = fb
#         memory[msgid] = fb
#         self._counts["translated_google"] += 1
#         return fb, "Google Translate"

#     def _plural_header_for_lang(self, lang: str) -> str:
#         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split("_", 1)[0]) or "nplurals=2; plural=(n != 1);"

#     def _nplurals_from_header(self, header: str) -> int:
#         m = re.search(r"nplurals\s*=\s*(\d+)", header)
#         return int(m.group(1)) if m else 2

#     def _plural_categories_for_lang(self, lang: str) -> List[str]:
#         base = lang.split('_', 1)[0]
#         if PluralRule and Locale:
#             try:
#                 loc = Locale.parse(lang)
#             except:
#                 try:
#                     loc = Locale.parse(base)
#                 except:
#                     return ["one", "other"]
#             if loc:
#                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
#         return ["one", "other"]

#     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         msgid = entry.msgid
#         full_key = f"{entry.msgctxt or ''}||{msgid}"

#         npl = self._nplurals_from_header(self._plural_header_for_lang(target_language))

#         # REUSE FROM MEMORY
#         for key in [full_key, msgid]:
#             if key in memory:
#                 value = memory[key]
#                 if isinstance(value, list) and len(value) == npl:
#                     result = {i: value[i] for i in range(npl)}
#                     self._counts["reused_json"] += 1
#                     return result

#         if (self._contains_protected_entity(entry.msgid) or
#             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
#             result = {}
#             for i in range(npl):
#                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
#             self._counts["protected"] += 1
#             return result

#         header = self._plural_header_for_lang(target_language)
#         categories = self._plural_categories_for_lang(target_language)
#         if "one" not in categories:
#             categories = ["one"] + [c for c in categories if c != "one"]
#         if "other" not in categories:
#             categories.append("other")

#         templates = {}
#         for cat in categories:
#             custom = self._apply_custom_rules(entry.msgid, target_language, cat)
#             if custom:
#                 templates[cat] = custom

#         if not templates:
#             one = self._fallback_translate(memory, entry.msgid, target_language)
#             other = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)
#             templates["one"] = one
#             templates["other"] = other
#             self._counts["translated_google"] += 2

#         idx_map = ["other"] * npl
#         if npl >= 2:
#             idx_map[1] = "one"
#         if npl >= 3:
#             idx_map[2] = "few" if "few" in categories else "other"
#         if npl >= 4:
#             idx_map[3] = "many" if "many" in categories else "other"

#         result = {}
#         for i, cat in enumerate(idx_map):
#             result[i] = templates.get(cat) or templates.get("other") or templates.get("one") or (entry.msgid_plural if i > 0 else entry.msgid)

#         plurals_list = [result[i] for i in range(npl)]
#         memory[full_key] = plurals_list
#         memory[msgid] = plurals_list

#         return result

#     def _single_qa_check(self, entry: polib.POEntry, translated: str, status: str, target_language: str):
#         issues = []
#         if not translated:
#             issues.append("empty")
#         base = entry.msgid_plural or entry.msgid
#         if not self._placeholders_are_valid(base, translated):
#             issues.append("placeholders")
#         if self._is_likely_untranslated(entry.msgid, translated):
#             issues.append("unchanged_like")
#         if issues:
#             self._counts["failed"] += 1

#     def _qa_check(self, entry: polib.POEntry, translated, status: str, target_language: str):
#         if isinstance(translated, list):
#             for t in translated:
#                 self._single_qa_check(entry, t, status, target_language)
#         else:
#             self._single_qa_check(entry, translated, status, target_language)

#     def run(self, pot_path, zip_path=None, csv_path=None, target_langs=None, output_dir=None):
#         self._display_status("Starting Localization Tool")

#         project_name = os.path.splitext(os.path.basename(pot_path))[0]
#         self._display_status(f"Project: {project_name}")

#         translations_base = os.path.join(settings.MEDIA_ROOT, "translations")
#         os.makedirs(translations_base, exist_ok=True)
#         project_dir = os.path.join(translations_base, project_name)
#         os.makedirs(project_dir, exist_ok=True)

#         self.pot_file_path = pot_path
#         valid_langs = [lang[0] for lang in settings.LANGUAGES]
#         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
#         if not self.target_languages:
#             self._display_error("No valid target languages provided.")
#             return True

#         try:
#             if not os.path.exists(pot_path):
#                 self._display_error("POT file not found.")
#                 return True

#             pot_file = polib.pofile(pot_path)

#             glossary = {}
#             if csv_path and os.path.exists(csv_path):
#                 glossary = self._parse_glossary_csv(csv_path)

#             existing_from_zip = {}
#             if zip_path and os.path.exists(zip_path):
#                 existing_from_zip = self._extract_and_parse_existing_pos(zip_path)

#             for target_language in self.target_languages:
#                 self._qa_rows = []
#                 self._counts = {
#                     "total": 0,
#                     "reused_json": 0,
#                     "reused_glossary": 0,
#                     "reused_zip": 0,
#                     "translated_google": 0,
#                     "protected": 0,
#                     "failed": 0,
#                 }

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}

#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             full_jed = json.load(f)
#                         translations_memory = {k: v for k, v in full_jed.items() if k != ""}
#                         self._display_status(f"Loaded {len(translations_memory)} strings from {target_language}.json")
#                     except Exception as e:
#                         self._display_error(f"Failed to load {jed_path}: {e} — starting fresh")
#                         translations_memory = {}

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
#                 po.metadata = {
#                     'Project-Id-Version': project_name,
#                     'POT-Creation-Date': now,
#                     'PO-Revision-Date': now,
#                     'Language': target_language,
#                     'MIME-Version': '1.0',
#                     'Content-Type': 'text/plain; charset=UTF-8',
#                     'Content-Transfer-Encoding': '8bit',
#                     'X-Generator': 'Colab Tool',
#                     'Plural-Forms': self._plural_header_for_lang(target_language)
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     source = "New"

#                     if entry.msgid_plural:
#                         plurals_dict = self._pluralize_entry(translations_memory, {}, entry, target_language)
#                         plurals_list = [plurals_dict.get(i, "") for i in range(self._nplurals_from_header(self._plural_header_for_lang(target_language)))]
#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr="",
#                             msgstr_plural=plurals_dict,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, plurals_list, "new", target_language)
#                     else:
#                         translated_msgstr, source = self._process_translation(
#                             translations_memory, {}, entry, glossary, existing_from_zip, target_language
#                         )
#                         if isinstance(translated_msgstr, list):
#                             translated_msgstr = translated_msgstr[0] if translated_msgstr else ""

#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgstr=translated_msgstr,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, translated_msgstr, "new", target_language)

#                     if source != "Global JSON (with context)" and source != "Global JSON (fallback)":
#                         full_key = f"{entry.msgctxt or ''}||{entry.msgid}"
#                         if entry.msgid_plural:
#                             translations_memory[full_key] = plurals_list
#                             translations_memory[entry.msgid] = plurals_list
#                         else:
#                             translations_memory[full_key] = [translated_msgstr]
#                             translations_memory[entry.msgid] = [translated_msgstr]

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 final_jed = translations_memory.copy()
#                 final_jed[""] = {
#                     "lang": target_language,
#                     "plural_forms": self._plural_header_for_lang(target_language)  # ← FIXED HERE
#                 }
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(final_jed, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} completed (v{version}):")
#                 self._display_status(f"   Total strings         : {self._counts['total']}")
#                 self._display_status(f"   Reused from JSON      : {self._counts['reused_json']}")
#                 self._display_status(f"   Reused from Glossary  : {self._counts['reused_glossary']}")
#                 self._display_status(f"   Reused from ZIP PO    : {self._counts['reused_zip']}")
#                 self._display_status(f"   Translated by Google  : {self._counts['translated_google']}")
#                 self._display_status(f"   Protected             : {self._counts['protected']}")
#                 self._display_status(f"   QA Failed             : {self._counts['failed']}")

#             self._display_status("Translation complete.")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Unexpected error: {e}\n{traceback.format_exc()}")
#             return False


# localizationtool/localization_logic.py best code comment on 23 dec to made changes of zip glossaies
# FINAL VERSION — QUALITY SYMBOLS ONLY IN JSON (NOT IN .PO/.MO) + CLEAN WEBSITE TEXT (2025-12-18)

# import polib
# import csv
# import zipfile
# import os
# import shutil
# from datetime import datetime
# from deep_translator import GoogleTranslator as _GoogleTranslator, exceptions
# import re
# import time
# import json
# from typing import Dict, Tuple, List, Optional
# from django.conf import settings
# from charset_normalizer import from_path

# try:
#     from babel.core import Locale
#     from babel.plural import PluralRule
# except ImportError:
#     Locale = None
#     PluralRule = None


# class _Translator:
#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         raise NotImplementedError


# class GoogleTranslatorEngine(_Translator):
#     _SEP = "INVISIBLE_SEPARATOR"

#     def translate(self, texts: List[str], target_lang: str) -> List[str]:
#         if not texts:
#             return []
#         joined = self._SEP.join(texts)
#         translator = _GoogleTranslator(source='auto', target=target_lang)
#         out = translator.translate(joined)
#         if isinstance(out, list):
#             return [str(x) for x in out]
#         parts = str(out).split(self._SEP)
#         if len(parts) != len(texts):
#             parts = []
#             for t in texts:
#                 parts.append(str(_GoogleTranslator(source='auto', target=target_lang).translate(t)))
#         return parts


# class ColabLocalizationTool:
#     def __init__(self, memory_base_dir: str = None):
#         self.pot_file_path = None
#         self.zip_file_path = None
#         self.csv_file_path = None
#         self.target_languages: List[str] = []
#         self.temp_dir = os.path.join(settings.MEDIA_ROOT, "temp_po_extract")

#         self.json_dir = os.path.join(settings.MEDIA_ROOT, "json")
#         os.makedirs(self.json_dir, exist_ok=True)

#         self.NON_TRANSLATABLE_ENTITIES = {
#             "&copy;", "&COPY;", "COPYRIGHT_SYMBOL",
#             "&reg;", "&REG;", "REGISTERED_TRADEMARK",
#             "&trade;", "&TRADE;", "TRADEMARK",
#             "&nbsp;", "EURO", "&euro;", "&lt;", "&gt;", "&amp;"
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

#         self.translation_rules_plural_templates = {
#             "%s min read": {
#                 "en": {"one": "%s min read", "other": "%s mins read"},
#                 "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
#                 "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
#                 "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
#                 "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
#                 "da": {"one": "%s min læsning", "other": "%s min læsning"},
#                 "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
#                 "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
#                 "no": {"one": "%s min lesing", "other": "%s min lesing"},
#                 "sv": {"one": "%s min läsning", "other": "%s min läsning"},
#                 "zh-CN": {"other": "%s 分钟阅读"},
#             }
#         }

#         self._qa_rows: List[Dict] = []
#         self._counts = {
#             "total": 0,
#             "reused_json": 0,
#             "reused_glossary": 0,
#             "reused_zip": 0,
#             "translated_google": 0,
#             "protected": 0,
#             "failed": 0,
#         }
#         self._cache: Dict[Tuple[str, str], str] = {}
#         self.translator_engine: _Translator = GoogleTranslatorEngine()

#         self.plural_forms_header = {
#             "en": "nplurals=2; plural=(n != 1);", "es": "nplurals=2; plural=(n != 1);",
#             "de": "nplurals=2; plural=(n != 1);", "fr": "nplurals=2; plural=(n > 1);",
#             "pt": "nplurals=2; plural=(n != 1);", "hi": "nplurals=2; plural=(n != 1);",
#             "ne": "nplurals=2; plural=(n != 1);", "ar": "nplurals=6; plural=(n==0?0 : n==1?1 : n==2?2 : n%100>=3 and n%100<=10?3 : n%100>=11 and n%100<=99?4 : 5);",
#             "it": "nplurals=2; plural=(n != 1);", "ja": "nplurals=1; plural=0;",
#             "pl": "nplurals=3; plural=(n==1 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "ru": "nplurals=3; plural=(n%10==1 and n%100!=11 ? 0 : n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) ? 1 : 2);",
#             "nl": "nplurals=2; plural=(n != 1);", "zh": "nplurals=1; plural=0;",
#             "id": "nplurals=1; plural=0;", "th": "nplurals=1; plural=0;",
#             "tl": "nplurals=2; plural=(n != 1);", "ko": "nplurals=1; plural=0;",
#             "en-gb": "nplurals=2; plural=(n != 1);", "sw": "nplurals=2; plural=(n != 1);",
#             "da": "nplurals=2; plural=(n != 1);", "fi": "nplurals=2; plural=(n != 1);",
#             "is": "nplurals=2; plural=(n != 1);", "no": "nplurals=2; plural=(n != 1);",
#             "sv": "nplurals=2; plural=(n != 1);", "zh-CN": "nplurals=1; plural=0;",
#         }

#     def _display_status(self, message):
#         print(f"\n--- STATUS: {message} ---")

#     def _display_error(self, message):
#         print(f"\n--- ERROR: {message} ---")

#     def _contains_protected_entity(self, text: str) -> bool:
#         return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

#     def _parse_glossary_csv(self, csv_file_path):
#         glossary_lookup: Dict[Tuple[str, str], str] = {}
#         encodings = ['utf-8', 'latin1', 'cp1252']
#         for encoding in encodings:
#             try:
#                 with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
#                     reader = csv.DictReader(f)
#                     for row in reader:
#                         orig = (row.get("Original String", "") or "").strip()
#                         ctx = (row.get("Context", "") or "").strip()
#                         trans = (row.get("Translated String", "") or "").strip()
#                         trans = self._normalize_placeholders(trans)
#                         glossary_lookup[(orig, ctx)] = trans
#                 return glossary_lookup
#             except Exception as e:
#                 print(f"Glossary parse error with {encoding}: {e}")
#         return glossary_lookup

#     def _match_glossary(self, glossary_lookup, msgid: str, msgctxt: str) -> Optional[str]:
#         key = (msgid, msgctxt or '')
#         if key in glossary_lookup:
#             return glossary_lookup[key]
#         return None

#     def _normalize_placeholders(self, msgstr):
#         return re.sub(r'%\s*(\d+)\s*\$\s*[sSdD]', r'%\1$s', msgstr)

#     def _extract_and_parse_existing_pos(self, zip_file_path):
#         existing_po_lookup = {}
#         if os.path.exists(self.temp_dir):
#             shutil.rmtree(self.temp_dir)
#         os.makedirs(self.temp_dir)

#         try:
#             with zipfile.ZipFile(zip_file_path, 'r') as zf:
#                 for member in zf.namelist():
#                     if member.endswith('.po') and not member.startswith('__MACOSX/'):
#                         zf.extract(member, self.temp_dir)
#                         path = os.path.join(self.temp_dir, member)

#                         try:
#                             detection = from_path(path).best()
#                             encoding = detection.encoding if detection and detection.encoding else 'utf-8'
#                             if encoding in ('ascii', None):
#                                 encoding = 'utf-8'

#                             po = polib.pofile(path, encoding=encoding)

#                             for entry in po:
#                                 key = (entry.msgid, entry.msgctxt or '')
#                                 cleaned = entry.msgstr.strip()
#                                 if cleaned:
#                                     cleaned = self._normalize_placeholders(cleaned)
#                                     if self._placeholders_are_valid(entry.msgid, cleaned):
#                                         cleaned = self._clean_translated_text(cleaned)
#                                         existing_po_lookup[key] = cleaned

#                             print(f"Loaded {member} → encoding: {encoding}")

#                         except Exception as e:
#                             print(f"Failed to parse {member} (tried {encoding}): {e}")
#                             for fallback in ['windows-1252', 'iso-8859-1', 'cp1252', 'latin1']:
#                                 try:
#                                     po = polib.pofile(path, encoding=fallback)
#                                     print(f"Success with fallback: {fallback}")
#                                     for entry in po:
#                                         key = (entry.msgid, entry.msgctxt or '')
#                                         cleaned = entry.msgstr.strip()
#                                         if cleaned:
#                                             cleaned = self._normalize_placeholders(cleaned)
#                                             if self._placeholders_are_valid(entry.msgid, cleaned):
#                                                 cleaned = self._clean_translated_text(cleaned)
#                                                 existing_po_lookup[key] = cleaned
#                                     break
#                                 except:
#                                     continue

#         except Exception as e:
#             print(f"Error extracting ZIP: {e}")
#         finally:
#             shutil.rmtree(self.temp_dir, ignore_errors=True)

#         return existing_po_lookup

#     def _collect_placeholders(self, text: str) -> List[str]:
#         ph = []
#         ph += self.printf_placeholder_regex.findall(text)
#         ph += self.icu_placeholder_regex.findall(text)
#         quoted = self.quoted_printf_regex.findall(text)
#         ph += quoted
#         normalized = []
#         for x in ph:
#             if isinstance(x, tuple):
#                 normalized.append('{' + x[0] + '}')
#             else:
#                 normalized.append(x)
#         return list(dict.fromkeys(normalized))

#     def _placeholders_are_valid(self, original: str, translated: str) -> bool:
#         try:
#             orig_ph = self._collect_placeholders(original)
#             trans_ph = self._collect_placeholders(translated)
#             return set(orig_ph) == set(trans_ph) and len(orig_ph) == len(trans_ph)
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

#     def _clean_translated_text(self, text):
#         text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
#         text = re.sub(r'\s+([.,!?;:])', r'\1', text)
#         text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
#         text = re.sub(r'(\s+)(”|\))', r'\2', text)
#         text = re.sub(r'(“|\()\s+', r'\1', text)
#         return text

#     def _is_likely_untranslated(self, original_text, translated_text):
#         protected_orig, _ = self._protect_markers(original_text)
#         protected_trans, _ = self._protect_markers(translated_text)
#         raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig)
#         raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans)
#         return raw_orig.strip().lower() == raw_trans.strip().lower()

#     def _apply_custom_rules(self, msgid, target_language, plural_category: Optional[str] = None):
#         if msgid in self.translation_rules_plural_templates:
#             lang_map = self.translation_rules_plural_templates[msgid]
#             lang_map = lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#             if lang_map and plural_category and plural_category in lang_map:
#                 return lang_map[plural_category]
#         if msgid in self.translation_rules:
#             lang_map = self.translation_rules[msgid]
#             return lang_map.get(target_language) or lang_map.get(target_language.split("_", 1)[0])
#         return None

#     def _is_valid_translation(self, text):
#         error_signs = ["Error 500", "That’s an error", "<html", "</html>"]
#         return not any(s.lower() in text.lower() for s in error_signs)

#     def _retry(self, func, max_retries=3):
#         delay = 1.0
#         for i in range(max_retries):
#             try:
#                 return func()
#             except Exception as e:
#                 print(f"Attempt {i+1} failed: {e}")
#                 if i == max_retries - 1:
#                     raise
#                 time.sleep(delay)
#                 delay *= 2

#     def _translate_batch(self, memory, texts: List[str], target_language: str) -> List[str]:
#         outputs = [None] * len(texts)
#         to_query = []
#         to_query_idx = []
#         for i, t in enumerate(texts):
#             if t in memory:
#                 outputs[i] = memory[t]
#             elif (t, target_language) in self._cache:
#                 outputs[i] = self._cache[(t, target_language)]
#             else:
#                 to_query.append(t)
#                 to_query_idx.append(i)
#         if to_query:
#             translated = self._retry(lambda: self.translator_engine.translate(to_query, target_language))
#             for idx, trans in zip(to_query_idx, translated):
#                 outputs[idx] = trans
#                 self._cache[(texts[idx], target_language)] = trans
#                 memory[texts[idx]] = trans
#                 time.sleep(0.3)
#         return [x or "" for x in outputs]

#     def _fallback_translate(self, memory, text, target_language):
#         if text in memory:
#             return memory[text]
#         if (text, target_language) in self._cache:
#             return self._cache[(text, target_language)]
#         protected, map_ = self._protect_markers(text)
#         try:
#             trans = self._translate_batch(memory, [protected], target_language)[0]
#             trans = re.sub(r"&\s+([a-zA-Z]+)\s*;", r"&\1;", trans)
#             result = self._restore_markers(trans, map_)
#             result = self._clean_translated_text(result)
#             if self._is_valid_translation(result):
#                 self._cache[(text, target_language)] = result
#                 memory[text] = result
#                 return result
#             return text
#         except:
#             return text

#     def _process_translation(self, memory, lang_json, pot_entry, glossary_lookup, existing_po_lookup, target_language):
#         msgid = pot_entry.msgid
#         msgctxt = pot_entry.msgctxt or ''
#         full_key = f"{msgctxt}||{msgid}"

#         self._counts["total"] += 1

#         # MAXIMUM JSON REUSE
#         if full_key in memory:
#             value = memory[full_key]
#             if isinstance(value, list):
#                 first = value[0] if value else ""
#             else:
#                 first = value
#             if first.startswith(("★", "○")):
#                 self._counts["reused_json"] += 1
#                 # Strip symbol for clean return
#                 clean = first[2:].strip() if first.startswith("★ ") or first.startswith("○ ") else first[1:].strip()
#                 return clean, "Global JSON"

#         if msgid in memory:
#             value = memory[msgid]
#             if isinstance(value, list):
#                 first = value[0] if value else ""
#             else:
#                 first = value
#             if first.startswith(("★", "○")):
#                 self._counts["reused_json"] += 1
#                 clean = first[2:].strip() if first.startswith("★ ") or first.startswith("○ ") else first[1:].strip()
#                 return clean, "Global JSON (fallback)"

#         if self._contains_protected_entity(msgid):
#             self._counts["protected"] += 1
#             return msgid, "Protected"

#         custom = self._apply_custom_rules(msgid, target_language)
#         if custom:
#             memory[full_key] = custom
#             memory[msgid] = custom
#             self._counts["reused_json"] += 1
#             return custom, "Custom Rule"

#         gloss = self._match_glossary(glossary_lookup, msgid, msgctxt)
#         if gloss:
#             if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 memory[full_key] = fb
#                 memory[msgid] = fb
#                 return fb, "Glossary (Fuzzy → Google)"
#             memory[full_key] = gloss
#             memory[msgid] = gloss
#             self._counts["reused_glossary"] += 1
#             return gloss, "Glossary"

#         key = (msgid, msgctxt)
#         if key in existing_po_lookup:
#             existing = existing_po_lookup[key]
#             if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
#                 fb = self._fallback_translate(memory, msgid, target_language)
#                 self._counts["translated_google"] += 1
#                 memory[full_key] = fb
#                 memory[msgid] = fb
#                 return fb, "ZIP PO (Fuzzy → Google)"
#             memory[full_key] = existing
#             memory[msgid] = existing
#             self._counts["reused_zip"] += 1
#             return existing, "ZIP PO"

#         fb = self._fallback_translate(memory, msgid, target_language)
#         memory[full_key] = fb
#         memory[msgid] = fb
#         self._counts["translated_google"] += 1
#         return fb, "Google Translate"

#     def _plural_header_for_lang(self, lang: str) -> str:
#         return self.plural_forms_header.get(lang) or self.plural_forms_header.get(lang.split("_", 1)[0]) or "nplurals=2; plural=(n != 1);"

#     def _nplurals_from_header(self, header: str) -> int:
#         m = re.search(r"nplurals\s*=\s*(\d+)", header)
#         return int(m.group(1)) if m else 2

#     def _plural_categories_for_lang(self, lang: str) -> List[str]:
#         base = lang.split('_', 1)[0]
#         if PluralRule and Locale:
#             try:
#                 loc = Locale.parse(lang)
#             except:
#                 try:
#                     loc = Locale.parse(base)
#                 except:
#                     return ["one", "other"]
#             if loc:
#                 return [c for c in ["one", "two", "few", "many", "other"] if c in loc.plural_form.rules]
#         return ["one", "other"]

#     def _pluralize_entry(self, memory, lang_json, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
#         msgid = entry.msgid
#         msgctxt = entry.msgctxt or ''
#         full_key = f"{msgctxt}||{msgid}"

#         npl = self._nplurals_from_header(self._plural_header_for_lang(target_language))

#         # REUSE FROM MEMORY
#         for key in [full_key, msgid]:
#             if key in memory:
#                 value = memory[key]
#                 if isinstance(value, list) and len(value) == npl:
#                     result = {i: value[i] for i in range(npl)}
#                     self._counts["reused_json"] += 1
#                     return result

#         if (self._contains_protected_entity(entry.msgid) or
#             (entry.msgid_plural and self._contains_protected_entity(entry.msgid_plural))):
#             result = {}
#             for i in range(npl):
#                 result[i] = entry.msgid_plural if i > 0 else entry.msgid
#             self._counts["protected"] += 1
#             return result

#         header = self._plural_header_for_lang(target_language)
#         categories = self._plural_categories_for_lang(target_language)
#         if "one" not in categories:
#             categories = ["one"] + [c for c in categories if c != "one"]
#         if "other" not in categories:
#             categories.append("other")

#         templates = {}
#         for cat in categories:
#             custom = self._apply_custom_rules(entry.msgid, target_language, cat)
#             if custom:
#                 templates[cat] = custom

#         if not templates:
#             one = self._fallback_translate(memory, entry.msgid, target_language)
#             other = self._fallback_translate(memory, entry.msgid_plural or entry.msgid, target_language)
#             templates["one"] = one
#             templates["other"] = other
#             self._counts["translated_google"] += 2

#         idx_map = ["other"] * npl
#         if npl >= 2:
#             idx_map[1] = "one"
#         if npl >= 3:
#             idx_map[2] = "few" if "few" in categories else "other"
#         if npl >= 4:
#             idx_map[3] = "many" if "many" in categories else "other"

#         result = {}
#         for i, cat in enumerate(idx_map):
#             result[i] = templates.get(cat) or templates.get("other") or templates.get("one") or (entry.msgid_plural if i > 0 else entry.msgid)

#         plurals_list = [result[i] for i in range(npl)]
#         memory[full_key] = plurals_list
#         memory[msgid] = plurals_list

#         return result

#     def _single_qa_check(self, entry: polib.POEntry, translated: str, status: str, target_language: str):
#         issues = []
#         if not translated:
#             issues.append("empty")
#         base = entry.msgid_plural or entry.msgid
#         if not self._placeholders_are_valid(base, translated):
#             issues.append("placeholders")
#         if self._is_likely_untranslated(entry.msgid, translated):
#             issues.append("unchanged_like")
#         if issues:
#             self._counts["failed"] += 1

#     def _qa_check(self, entry: polib.POEntry, translated, status: str, target_language: str):
#         if isinstance(translated, list):
#             for t in translated:
#                 self._single_qa_check(entry, t, status, target_language)
#         else:
#             self._single_qa_check(entry, translated, status, target_language)

#     def run(self, pot_path, zip_path=None, csv_path=None, target_langs=None, output_dir=None):
#         self._display_status("Starting Localization Tool")

#         project_name = os.path.splitext(os.path.basename(pot_path))[0]
#         self._display_status(f"Project: {project_name}")

#         translations_base = os.path.join(settings.MEDIA_ROOT, "translations")
#         os.makedirs(translations_base, exist_ok=True)
#         project_dir = os.path.join(translations_base, project_name)
#         os.makedirs(project_dir, exist_ok=True)

#         self.pot_file_path = pot_path
#         valid_langs = [lang[0] for lang in settings.LANGUAGES]
#         self.target_languages = [lang for lang in target_langs if lang in valid_langs]
#         if not self.target_languages:
#             self._display_error("No valid target languages provided.")
#             return True

#         try:
#             if not os.path.exists(pot_path):
#                 self._display_error("POT file not found.")
#                 return True

#             pot_file = polib.pofile(pot_path)

#             glossary = {}
#             if csv_path and os.path.exists(csv_path):
#                 glossary = self._parse_glossary_csv(csv_path)

#             existing_from_zip = {}
#             if zip_path and os.path.exists(zip_path):
#                 existing_from_zip = self._extract_and_parse_existing_pos(zip_path)

#             for target_language in self.target_languages:
#                 self._qa_rows = []
#                 self._counts = {
#                     "total": 0,
#                     "reused_json": 0,
#                     "reused_glossary": 0,
#                     "reused_zip": 0,
#                     "translated_google": 0,
#                     "protected": 0,
#                     "failed": 0,
#                 }

#                 jed_path = os.path.join(self.json_dir, f"{target_language}.json")
#                 translations_memory = {}

#                 if os.path.exists(jed_path):
#                     try:
#                         with open(jed_path, 'r', encoding='utf-8') as f:
#                             full_jed = json.load(f)
#                         translations_memory = {k: v for k, v in full_jed.items() if k != ""}
#                         self._display_status(f"Loaded {len(translations_memory)} strings from {target_language}.json")
#                     except Exception as e:
#                         self._display_error(f"Failed to load {jed_path}: {e} — starting fresh")
#                         translations_memory = {}

#                 version = 1
#                 while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
#                     version += 1

#                 po = polib.POFile()
#                 now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S+0000")
#                 po.metadata = {
#                     'Project-Id-Version': project_name,
#                     'POT-Creation-Date': now,
#                     'PO-Revision-Date': now,
#                     'Language': target_language,
#                     'MIME-Version': '1.0',
#                     'Content-Type': 'text/plain; charset=UTF-8',
#                     'Content-Transfer-Encoding': '8bit',
#                     'X-Generator': 'Colab Tool',
#                     'Plural-Forms': self._plural_header_for_lang(target_language)
#                 }

#                 for entry in pot_file:
#                     if not entry.msgid:
#                         continue

#                     msgctxt = entry.msgctxt or ''
#                     full_key = f"{msgctxt}||{entry.msgid}"

#                     source = "New"

#                     if entry.msgid_plural:
#                         plurals_dict = self._pluralize_entry(translations_memory, {}, entry, target_language)
#                         plurals_list = [plurals_dict.get(i, "") for i in range(self._nplurals_from_header(self._plural_header_for_lang(target_language)))]

#                         # CLEAN FOR PO FILE (no symbols)
#                         clean_plurals = {i: s.replace("★", "").replace("○", "").strip() if isinstance(s, str) else "" for i, s in plurals_dict.items()}

#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgid_plural=entry.msgid_plural,
#                             msgstr="",
#                             msgstr_plural=clean_plurals,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, plurals_list, "new", target_language)
#                     else:
#                         translated_msgstr, source = self._process_translation(
#                             translations_memory, {}, entry, glossary, existing_from_zip, target_language
#                         )
#                         if isinstance(translated_msgstr, list):
#                             translated_msgstr = translated_msgstr[0] if translated_msgstr else ""

#                         # CLEAN FOR PO FILE (remove symbols)
#                         clean_msgstr = translated_msgstr.replace("★", "").replace("○", "").strip() if isinstance(translated_msgstr, str) else ""

#                         new_entry = polib.POEntry(
#                             msgid=entry.msgid,
#                             msgstr=clean_msgstr,
#                             msgctxt=entry.msgctxt,
#                             occurrences=entry.occurrences,
#                             comment=entry.comment,
#                             tcomment=entry.tcomment
#                         )
#                         po.append(new_entry)
#                         self._qa_check(entry, clean_msgstr, "new", target_language)

#                     # SAVE WITH SYMBOLS TO JSON (for quality tracking)
#                     is_high_quality = ("ZIP PO" in source or "Glossary" in source or "Protected" in source or "Custom Rule" in source or "Global JSON" in source)
#                     symbol = "★" if is_high_quality else "○"

#                     if entry.msgid_plural:
#                         prefixed_list = [f"{symbol} {s}".strip() if s else "" for s in plurals_list]
#                         translations_memory[full_key] = prefixed_list
#                         translations_memory[entry.msgid] = prefixed_list
#                     else:
#                         prefixed = f"{symbol} {translated_msgstr}".strip() if translated_msgstr else ""
#                         translations_memory[full_key] = [prefixed]
#                         translations_memory[entry.msgid] = [prefixed]

#                 out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
#                 out_mo = out_po.replace('.po', '.mo')
#                 po.save(out_po)
#                 po.save_as_mofile(out_mo)

#                 final_jed = translations_memory.copy()
#                 final_jed[""] = {
#                     "lang": target_language,
#                     "plural_forms": self._plural_header_for_lang(target_language)
#                 }
#                 with open(jed_path, 'w', encoding='utf-8') as f:
#                     json.dump(final_jed, f, ensure_ascii=False, indent=2, sort_keys=True)

#                 self._display_status(f"{target_language.upper()} completed (v{version}):")
#                 self._display_status(f"   Total strings         : {self._counts['total']}")
#                 self._display_status(f"   Reused from JSON      : {self._counts['reused_json']}")
#                 self._display_status(f"   Reused from Glossary  : {self._counts['reused_glossary']}")
#                 self._display_status(f"   Reused from ZIP PO    : {self._counts['reused_zip']}")
#                 self._display_status(f"   Translated by Google  : {self._counts['translated_google']}")
#                 self._display_status(f"   Protected             : {self._counts['protected']}")
#                 self._display_status(f"   QA Failed             : {self._counts['failed']}")

#             self._display_status("Translation complete.")
#             return True

#         except Exception as e:
#             import traceback
#             self._display_error(f"Unexpected error: {e}\n{traceback.format_exc()}")
#             return False







# localizationtool/localization_logic.py
# FINAL PERFECT VERSION — Language folders + file filtering by language code + No mixing (Dec 24, 2025)

import polib
import csv
import os
import shutil
import re
import time
import json
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

        self.translation_rules_plural_templates = {
            "%s min read": {
                "en": {"one": "%s min read", "other": "%s mins read"},
                "fr": {"one": "%s min de lecture", "other": "%s min de lecture"},
                "ru": {"one": "%s мин. чтения", "few": "%s мин. чтения", "many": "%s мин. чтения", "other": "%s мин. чтения"},
                "ar": {"one": "قراءة في دقيقة %s", "other": "قراءة في %s دقيقة"},
                "sw": {"one": "%s dakika kusoma", "other": "%s dakika kusoma"},
                "da": {"one": "%s min læsning", "other": "%s min læsning"},
                "fi": {"one": "%s min lukeminen", "other": "%s min lukeminen"},
                "is": {"one": "%s mín lestur", "other": "%s mín lestur"},
                "no": {"one": "%s min lesing", "other": "%s min lesing"},
                "sv": {"one": "%s min läsning", "other": "%s min läsning"},
                "zh-CN": {"other": "%s 分钟阅读"},
            }
        }

        self._counts = {
            "total": 0, "reused_json": 0, "reused_glossary": 0,
            "reused_zip": 0, "translated_google": 0, "protected": 0
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

    def _display_status(self, message):
        print(f"\n--- STATUS: {message} ---")

    def _display_error(self, message):
        print(f"\n--- ERROR: {message} ---")

    def _contains_protected_entity(self, text: str) -> bool:
        return any(entity in text for entity in self.NON_TRANSLATABLE_ENTITIES)

    def _collect_placeholders(self, text: str) -> List[str]:
        ph = self.printf_placeholder_regex.findall(text) + self.icu_placeholder_regex.findall(text) + self.quoted_printf_regex.findall(text)
        return list(dict.fromkeys(ph))

    def _placeholders_are_valid(self, original: str, translated: str) -> bool:
        try:
            return set(self._collect_placeholders(original)) == set(self._collect_placeholders(translated))
        except:
            return False

    def _protect_markers(self, text: str) -> Tuple[str, Dict[str, str]]:
        placeholders = self._collect_placeholders(text)
        tags = self.html_tag_regex.findall(text)
        to_protect = placeholders + tags
        to_protect.sort(key=len, reverse=True)
        placeholder_map = {}
        protected_text = text
        for i, ph in enumerate(to_protect):
            token = f"PH_{i}_TOKEN"
            placeholder_map[token] = ph
            protected_text = protected_text.replace(ph, token)
        return protected_text, placeholder_map

    def _restore_markers(self, text: str, placeholder_map: Dict[str, str]) -> str:
        for token, ph in placeholder_map.items():
            text = text.replace(token, ph)
        return text

    def _clean_translated_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'&\s*(#?\w+)\s*;', r'&\1;', text)
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)
        text = re.sub(r'(\s+)(”|\))', r'\2', text)
        text = re.sub(r'(“|\()\s+', r'\1', text)
        return text.strip()

    def _is_likely_untranslated(self, original_text: str, translated_text: str) -> bool:
        protected_orig, _ = self._protect_markers(original_text)
        protected_trans, _ = self._protect_markers(translated_text)
        raw_orig = re.sub(r'PH_\d+_TOKEN', '', protected_orig).strip().lower()
        raw_trans = re.sub(r'PH_\d+_TOKEN', '', protected_trans).strip().lower()
        return raw_orig == raw_trans

    def _apply_custom_rules(self, msgid: str, target_language: str, plural_category: Optional[str] = None):
        if msgid in self.translation_rules_plural_templates:
            lang_map = self.translation_rules_plural_templates[msgid]
            map_for_lang = lang_map.get(target_language) or lang_map.get(target_language.split('_')[0])
            if map_for_lang and plural_category in map_for_lang:
                return map_for_lang[plural_category]
        if msgid in self.translation_rules:
            lang_map = self.translation_rules[msgid]
            return lang_map.get(target_language) or lang_map.get(target_language.split('_')[0])
        return None

    def _fallback_translate(self, memory: Dict, text: str, target_language: str) -> str:
        key = (text, target_language)
        if key in self._cache:
            return self._cache[key]
        protected, map_ = self._protect_markers(text)
        try:
            trans = self.translator_engine.translate([protected], target_language)[0]
            result = self._restore_markers(trans, map_)
            result = self._clean_translated_text(result)
            self._cache[key] = result
            memory[text] = result
            return result
        except:
            return text

    def _parse_glossary_csv(self, csv_file_path: Optional[str]) -> Dict[Tuple[str, str], str]:
        glossary_lookup = {}
        if not csv_file_path or not os.path.exists(csv_file_path):
            return glossary_lookup
        encodings = ['utf-8', 'latin1', 'cp1252']
        for encoding in encodings:
            try:
                with open(csv_file_path, 'r', encoding=encoding, errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        orig = (row.get("Original String", "") or "").strip()
                        ctx = (row.get("Context", "") or "").strip()
                        trans = (row.get("Translated String", "") or "").strip()
                        glossary_lookup[(orig, ctx)] = trans
                return glossary_lookup
            except:
                continue
        return glossary_lookup

    # FINAL FIX: Only load .po files that contain the correct language code
    def _load_pos_from_folder(self, folder_path: str, lang_code: str) -> Dict[Tuple[str, str], str]:
        lookup = {}
        if not folder_path or not os.path.exists(folder_path):
            return lookup

        lang_pattern = f"-{lang_code}."
        print(f"Loading .po files for '{lang_code}' from folder (only files containing '{lang_pattern}')")

        for root, _, files in os.walk(folder_path):
            for file in files:
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
                        print(f"   ✓ Loaded: {file} ({len(lookup)} strings so far)")
                    except Exception as e:
                        print(f"   ✗ Failed to load {file}: {e}")

        print(f"   → Final: {len(lookup)} strings loaded for {lang_code}")
        return lookup

    def _process_translation(self, memory: Dict, pot_entry: polib.POEntry, glossary_lookup: Dict, existing_po_lookup: Dict, target_language: str):
        msgid = pot_entry.msgid
        msgctxt = pot_entry.msgctxt or ''
        full_key = f"{msgctxt}||{msgid}"

        self._counts["total"] += 1

        # 1. Global JSON
        if full_key in memory:
            val = memory[full_key]
            if isinstance(val, list) and val:
                text = val[0]
                if text.startswith(("★", "○")):
                    self._counts["reused_json"] += 1
                    return text[2:].strip(), "Global JSON"
            elif isinstance(val, str):
                self._counts["reused_json"] += 1
                return val.strip(), "Global JSON"

        # 2. Protected
        if self._contains_protected_entity(msgid):
            self._counts["protected"] += 1
            return msgid, "Protected"

        # 3. Custom rules
        custom = self._apply_custom_rules(msgid, target_language)
        if custom:
            self._counts["reused_json"] += 1
            return custom, "Custom Rule"

        # 4. Glossary
        gloss = glossary_lookup.get((msgid, msgctxt))
        if gloss:
            if not self._placeholders_are_valid(msgid, gloss) or self._is_likely_untranslated(msgid, gloss):
                fb = self._fallback_translate(memory, msgid, target_language)
                self._counts["translated_google"] += 1
                return fb, "Glossary → Google"
            self._counts["reused_glossary"] += 1
            return gloss, "Glossary"

        # 5. Existing PO from correct folder
        key = (msgid, msgctxt)
        if key in existing_po_lookup:
            existing = existing_po_lookup[key]
            if not self._placeholders_are_valid(msgid, existing) or self._is_likely_untranslated(msgid, existing):
                fb = self._fallback_translate(memory, msgid, target_language)
                self._counts["translated_google"] += 1
                return fb, "Existing → Google"
            self._counts["reused_zip"] += 1
            return existing, "Existing PO"

        # 6. Google Translate
        fb = self._fallback_translate(memory, msgid, target_language)
        self._counts["translated_google"] += 1
        return fb, "Google Translate"

    def _plural_header_for_lang(self, lang: str) -> str:
        return self.plural_forms_header.get(lang, "nplurals=2; plural=(n != 1);")

    def _pluralize_entry(self, memory: Dict, entry: polib.POEntry, target_language: str) -> Dict[int, str]:
        header = self._plural_header_for_lang(target_language)
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

    def run(self, pot_path, zip_paths_by_lang=None, glossary_by_lang=None, target_langs=None, output_dir=None):
        self._display_status("Starting Localization Tool")

        if zip_paths_by_lang is None:
            zip_paths_by_lang = {}

        project_dir = output_dir or os.path.dirname(pot_path)
        os.makedirs(project_dir, exist_ok=True)

        valid_langs = [code for code, _ in settings.LANGUAGES]
        target_languages = [lang for lang in target_langs if lang in valid_langs]

        if not target_languages:
            self._display_error("No valid languages")
            return False

        try:
            pot_file = polib.pofile(pot_path)

            # Load per-language existing POs with filtering
            existing_by_lang = {}
            for lang in target_languages:
                folder = zip_paths_by_lang.get(lang)
                if folder:
                    self._display_status(f"Loading existing translations for {lang.upper()} from folder")
                    existing_by_lang[lang] = self._load_pos_from_folder(folder, lang)
                else:
                    existing_by_lang[lang] = {}

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

                glossary = self._parse_glossary_csv(glossary_by_lang.get(target_language)) if glossary_by_lang else {}
                existing_lookup = existing_by_lang[target_language]

                version = 1
                while os.path.exists(os.path.join(project_dir, f"{target_language}-{version}.po")):
                    version += 1

                po = polib.POFile()
                po.metadata = {
                    'Project-Id-Version': '1.0',
                    'Language': target_language,
                    'Plural-Forms': self._plural_header_for_lang(target_language),
                    'X-Generator': 'Advanced Tool 2025',
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
                        translations_memory[entry.msgid] = prefixed
                    else:
                        translated, source = self._process_translation(translations_memory, entry, glossary, existing_lookup, target_language)
                        clean = translated.strip()
                        po.append(polib.POEntry(msgid=entry.msgid, msgstr=clean, msgctxt=entry.msgctxt))
                        symbol = "★" if source in ["Global JSON", "Custom Rule", "Glossary", "Existing PO", "Protected"] else "○"
                        prefixed = f"{symbol} {clean}"
                        translations_memory[f"{entry.msgctxt or ''}||{entry.msgid}"] = [prefixed]
                        translations_memory[entry.msgid] = [prefixed]

                out_po = os.path.join(project_dir, f"{target_language}-{version}.po")
                out_mo = out_po.replace('.po', '.mo')
                po.save(out_po)
                po.save_as_mofile(out_mo)

                translations_memory[""] = {"lang": target_language, "plural_forms": self._plural_header_for_lang(target_language)}
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