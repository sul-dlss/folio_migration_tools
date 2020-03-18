"""The Alabama mapper, responsible for parsing Items acording to the
FOLIO community specifications"""
import uuid
import json
import csv
import sys
import traceback
from datetime import datetime

csv.field_size_limit(sys.maxsize)


class ItemsDefaultMapper:
    """Maps an Item to inventory Item format according to
    the FOLIO community convention"""

    # Bootstrapping (loads data needed later in the script.)

    def __init__(self, folio, item_map, holdings_id_map, location_map):
        print("init")
        csv.register_dialect("tsv", delimiter="\t")
        csv.register_dialect("tsvq", delimiter="\t", quotechar='"')
        csv.register_dialect("pipe", delimiter="|")
        self.folio = folio
        self.stats = {"missing_location_codes": 0, "unmapped item types": 0}
        self.item_schema = folio.get_item_schema()
        self.item_id_map = {}
        self.map = item_map
        print(item_map)
        self.holdings_id_map = holdings_id_map
        self.mapped_folio_fields = {}
        for key in self.item_schema["properties"].keys():
            self.mapped_folio_fields[key] = 0
        self.mapped_legacy_field = {}

        """Locations stuff"""
        self.failed_items = []
        self.locations_map = {}
        self.missing_location_codes = {}
        self.setup_locations(location_map)

        """Loan types, material types"""
        self.loan_type_map = {}
        self.unmapped_loan_types = {}
        self.setup_m_and_l_types()

        """Note types"""
        self.item_note_types = self.folio.folio_get_all(
            "/item-note-types", "itemNoteTypes"
        )
        self.note_id = next(
            x["id"] for x in self.item_note_types if "Note" == x["name"]
        )

    def setup_m_and_l_types(self,):
        with open(self.map["materialTypeMap"]) as material_type_f:
            mt_map = list(csv.DictReader(material_type_f, dialect="tsv"))
            loan_types = self.folio.folio_get_all("/loan-types", "loantypes")
            material_types = self.folio.folio_get_all("/material-types", "mtypes")
            for b in mt_map:
                lt_id = next(
                    (x["id"] for x in loan_types if b["loan_type"] == x["name"]),
                    "Unmapped",
                )
                mt_id = next(
                    (
                        x["id"]
                        for x in material_types
                        if b["material_type"] == x["name"]
                    ),
                    "Unmapped",
                )
                if lt_id == "Unmapped":
                    print(b["loan_type"])
                if mt_id == "Unmapped":
                    print(b["material_type"])
                self.loan_type_map[b["legacy_type"]] = {
                    "loan_type": lt_id,
                    "material_type": mt_id,
                }
        print(f"set up LoanTypeMap: {len(self.loan_type_map)} rows.")

    def setup_locations(self, location_map):
        temp_map = {}
        for loc in self.folio.locations:
            key = loc[self.map["mapOnLocationField"]].strip()
            temp_map[key] = loc["id"]
        if location_map and any(location_map):
            for v in location_map:
                if "," in v["legacy_code"]:
                    for k in v["legacy_code"].split(","):
                        self.locations_map[k.strip()] = temp_map[v["folio_code"]]
                else:
                    self.locations_map[v["legacy_code"]] = temp_map[v["folio_code"]]
        else:
            print("No location map supplied")
            self.locations_map = temp_map
        # self.locations_map = location_map
        # print(json.dumps(self.locations_map, indent=4))

    def wrap_up(self):
        # print(json.dumps(self.failed_items, indent=4))
        print("mapped FOLIO fields")
        print(json.dumps(self.mapped_folio_fields, indent=4))
        print("Mapped legacy fields")
        print(json.dumps(self.mapped_legacy_field, indent=4))
        print("Missing location codes")
        print(json.dumps(self.missing_location_codes, indent=4))
        print("unmapped loan types")
        print(json.dumps(self.unmapped_loan_types, indent=4))
        print(json.dumps(self.stats, indent=4))

    def get_loc_id(self, loc_code):
        folio_loc_id = next(
            (l["id"] for l in self.folio.locations if loc_code.strip() == l["code"]), ""
        )
        if not folio_loc_id:
            raise ValueError(f"Location code not found in FOLIO: {loc_code}")
        return folio_loc_id

    def get_records(self, file):
        reader = None
        if self.map["itemsFileType"] == "TSV":
            reader = csv.DictReader(file, dialect="tsv")
        if self.map["itemsFileType"] == "PIPE":
            reader = csv.DictReader(file, dialect="pipe")
        if self.map["itemsFileType"] == "TSVQ":
            reader = csv.DictReader(file, dialect="tsvq")
        if self.map["itemsFileType"] == "CSV":
            csv.register_dialect("my_csv", delimiter=self.map["itemsFileDelimiter"])
            reader = csv.DictReader(file, dialect="my_csv")
        # reader = csv.DictReader(file, dialect="pipe")
        i = 0
        try:
            for row in reader:
                i += 1
                yield row
        except Exception as ee:
            print(f"row:{i}")
            print(ee)
            # raise ee

    def parse_item(self, legacy_item):
        try:
            item = {
                "id": str(uuid.uuid4()),
                "status": {"name": "Available"},
                "metadata": self.folio.get_metadata_construct(),
            }
            legacy_id = legacy_item.get("Z30_REC_KEY", "")
            self.count_mapped("id", "")
            self.count_mapped("status", "")
            self.count_mapped("metadata", "")
            for legacy_key, value in self.map["fields"].items():
                folio_field = value["target"]
                legacy_value = legacy_item.get(legacy_key, "")
                if legacy_value:
                    legacy_value = legacy_value.strip()
                if legacy_value and folio_field:
                    if folio_field == "formerIds":
                        legacy_id = legacy_value
                    elif folio_field in ["permanentLocationId", "temporaryLocationId"]:
                        code = self.get_location_code(legacy_value)
                        if code:
                            item[folio_field] = code
                    elif folio_field == "materialTypeId":
                        self.handle_material_types(legacy_value, item)
                    elif folio_field == "holdingsRecordId":
                        if legacy_value not in self.holdings_id_map:
                            raise ValueError(f"Holdings id {legacy_value} not in map")
                        else:
                            item[folio_field] = self.holdings_id_map[legacy_value]
                    elif folio_field == "notes":
                        self.add_note(legacy_value, item)
                    else:
                        if self.is_string(folio_field):
                            item[folio_field] = legacy_value
                        elif self.is_string_array(folio_field):
                            if folio_field in item and any(item[folio_field]):
                                item[folio_field].append(legacy_value)
                            else:
                                item[folio_field] = [legacy_value]
                    self.count_mapped(folio_field, legacy_key)

            for req in self.item_schema["required"]:
                if req not in item.keys():
                    raise ValueError(f"{req} is required")
                if "permanentLoanTypeId" not in item.keys():
                    raise ValueError(f"{req} is required")
                if "materialTypeId" not in item.keys():
                    raise ValueError(f"{req} is required")
            self.item_id_map[legacy_id] = item["id"]
            return item
        except ValueError as ve:
            print(f"{ve} for {legacy_id}")
            return None
        except Exception as ee:
            print(f"{ee} for {legacy_id}")
            traceback.print_exc()
            raise ee

    def get_location_code(self, legacy_value):
        location_id = self.locations_map.get(legacy_value.strip(), "")
        if location_id == "":
            self.missing_location_codes[legacy_value] = (
                self.missing_location_codes.get(legacy_value, 0) + 1
            )
            self.stats["missing_location_codes"] += 1
            # raise ValueError(f"No location in map for {legacy_value}")
        return location_id

    def is_string(self, target):
        folio_prop = self.item_schema["properties"][target]["type"]
        return folio_prop == "string"

    def is_string_array(self, target):
        f = self.item_schema["properties"][target]
        return f["type"] == "array" and f["items"]["type"] == "string"

    def count_mapped(self, target, legacy_key):
        if target:
            self.mapped_folio_fields[target] += 1
        if legacy_key:
            self.mapped_legacy_field[legacy_key] = (
                self.mapped_legacy_field.get(legacy_key, 0) + 1
            )

    def add_note(self, note_string, item, note_type_name="", staffOnly=False):
        nt_id = next(
            (x["id"] for x in self.item_note_types if note_type_name == x["name"]),
            self.note_id,
        )
        note_to_add = {
            "itemNoteTypeId": nt_id,
            "note": note_string,
            "staffOnly": staffOnly,
        }
        if "notes" in item and any(item["notes"]):
            item["notes"].append(note_to_add)
        else:
            item["notes"] = [note_to_add]

    def handle_material_types(self, legacy_value, item):
        v = legacy_value
        if v.startswith("DigitalEquip"):
            v = "DigitalEquipment"
            # TODO: map value!
            cost = v.replace("DigitalEquip_", "")
            self.add_note(cost, item, "Replacement Cost (USD)", True)
            print(f"adding Cost note: {cost}")
        if "*" in self.loan_type_map:
            item["permanentLoanTypeId"] = self.loan_type_map["*"]["loan_type"]
            item["materialTypeId"] = self.loan_type_map["*"]["material_type"]
            self.count_mapped("materialTypeId", "")
            self.count_mapped("permanentLoanTypeId", "")
        elif v not in self.loan_type_map:
            self.unmapped_loan_types[v] = self.unmapped_loan_types.get(v, 0) + 1
            self.stats["unmapped item types"] += 1
            print(f"legacy item type {legacy_value} not mapped")
        else:
            t = self.loan_type_map[v]
            item["permanentLoanTypeId"] = t["loan_type"]
            item["materialTypeId"] = t["material_type"]
            self.count_mapped("materialTypeId", "")
            self.count_mapped("permanentLoanTypeId", "")
