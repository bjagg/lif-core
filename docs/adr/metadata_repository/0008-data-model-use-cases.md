# ADR 0008: MDR Data Model Use Cases

Date: 2026-01-19

## Status
Proposed

## Context
Recent testing of the **MDR** has revealed some questions on Data Model behavior [#790](https://github.com/LIF-Initiative/lif-core/issues/790). As discussions occurred to determine issue resolution, it was noted there was a lack of documented requirements around **MDR** Data Models. This ADR aims to specify requirements of the **MDR** _Data Models_, how existing _Entities_, _Attributes_, and _Value Sets_ are associated, and the behavior of transformations.

This ADR is aimed at what **MDR** _should_ support, not necessarily what it _currently_ supports.

It is not meant as the MDR user guide.

## Decision
The following requirements will govern questions around MDR for the _Data Model_ Types:
- Base LIF
- Org LIF
- Source Schema
- Partner LIF

### General Concepts

**Associated _Entities_ - Reference**

_Entities_ can be associated by **reference** using the (`+ Existing Entity` > `Placement` = `Reference`) UX flow. Since _Entities_ are associated (and not copied) in the system, an update on the origin _Entity_ will reflect in the UX in all associated places.

Child _Entities_ of the associated-by-reference _Entity_ behave the same way as the origin _Entity_, including their _Attributes_.

Child _Attributes_ of these _Entities_ must have the `Required` field set to 'Yes' for the _Attributes_ to display in the _associated_ _Entity_ location(s) (including the schema export), and to be part of a Transformation mapping.

The `Relationship` field is a free form field, but **MDR** recognizes reserved words, such as _TBD_.

**Associated _Entities_ - Embedded**

_Entities_ can be associated by **embedding** using the (`+ Existing Entity` > `Placement` = `Embedded`) UX flow. Since _Entities_ are associated (and not copied) in the system, an update of the origin _Entity_ will reflect in the UX in all associated places.

Child _Attributes_ of these associated-by-embedding _Entities_ will display in the **associated** _Entity_ location(s) (including the schema export), and can be part of a Transformation mapping.

The reference `Relationship` is a free form field, but **MDR** recognizes reserved words, such as TBD.

**Associated _Attributes_**

_Attributes_ can be associated using the (`+ Existing Attribute`) UX flow, and there is a single type of _Attribute_ association. Since _Attributes_ are associated (and not copied) in the system, an update on the origin _Attribute_ will reflect in the UX in all associated places.

**Associated _Value Sets_**

_Value Sets_ can be 'associated' using the (`+ Existing Value Set`) UX flow. This association is different than _Entity_ and _Attribute_ associations in the database, where the ID of the _Value Set_ is directly set on the _Attribute_ record. Since _Value Sets_ are associated (and not copied) in the system, an update on the origin _Value Set_ will reflect in the UX in all associated places.

_Values_ directly reference their _Value Set_ and cannot be associated to other _Value Sets_.

**Data Portability**

All models and transformations can be exported from a LIF system and imported into another LIF system. While database IDs show up in the exports, they are used in the scope of that specific export (as opposed to being leveraged in the import process to avoid duplicate entries). The partial exception to this are _Data Model_ IDs. On import, the caller specifies a default _Data Model_ ID, along with a mapping of _Data Model_ IDs to provide the context in which to import the _Entities__, _Attributes_, etc.

In order to maintain portable data:

* **Data Models** have a unique name & version (and each version of a _Data Model_ receives it's own ID)
* **Entities** are unique by their origin _Data Model_ ID and the _Entity's_ `UniqueName` (meant to be the path of the _Entity_, such as `person.details.birth_location`)
* **Attributes** are unique by their origin _Data Model_ ID and the _Attribute's_ `UniqueName` (meant to be the path of the _Attribute_, such as `person.details.birth_location.city`). In an export, entries that have a `ValueSetId`, even if the value of the `ValueSetId` field is `null`, is considered to be an _Attribute_.
* **ValueSets** are unique by their origin _Data Model_ ID and the _ValueSet's_ `Name`.
* **Values** are unique by their origin _ValueSet_ ID and the `ValueName`.

#### Transformations / Mappings

One of the primary benefits of using MDR is the ability to _map_ or _transform_ a block of JSON from one form into another. Any _Data Model_ in the LIF system can be used as the source or target for this transformation.

Transformations can only be made between _Attributes_.

### Base LIF

The foundational model that all LIF adopters can use to seed and enhance their _Org LIF_ models. The intent is the LIF Steward manages the _Base LIF_ model, however since the LIF system is open source, anyone _could_ edit their copy of the _Base LIF_ model. 

In order for an _Org LIF_ or _Partner LIF_ model to be in the system, there will need to be a _Base LIF_.

#### Number Supported

Number of models supported per LIF system: 0 - 1

#### Associated _Entities_ - Reference

Supported.

The origin _Entity_ must be within the _Base LIF_.

#### Associated _Entities_ - Embedded

Supported.

The origin _Entity_ must be within the _Base LIF_.

#### Associated _Attributes_

Supported.

The origin _Attribute_ must be within the _Base LIF_.

#### Associated _Value Sets_

Supported.

The origin _Value Set_ must be within the _Base LIF_.

#### Org LIF

A model specific to the LIF adopter, seeded and reliant on references from the _Base LIF_ model (known as inclusions), and enhancements added directly by the LIF adopter (known as extensions). 

Requires the _Base LIF_ to be present.

#### Number Supported

Number of models supported per LIF system: 0 - 1

#### Associated _Entities_ - Reference

Supported.

The origin _Entity_ must be within the _Base LIF_ or _Org LIF_.

#### Associated _Entities_ - Embedded

Supported.

The origin _Entity_ must be within the _Base LIF_ or _Org LIF_.

#### Associated _Attributes_

Supported.

The origin Attribute must be within the _Base LIF_ or _Org LIF_.

#### Associated _Value Sets_

Supported.

The origin _Value Set_ must be within the _Base LIF_ or _Org LIF_.

### Source Schema

A self-contained model, without any dependencies on other data model types (including other _Source Schemas_). 

#### Number Supported

Number of models supported per LIF system: 0 - M

#### Associated _Entities_ - Reference

Supported.

The origin _Entity_ must be within the _Source Schema_.

#### Associated _Entities_ - Embedded

Supported.

The origin _Entity_ must be within the _Source Schema_.

#### Associated _Attributes_

Supported.

The origin _Attribute_ must be within the _Source Schema_.

#### Associated _Value Sets_

Supported.

The origin _Value Set_ must be within the _Source Schema_.

### Partner LIF

An _Org LIF_ from a different LIF system. It will likely have references into the _Base LIF_ model (hence the importance of having the _Base LIF_ model be consistent across LIF systems). It is not meant to be altered as a _Partner LIF_ model. Instead, the origin _Org LIF_ should be adjusted as needed, exported, and then imported into a target LIF system as a _Partner LIF_ model. 

#### Number Supported

Number of models supported per LIF system: 0 - N

#### Associated _Entities_ - Reference

Supported on import, but not for editing in the target LIF system.

#### Associated _Entities_ - Embedded

Supported on import, but not for editing in the target LIF system.

#### Associated _Attributes_

Supported on import, but not for editing in the target LIF system.

#### Associated _Value Sets_

Supported on import, but not for editing in the target LIF system.

## Alternatives
A variety of alternatives could exist. The design was chosen to best serve the community.

## Consequences
Some changes to the **MDR** will be needed to achieve alignment with this design.

## References
- https://github.com/LIF-Initiative/lif-core/issues/790
- https://github.com/LIF-Initiative/lif-core/issues/792
