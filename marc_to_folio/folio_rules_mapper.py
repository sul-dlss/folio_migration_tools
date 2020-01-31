'''The default mapper, responsible for parsing MARC21 records acording to the
FOLIO community specifications'''
import json
import os.path
import re
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from io import StringIO

import requests
from pymarc import Field, JSONWriter

from marc_to_folio.default_mapper import DefaultMapper


class RulesMapper(DefaultMapper):
    '''Maps a MARC record to inventory instance format according to
    the FOLIO community convention'''
    # Bootstrapping (loads data needed later in the script.)

    def __init__(self, folio, results_path):
        self.filter_chars = r'[.,\/#!$%\^&\*;:{}=\-_`~()]'
        self.filter_chars_dop = r'[.,\/#!$%\^&\*;:{}=\_`~()]'
        self.filter_last_chars = r',$'
        self.folio = folio
        self.migration_user_id = 'd916e883-f8f1-4188-bc1d-f0dce1511b50'
        self.srs_recs = []
        instance_url = 'https://raw.githubusercontent.com/folio-org/mod-inventory-storage/master/ramls/instance.json'
        schema_request = requests.get(instance_url)
        # schema_request = requests.get('https://raw.githubusercontent.com/folio-org/mod-source-record-manager/master/ramls/instance.json')
        schema_text = schema_request.text
        # schema_text = schema_text.replace('raml-util/schemas/tags.schema', 'https://raw.githubusercontent.com/folio-org/raml/master/schemas/tags.schema')
        # schema_text = schema_text.replace('raml-util/schemas/metadata.schema', 'https://raw.githubusercontent.com/folio-org/raml/master/schemas/metadata.schema')

        self.instance_schema = json.loads(schema_text)
        # self.instance_schema['properties'].pop('tags')
        # self.instance_schema['title'] = 'Instance'
        # self.instance_schema['$id'] = instance_url
        self.holdings_map = {}
        self.results_path = results_path
        self.srs_records_file = open(os.path.join(
            self.results_path, 'srs.json'), "w+")
        self.srs_raw_records_file = open(os.path.join(
            self.results_path, 'srs_raw_records.json'), "w+")
        self.srs_marc_records_file = open(os.path.join(
            self.results_path, 'srs_marc_records.json'), "w+")
        self.id_map = {}
        print("Fetching valid language codes...")
        self.language_codes = list(self.fetch_language_codes())
        self.contrib_name_types = {}
        self.mapped_folio_fields = {}
        self.alt_title_map = {}
        self.identifier_types = []
        # self.mappings = self.folio.folio_get_single_object('/mapping-rules')
        with open('/mnt/c/code/folio-fse/MARC21-To-FOLIO/maps/mapping_rules_default.json') as map_f:
            self.mappings = json.load(map_f)
        self.unmapped_tags = {}

    def add_stats(self, stats, a):
        if a not in stats:
            stats[a] = 1
        else:
            stats[a] += 1

    def wrap_up(self):
        self.flush_srs_recs()
        self.srs_records_file.close()
        self.srs_marc_records_file.close()
        self.srs_raw_records_file.close()
        print(self.unmapped_tags)

    '''
    def instantiate_instance(self, userId):
        builder = pjs.ObjectBuilder(self.instance_schema)
        ns = builder.build_classes()
        Instance = ns.Instance
        i = Instance()
        print(i)
        '''

    def parse_bib(self, marc_record, record_source):
        ''' Parses a bib recod into a FOLIO Inventory instance object
            Community mapping suggestion: https://bit.ly/2S7Gyp3
             This is the main function'''
        rec = {
            'id': str(uuid.uuid4()),
            'metadata': super().get_metadata_construct(self.migration_user_id)}
        for marc_field in marc_record:
            if marc_field.tag not in self.mappings:
                self.add_stats(self.unmapped_tags, marc_field.tag)
            else:
                mappings = self.mappings[marc_field.tag]
                self.map_field_according_to_mapping(marc_field, mappings, rec)

        # self.validate(rec)        
        for key, value in rec.items():
            if isinstance(value, list):
                res = []
                for v in value:
                    if v not in res:
                        res.append(v)
                rec[key] = res
        print(json.dumps(rec, indent=4, sort_keys=True))
        return rec

    def map_field_according_to_mapping(self, marc_field, mappings, rec):
        for mapping in mappings:
            if 'entity' not in mapping:
                if 'rules' in mapping and any(mapping['rules']) and any(mapping['rules'][0]['conditions']):
                    self.add_value_to_target(
                        rec, mapping['target'], self.apply_rules(marc_field, mapping))
                else:
                    self.add_value_to_target(rec, mapping['target'], marc_field.format_field())
            else:
                self.handle_entity_mapping(marc_field, mapping['entity'], rec)

    def handle_entity_mapping(self, marc_field, entity_mapping, rec):
        e_parent = entity_mapping[0]['target'].split('.')[0]
        sch = self.instance_schema['properties']
        print(f"entity mapping into {e_parent} {marc_field.tag} parent is of type {sch[e_parent]['type']}")
        entity = {}
        for em in entity_mapping:
            k = em['target'].split('.')[-1]
            v = self.apply_rules(marc_field, em)
            #v = ' '.join(marc_field.get_subfields(*em['subfield']))
            entity[k] = v
        if sch[e_parent]['type'] == 'array':
            if e_parent not in rec:
                rec[e_parent] = [entity]
            else:
                rec[e_parent].append(entity)
        else:
            rec[e_parent] = entity
        # rec[e_parent] = list(rec[e_parent])

    def apply_rules(self, marc_field, mapping):
        # print(mapping)
        # print(marc_field)
        value = ''
        if 'rules' in mapping and  any(mapping['rules']) and any(mapping['rules'][0]['conditions']):
            c_type_def = mapping['rules'][0]['conditions'][0]['type'].split(',')
            condition_types = [x.strip() for x in c_type_def]
            # print(f'conditions {condition_types}')
            if mapping.get('applyRulesOnConcatenatedData', ''):
                value = ' '.join(marc_field.get_subfields(*mapping['subfield']))
                value = self.apply_rule(value, condition_types, marc_field)
            else:
                value = ' '.join([self.apply_rule(x, condition_types, marc_field) for x in marc_field.get_subfields(*mapping['subfield'])])
            if not value:
                print(f"no value! {value} {marc_field}")
            return value
        elif 'rules' not in mapping or not any(mapping['rules']) or not any(mapping['rules'][0]['conditions']):
            value = ' '.join(marc_field.get_subfields(*mapping['subfield']))
            print(f"no rules")
            return value


    def apply_rule(self, value, condition_types, marc_field):
        v = value
        for condition_type in condition_types:
            if condition_type == 'trim_period':
                v = v.strip().rstrip('.').rstrip(',')
            elif condition_type == 'trim':
                v = v.strip()
            elif condition_type == 'remove_ending_punc':
                chars = '.;:,/+=- '
                while len(v) > 0 and v[-1] in chars:
                    v = v.rstrip(v[-1])
            elif condition_type == 'remove_prefix_by_indicator':
                v = self.get_index_title(marc_field, v)
            # elif condition_type == 'capitalize':

            else:
                print(f'{condition_type} not matched!')
        return v

    def add_value_to_target(self, rec, target_string, value):
        targets = target_string.split('.')
        sch = self.instance_schema['properties']
        prop = rec
        sc_prop = sch
        sc_parent = None
        parent = None
        if len(targets) == 1:
            # print(f"{target_string} {value} {rec}")
            if sch[target_string]['type'] == 'array' and sch[target_string]['items']['type'] == 'string':
                if target_string not in rec:
                    rec[target_string] = [value]
                else:
                    # print(f"Adding into list! {target_string} {(rec[target_string])} {value}")
                    rec[target_string].append(value)
            elif sch[target_string]['type'] == 'string':
                rec[target_string] = value
            else:
                print(f"Edge! {target_string} {sch[target_string]['type']}")
        else:
            for target in targets:
                if target in sc_prop:
                    sc_prop = sc_prop[target]
                else:
                    sc_prop = sc_parent['items']['properties'][target]
                if target not in rec:
                    if sc_prop['type'] == 'array':
                        prop[target] = []
                        break
                        # prop[target].append({})
                    elif sc_parent['type'] == 'array' and sc_prop['type'] == 'string':
                        print(f"break! {target} {sc_prop['type']} {prop}")
                        break
                    else:
                        if (sc_parent['type'] == 'array'):
                            prop[target] = {}
                            parent.append(prop[target])
                if target == targets[-1]:
                    prop[target] = value
                prop = prop[target]
                sc_parent = sc_prop
                parent = target

    def validate(self, folio_rec):
        if folio_rec["title"].strip() == "":
            print(f"No title for {folio_rec['hrid']}")
        for key, value in folio_rec.items():
            if isinstance(value, str) and len(value) > 0:
                self.mapped_folio_fields['key]'] = self.mapped_folio_fields.get(
                    key, 0) + 1
            if isinstance(value, list) and len(value) > 0:
                self.mapped_folio_fields['key]'] = self.mapped_folio_fields.get(
                    key, 0) + 1

    def save_source_record(self, marc_record, instance_id):
        '''Saves the source Marc_record to the Source record Storage module'''
        marc_record.add_field(Field(tag='999',
                                    indicators=['f', 'f'],
                                    subfields=['i', instance_id]))
        self.srs_recs.append((marc_record, instance_id))
        if len(self.srs_recs) > 1000:
            self.flush_srs_recs()
            self.srs_recs = []

    def flush_srs_recs(self):
        pool = ProcessPoolExecutor(max_workers=4)
        results = list(pool.map(get_srs_strings, self.srs_recs))
        self.srs_records_file.write("".join(r[0]for r in results))
        self.srs_marc_records_file.write(
            "".join(r[2] for r in results))
        self.srs_raw_records_file.write("".join(r[1] for r in results))

    def post_new_source_storage_record(self, loan):
        okapi_headers = self.folio.okapi_headers
        host = self.folio.okapi_url
        path = ("{}/source-storage/records".format(host))
        response = requests.post(path,
                                 data=loan,
                                 headers=okapi_headers)
        if response.status_code != 201:
            print("Something went wrong. HTTP {}\nMessage:\t{}"
                  .format(response.status_code, response.text))

    def get_editions(self, marc_record):
        fields = marc_record.get_fields('250')
        for field in fields:
            yield " ".join(field.get_subfields('a', 'b'))

    def get_publication_frequency(self, marc_record):
        for tag in ['310', '321']:
            for field in marc_record.get_fields(tag):
                yield ' '.join(field.get_subfields(*'ab'))

    def get_publication_range(self, marc_record):
        for field in marc_record.get_fields('362'):
            yield ' '.join(field.get_subfields('a'))

    def get_nature_of_content(self, marc_record):
        return ["81a3a0e2-b8e5-4a7a-875d-343035b4e4d7"]

    def get_physical_desc(self, marc_record):
        # TODO: improve according to spec
        for tag in ['300']:
            for field in marc_record.get_fields(tag):
                yield field.format_field()

    def get_index_title(self, marc_field, title_string):
        # TODO: fixa!
        '''Returns the index title according to the rules''' 
        ind2 = marc_field.indicator2
        reg_str = r'[\s:\/]{0,3}$'
        if ind2 in map(str, range(1, 9)):
            num_take = int(ind2)
            return re.sub(reg_str, '', title_string[num_take:])
        else:
            return re.sub(reg_str, '', title_string)

    def get_notes(self, marc_record):
        '''Collects all notes fields and stores them as generic notes.'''
        # TODO: specify note types with better accuracy.
        for key, value in self.note_tags.items():
            for field in marc_record.get_fields(key):
                yield {
                    # TODO: add logic for noteTypeId
                    "instanceNoteTypeId": "9d4fcaa1-b1a5-48ea-b0d1-986839737ad2",
                    "note": " ".join(field.get_subfields(*value)),
                    # TODO: Map staffOnly according to field
                    "staffOnly": False
                }

    def get_title(self, marc_record):
        if '245' not in marc_record:
            return ''
        '''Get title or raise exception.'''
        title = " ".join(marc_record['245'].get_subfields(*list('anpbcfghks')))
        if title:
            return title
        else:
            raise ValueError("No title for {}\n{}"
                             .format(marc_record['001'], marc_record))

    def folio_record_template(self, identifier):
        '''Create a new folio record from template'''
        # if created from json schema validation could happen earlier...
        return {'id': str(identifier)}

    def get_instance_type_id(self, marc_record):
        # TODO: Check 336 first!
        instance_type_code = marc_record.leader[6]
        table = {
            'a': 'txt',
            'm': 'txt',
            't': 'txt',
            'e': 'cri',
            'g': 'tdi',
            'i': 'snd',
            'p': 'xxx'}
        code = table.get(instance_type_code, 'zzz')
        return next(i['id'] for i in self.folio.instance_types
                    if code == i['code'])

    def get_mode_of_issuance_id(self, marc_record):
        mode_of_issuance = marc_record.leader[7]
        table = {'m': 'Monograph', 's': 'Serial'}
        name = table.get(mode_of_issuance, 'Other')
        return next(i['id'] for i in self.folio.modes_of_issuance
                    if name == i['name'])

    def name_type_id(self, n):
        if not any(self.contrib_name_types):
            self.contrib_name_types = {f['name']: f['id']
                                       for f in self.folio.contrib_name_types}
        return self.contrib_name_types[n]

    def get_contributors(self, marc_record):
        '''Collects contributors from the marc record and adds the apropriate
        Ids'''
        fields = {'100': {'subfields': 'abcdq',
                          'nameTypeId': 'Personal name'},
                  '110': {'subfields': 'abcdn',
                          'nameTypeId': 'Corporate name'},
                  '111': {'subfields': 'abcd',
                          'nameTypeId': 'Meeting name'},
                  '700': {'subfields': 'abcdq',
                          'nameTypeId': 'Personal name'},
                  '710': {'subfields': 'abcdn',
                          'nameTypeId': 'Corporate name'},
                  '711': {'subfields': 'abcd',
                          'nameTypeId': 'Meeting name'}
                  }
        first = 0
        for field_tag in fields:
            for field in marc_record.get_fields(field_tag):
                ctype = self.get_contrib_type_id(marc_record)
                first += 1
                subs = field.get_subfields(*fields[field_tag]['subfields'])
                ntd = self.name_type_id(fields[field_tag]['nameTypeId'])
                yield {'name': re.sub(self.filter_last_chars, '', ' '.join(subs)),
                       'contributorNameTypeId': ntd,
                       'contributorTypeId': ctype,
                       'primary': first < 2}

    def get_contrib_type_id(self, marc_record):
        ''' Maps type of contribution to the right FOLIO Contributor types'''
        # TODO: create logic here...
        ret = 'a5bee4d0-c5b9-449c-a6ee-880143b117bc'
        return ret

    def get_urls(self, marc_record):
        for field in marc_record.get_fields('856'):
            yield {
                'uri': (field['u'] if 'u' in field else ''),
                'linkText': (field['y'] if 'y' in field else ''),
                'materialsSpecification': field['3'] if '3' in field else '',
                'publicNote': field['z'] if 'z' in field else ''
                # 'relationsshipId': field.indicator2}
            }

    def get_subjects(self, marc_record):
        ''' Get subject headings from the marc record.'''
        for tag in list(self.non_mapped_subject_tags.keys()):
            if any(marc_record.get_fields(tag)):
                print("Unmapped Subject field {} in {}"
                      .format(tag, marc_record['001']))
        for key, value in self.subject_tags.items():
            for field in marc_record.get_fields(key):
                yield " ".join(field.get_subfields(*value)).strip()

    def get_alt_titles(self, marc_record):
        '''Finds all Alternative titles.'''
        if not any(self.alt_title_map):
            self.alt_title_map = {'130': [next(f['id'] for f
                                               in self.folio.alt_title_types
                                               if f['name'] == 'No type specified'),
                                          list('anpdfghklmorst')],
                                  '222': [next(f['id'] for f
                                               in self.folio.alt_title_types
                                               if f['name'] == 'No type specified'),
                                          list('anpdfghklmorst')],
                                  '240': [next(f['id'] for f
                                               in self.folio.alt_title_types
                                               if f['name'] == 'No type specified'),
                                          list('anpdfghklmors')],
                                  '246': [next(f['id'] for f
                                               in self.folio.alt_title_types
                                               if f['name'] == 'No type specified'),
                                          list('anpbfgh5')],
                                  '247': [next(f['id'] for f
                                               in self.folio.alt_title_types
                                               if f['name'] == 'No type specified'),
                                          list('anpbfghx')]}
        for field_tag in self.alt_title_map:
            for field in marc_record.get_fields(field_tag):
                yield {'alternativeTitleTypeId': self.alt_title_map[field_tag][0],
                       'alternativeTitle': " - "
                       .join(field.get_subfields(*self.alt_title_map[field_tag][1]))}
        # return list(dict((v['alternativeTitleTypeId'], v)
        #                 for v in res).values())

    def get_publication(self, marc_record):
        # TODO: Improve with 008 and 260/4 $c
        '''Publication'''
        for field in marc_record.get_fields('260'):
            dop = str(next(iter(field.get_subfields('c')), ''))
            yield {'publisher': self.get_filtered_subfield(field, 'b'),
                   'place': self.get_filtered_subfield(field, 'a'),
                   'dateOfPublication': re.sub(self.filter_chars_dop,
                                               str(''), dop).strip() or ''}
        for field in marc_record.get_fields('264'):
            dop = str(next(iter(field.get_subfields('c')), ''))
            yield {'publisher': self.get_filtered_subfield(field, 'b'),
                   'place': self.get_filtered_subfield(field, 'a'),
                   'dateOfPublication': re.sub(self.filter_chars_dop,
                                               str(''), dop).strip() or '',
                   'role': self.get_publication_role(field.indicators[1])}

    def get_filtered_subfield(self, field, name):
        field_value = next(iter(field.get_subfields(name)), '')
        return re.sub(self.filter_chars, str(''), str(field_value)).strip() or ''

    def get_publication_role(self, ind2):
        roles = {'0': 'Production',
                 '1': 'Publication',
                 '2': 'Distribution',
                 '3': 'Manufacturer',
                 '4': ''
                 }
        if ind2.strip() not in roles.keys():
            return roles['4']
        return roles[ind2.strip()]

    def get_series(self, marc_record):
        '''Series'''
        tags = {'440': 'anpv',
                '490': '3av',
                '800': 'abcdefghjklmnopqrstuvwx35',
                '810': 'abcdefghklmnoprstuvwx35',
                '811': 'acdefghjklnpqstuvwx35',
                '830': 'adfghklmnoprstvwx35'}
        for key, value in tags.items():
            for field in marc_record.get_fields(key):
                yield ' '.join(field.get_subfields(*value))

    def get_languages(self, marc_record):
        '''Get languages and tranforms them to correct codes'''
        languages = set()
        skip_languages = ['###', 'zxx']
        lang_fields = marc_record.get_fields('041')
        if any(lang_fields):
            subfields = 'abdefghjkmn'
            for lang_tag in lang_fields:
                lang_codes = lang_tag.get_subfields(*list(subfields))
                for lang_code in lang_codes:
                    lang_code = str(lang_code).lower()
                    langlength = len(lang_code.replace(" ", ""))
                    if langlength == 3:
                        languages.add(lang_code.replace(" ", ""))
                    elif langlength > 3 and langlength % 3 == 0:
                        lc = lang_code.replace(" ", "")
                        new_codes = [lc[i:i + 3]
                                     for i in range(0, len(lc), 3)]
                        languages.update(new_codes)
                        languages.discard(lang_code)

                languages.update()
            languages = set(self.filter_langs(filter(None, languages),
                                              skip_languages,
                                              marc_record['001'].format_field()))
        elif '008' in marc_record and len(marc_record['008'].data) > 38:
            from_008 = ''.join((marc_record['008'].data[35:38]))
            if from_008:
                languages.add(from_008.lower())
        # TODO: test agianist valide language codes
        return list(languages)

    def fetch_language_codes(self):
        '''fetches the list of standardized language codes from LoC'''
        url = "https://www.loc.gov/standards/codelists/languages.xml"
        tree = ET.fromstring(requests.get(url).content)
        name_space = "{info:lc/xmlns/codelist-v1}"
        xpath_expr = "{0}languages/{0}language/{0}code".format(name_space)
        for code in tree.findall(xpath_expr):
            yield code.text

    def get_classifications(self, marc_record):
        '''Collects Classes and adds the appropriate metadata'''
        def get_class_type_id(x):
            return next((f['id'] for f
                         in self.folio.class_types
                         if f['name'] == x), None)
        fields = {'050': ['LC', 'ab'],
                  '082': ['Dewey', 'a'],
                  '086': ['GDC', 'a'],
                  '090': ['LC', 'ab']
                  }
        for field_tag in fields:
            for field in marc_record.get_fields(field_tag):
                class_type = get_class_type_id(fields[field_tag][0])
                if class_type:
                    yield {'classificationTypeId': get_class_type_id(fields[field_tag][0]),
                           'classificationNumber': " ".join(field.get_subfields(*fields[field_tag][1]))}
                else:
                    print("No classification type for {} ({}) for {}."
                          .format(field.tag, field.format_field(),
                                  marc_record['001'].format_field(),))

    def get_identifiers(self, marc_record):
        '''Collects Identifiers and adds the appropriate metadata'''
        if not any(self.identifier_types):
            self.identifier_types = [
                ['010', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'LCCN'), ''),
                 'a'],
                ['019', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'System control number'), ''),
                 'a'],
                ['020', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'ISBN'), ''), 'a'],
                ['020', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Invalid ISBN'), ''),
                 'z'],
                ['024', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Other standard identifier'), ''),
                 'a'],
                ['028', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Publisher or distributor number'), ''),
                 'a'],
                ['022', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'ISSN'), ''),
                 'a'],
                ['022', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Invalid ISSN'), ''),
                 'zmy'],
                ['022', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Linking ISSN'), ''),
                 'l'],
                # TODO: OCLC number? Distinguish 035s from eachother
                ['035', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'Control number'), ''),
                 'az'],
                ['074', next((f['id'] for f
                              in self.folio.identifier_types
                              if f['name'] == 'GPO item number'), ''),
                 'a']]
        for b in self.identifier_types:
            tag = b[0]
            identifier_type_id = b[1]
            subfields = b[2]
            for field in marc_record.get_fields(tag):
                for subfield in field.get_subfields(*list(subfields)):
                    if identifier_type_id:
                        yield {'identifierTypeId': identifier_type_id,
                               'value': subfield}

    def filter_langs(self, language_values, forbidden_values, legacyid):
        for language_value in language_values:
            if language_value in self.language_codes and language_value not in forbidden_values:
                yield language_value
            else:
                if language_value == 'jap':
                    yield 'jpn'
                elif language_value == 'fra':
                    yield 'fre'
                elif language_value == 'sve':
                    yield 'swe'
                elif language_value == 'tys':
                    yield 'ger'
                else:
                    print('Illegal language code: {} for {}'
                          .format(language_value, legacyid))


# Wrapping corouting which waits for return from process pool.

def get_srs_strings(my_tuple):
    json_string = StringIO()
    writer = JSONWriter(json_string)
    writer.write(my_tuple[0])
    writer.close(close_fh=False)
    marc_uuid = str(uuid.uuid4())
    raw_uuid = str(uuid.uuid4())
    record = {
        "id": str(uuid.uuid4()),
        "deleted": False,
        "snapshotId": "67dfac11-1caf-4470-9ad1-d533f6360bdd",
        "matchedProfileId": str(uuid.uuid4()),
        "matchedId": str(uuid.uuid4()),
        "generation": 1,
        "recordType": "MARC",
        "rawRecordId": raw_uuid,
        "parsedRecordId": marc_uuid,
        "additionalInfo": {
            "suppressDiscovery": False
        },
        "externalIdsHolder": {
            "instanceId": my_tuple[1]
        }
    }
    raw_record = {
        "id": raw_uuid,
        "content": my_tuple[0].as_json()
    }
    marc_record = {
        "id": marc_uuid,
        "content": json.loads(my_tuple[0].as_json())
    }
    return (f"{record['id']}\t{json.dumps(record)}\n",
            f"{raw_record['id']}\t{json.dumps(raw_record)}\n",
            f"{marc_record['id']}\t{json.dumps(marc_record)}\n")