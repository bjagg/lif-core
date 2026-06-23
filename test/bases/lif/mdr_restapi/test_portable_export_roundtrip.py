"""End-to-end export->import round-trip for the name-based portable serializer.

Exercises the whole portability path against a live Postgres DB:

    seed a source model (entities, an attribute + association, an entity reference,
    a data-model constraint)
        -> export_datamodel_portable   (ID-based rows rewritten to name-based refs)
        -> import_datamodel            (names resolved against freshly created rows)

and asserts every cross-row reference survives as a *name*: the attribute lands on the
right entity, the entity association points parent->child, and the constraint targets the
right element — none of it leaking the source database's primary keys.
"""

from sqlmodel import select

from lif.datatypes.mdr_sql_model import (
    Attribute,
    DataModel,
    DataModelConstraints,
    DataModelType,
    DatamodelElementType,
    Entity,
    EntityAssociation,
    EntityAttributeAssociation,
    EntityPlacementType,
    ValueSet,
    ValueSetValue,
)
from lif.mdr_services.import_export_service import export_datamodel_portable, import_datamodel


async def _seed_source_model(session):
    dm = DataModel(
        Name="PortableRoundTripSource",
        Type=DataModelType.SourceSchema,
        DataModelVersion="1.0",
        ContributorOrganization="UniconQA",
        Deleted=False,
    )
    session.add(dm)
    await session.commit()
    await session.refresh(dm)

    person = Entity(Name="Person", UniqueName="Person", DataModelId=dm.Id, Array="No", Required="No", Deleted=False)
    org = Entity(
        Name="Organization", UniqueName="Organization", DataModelId=dm.Id, Array="No", Required="No", Deleted=False
    )
    session.add(person)
    session.add(org)
    await session.commit()
    await session.refresh(person)
    await session.refresh(org)

    gender_vs = ValueSet(Name="GenderCode", DataModelId=dm.Id, Deleted=False)
    session.add(gender_vs)
    await session.commit()
    await session.refresh(gender_vs)
    session.add(ValueSetValue(ValueSetId=gender_vs.Id, DataModelId=dm.Id, Value="F", ValueName="Female", Deleted=False))

    first_name = Attribute(
        Name="firstName", UniqueName="firstName", DataType="string", DataModelId=dm.Id, Deleted=False
    )
    gender = Attribute(
        Name="gender", UniqueName="gender", DataType="string", DataModelId=dm.Id, ValueSetId=gender_vs.Id, Deleted=False
    )
    session.add(first_name)
    session.add(gender)
    await session.commit()
    await session.refresh(first_name)
    await session.refresh(gender)

    session.add(EntityAttributeAssociation(EntityId=person.Id, AttributeId=first_name.Id, Deleted=False))
    session.add(EntityAttributeAssociation(EntityId=person.Id, AttributeId=gender.Id, Deleted=False))
    session.add(
        EntityAssociation(
            ParentEntityId=person.Id,
            ChildEntityId=org.Id,
            Relationship="employedBy",
            Placement=EntityPlacementType.Reference,
            Deleted=False,
        )
    )
    session.add(
        DataModelConstraints(
            ForDataModelId=dm.Id,
            ElementType=DatamodelElementType.Entity,
            ElementId=person.Id,
            ConstraintType="Required",
            Contributor="tester",
            ContributorOrganization="UniconQA",
            Deleted=False,
        )
    )
    await session.commit()
    return dm


async def test_portable_export_import_roundtrip(test_db_session):
    session = test_db_session
    source = await _seed_source_model(session)

    portable = await export_datamodel_portable(session, source.Id)

    # The serializer must have rewritten every DB-id reference as a name.
    assert portable.DataModel.BaseDataModelId is None
    attr = next(a for a in portable.Attributes if a.Name == "firstName")
    assert attr.EntityName == "Person"
    gender_attr = next(a for a in portable.Attributes if a.Name == "gender")
    assert gender_attr.EntityName == "Person"
    assert gender_attr.ValueSetName == "GenderCode"  # ValueSetId rewritten to its name
    assert any(
        ea.ParentEntityName == "Person" and ea.ChildEntityName == "Organization" for ea in portable.EntityAssociation
    )
    assert [c.ElementName for c in portable.DataModelConstraints] == ["Person"]

    # Import into a fresh model on the same DB (rename to avoid the unique-name guard).
    portable.DataModel.Name = "PortableRoundTripTarget"
    result = await import_datamodel(session, portable)
    assert result == {"ok": True}

    target = (
        (await session.execute(select(DataModel).where(DataModel.Name == "PortableRoundTripTarget"))).scalars().first()
    )
    assert target is not None and target.Id != source.Id

    entities = (
        (await session.execute(select(Entity).where(Entity.DataModelId == target.Id, Entity.Deleted == False)))
        .scalars()
        .all()
    )
    by_name = {e.Name: e.Id for e in entities}
    assert sorted(by_name) == ["Organization", "Person"]

    # Attribute resolved onto the right entity via its EntityName.
    target_attr = (
        (
            await session.execute(
                select(Attribute).where(Attribute.DataModelId == target.Id, Attribute.Name == "firstName")
            )
        )
        .scalars()
        .first()
    )
    assert target_attr is not None
    eaa = (
        (
            await session.execute(
                select(EntityAttributeAssociation).where(
                    EntityAttributeAssociation.EntityId == by_name["Person"],
                    EntityAttributeAssociation.AttributeId == target_attr.Id,
                )
            )
        )
        .scalars()
        .first()
    )
    assert eaa is not None

    # Entity association resolved parent->child with its relationship preserved.
    assoc = (
        (
            await session.execute(
                select(EntityAssociation)
                .join(Entity, Entity.Id == EntityAssociation.ParentEntityId)
                .where(Entity.DataModelId == target.Id, EntityAssociation.Deleted == False)
            )
        )
        .scalars()
        .first()
    )
    assert assoc is not None
    assert assoc.ParentEntityId == by_name["Person"]
    assert assoc.ChildEntityId == by_name["Organization"]
    assert assoc.Relationship == "employedBy"

    # Value set recreated and the gender attribute re-linked to it by name.
    target_vs = (
        (
            await session.execute(
                select(ValueSet).where(ValueSet.DataModelId == target.Id, ValueSet.Name == "GenderCode")
            )
        )
        .scalars()
        .first()
    )
    assert target_vs is not None
    target_gender = (
        (await session.execute(select(Attribute).where(Attribute.DataModelId == target.Id, Attribute.Name == "gender")))
        .scalars()
        .first()
    )
    assert target_gender is not None and target_gender.ValueSetId == target_vs.Id

    # Constraint persisted, element resolved by name, ForDataModelId remapped to the new model.
    constraint = (
        (await session.execute(select(DataModelConstraints).where(DataModelConstraints.ForDataModelId == target.Id)))
        .scalars()
        .first()
    )
    assert constraint is not None
    assert constraint.ElementType == DatamodelElementType.Entity
    assert constraint.ElementId == by_name["Person"]
