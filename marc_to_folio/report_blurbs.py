blurbs = {
    "Introduction": "<br/>Data errors preventing records from being migrated are marked **FIX BEFORE MIGRATION**. The library is advised to clean up these errors in the source data.<br/><br/> The sections related to field counts and mapping results are marked **REVIEW**. These do not indicate errors preventing records from being migrated, but may point to data anomalies or in the mappings. The library should review these to make sure that the numbers are what one would expect, knowing the source data. Is this the expected number of serials? Is this the expected number of cartographic materials?",
    "Mapped Legacy fields": "Library action: **REVIEW** <br/>This table lists all the MARC fields in the source data, and whether it has been mapped to a FOLIO instance record field. The library should examine the MARC tags with a high 'Unmapped' figure and determine if these MARC tags contain data that you would like mapped to the FOLIO instance record.",
    "Mapped FOLIO fields": "Library action: **REVIEW** <br/>This table shows how many of the FOLIO instance records created contain data in the different FOLIO fields. The library should review the mapped totals against what they would expect to see mapped.",
    "__Section 1: instances": "This entries below seem to be related to instances",
    "Record status (leader pos 5)": "**Consider fixing d-values before migration**<br/>An overview of the Record statuses (Leader position 5) present in your source data.    Pay attention to the number of occurrences of the value 'd'. These d's are expressing that they are deleted, and the records might not work as expected in FOLIO. Consider marking them as suppressed in your current system and export them as a separate batch in order to have them suppressed in FOLIO.",
    "Bib records that failed to parse": "**FIX BEFORE MIGRATION** This section outputs the contents of records that could not be parsed by the transformation script (e.g. due to encoding issues). These should be reviewed by the library. The records cannot be migrated until they parse correctly.",
    "Records failed to migrate due to Value errors found in Transformation": "**FIX BEFORE MIGRATION** This section identifies records that have unexpected or missing values that prevent the transformation. The type of error will be specified. The library must resolve the issue for the record to be migrated.",
    "Records without titles": "**FIX IN SOURCE DATA** These records are missing a 245 field. FOLIO requires an instance title. The library must enter this information for the record to be migrated.",
    "Records without Instance Type Ids": "**IC ACTION REQUIRED** These reords should get an instance type ID mapped from 336, or a default of Undefined, or they will not be transformed.",
    "Mapped instance formats": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Instance format values. The library should review the total number for each value against what they would expect to see mapped.",
    "Mapped identifier types": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Identifier type values. The library should review the total number for each value against what they would expect to see mapped.",
    "Mapped note types": "**REVIEW** <br/>The created FOLIO instances contain the following Note type values.  <br/>The library should review the total number for each value against what they would expect to see mapped.",
    "Mapped contributor name types": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Name type values. The library should review the total number for each value against what they would expect to see mapped.",
    "Unmapped contributor name types": "**REVIEW/IC ACTION REQUIRED** <br/>Contributor bame types present in the source data, but not mapped to a FOLIO value. The library and IC should review values and mapping.",
    "Contributor type mapping": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Contributor type values. The library should review the total number for each value against what they would expect to see mapped.",
    "Mapped electronic access relationships types": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Electronic access relationship type values. The library should review the total number for each value against what they would expect to see mapped.",
    "Incomplete entity mapping adding entity": "**NO ACTION REQUIRED** <br/>This is a coding anomaly that FSE will look into.  <br/>Usually, the library does not have to do anything about it.<br/> One thing to look at is if there are many repeated subfields or unexpected patterns of subfields in the table.",
    "Resource Type Mapping (336, 008)": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Instance type values. The library should review the total number for each value against what they would expect to see mapped.",
    "Mapped Alternative title types": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Alternative title type values. The library should review the total number for each value against what they would expect to see mapped.",
    "880 mappings": "This table shows how the 880 (Alternate Graphic Representation) has been mapped.",
    "880 mappings: mapped field not in mapping-rules": "Library action: **REVIEW** <br/>Fields that are referenced in the 880 mapping, but not configured in the mapping-rules.",
    "Instance level callNumber": "Library action: **REVIEW** <br/>True if the source data contains bib level call numbers in MARC field 099.",
    "Non-numeric tags in records": "Library action: **REVIEW** <br/>Non-numeric tags may indicate locally defined fields.",
    "Instance format ids handling (337 + 338)": "Library action: **REVIEW** <br/>This is how data in source MARC fields 337 and 338 have been mapped to FOLIO instance format ID.",
    "Unspecified Modes of issuance code": "Library action: **REVIEW** <br/>Number of created FOLIO instances with Mode of issueance set to *Unspecified*.",
    "Matched Modes of issuance code": "Library action: **REVIEW** <br/>The created FOLIO instances contain the following Mode of issuace values. The library should review the total number for each value against what they would expect to see mapped.",
    "Unrecognized language codes in records": "Library action: **REVIEW** <br/>Language code values in the source data that do not match standard language codes. If not fixed before migration, these will display as Undetermined in the instance record.",
    "__Section 2: holdings": "The entries below seem to be related to holdings",
    "Callnumber types": "Section description to be added.",
    "Holdings type mapping": "Section description to be added.",
    "Legacy location codes": "Section description to be added.",
    "Locations - Unmapped legacy codes": "Section description to be added.",
    "Mapped Locations": "Section description to be added.",
    "Leader 06 (Holdings type)": "Section description to be added.",
    "__Section 3: items": "The entries below seem to be related to items",
    "ValueErrors": "Section description to be added.",
    "Exceptions": "Section description to be added.",
    "Top missing holdings ids": "Section description to be added.",
    "Top duplicate item ids": "Section description to be added.",
    "Missing location codes": "Section description to be added.",
    "Circulation notes": "Section description to be added.",
    "Call number legacy typesName - Not yet mapped": "Section description to be added.",
    "Legacy item status - Not mapped": "Section description to be added.",
    "Mapped Material Types": "Section description to be added.",
    "Unapped Material Types": "Section description to be added.",
    "Mapped loan types": "Section description to be added.",
    "Unmapped loan types": "Section description to be added.",
    "HRID Handling": "Section description to be added.",
    "Preceeding and Succeeding titles": "Section description to be added.",
    "Holdings generation from bibs": "Section description to be added.",
    "Instance format ids handling (337 + 338))": "Section description to be added.",
    "Mapped classification types": "Section description to be added.",
    "Location mapping": "These are the results for the mapping between legacy locations and your new FOLIO location structure",
    "Value set in mapping file": "The value for these fields are set in the mapping file instead of coming from the legacy system data.",
    "Values mapped from legacy fields": "A list fo the values and what they were mapped to"
}
