from typing import List
from fastapi import HTTPException
from lif.datatypes.mdr_sql_model import (
    Attribute,
    DataModel,
    DataModelType,
    DatamodelElementType,
    Entity,
    EntityAssociation,
    EntityAttributeAssociation,
    Transformation,
    TransformationAttribute,
    TransformationGroup,
    ValueSet,
    ValueSetValue,
)
from lif.mdr_dto.attribute_dto import AttributeDTO, CreateAttributeDTO
from lif.mdr_dto.datamodel_constraints_dto import CreateDataModelConstraintsDTO, DataModelConstraintsDTO
from lif.mdr_dto.datamodel_dto import CreateDataModelDTO, DataModelDTO
from lif.mdr_dto.entity_association_dto import CreateEntityAssociationDTO, EntityAssociationDTO
from lif.mdr_dto.entity_attribute_association_dto import (
    CreateEntityAttributeAssociationDTO,
    EntityAttributeAssociationDTO,
)
from lif.mdr_dto.entity_dto import CreateEntityDTO, EntityDTO
from lif.mdr_dto.import_export_dto import (
    CreateCloneDTO,
    DataModelExportDTO,
    ImportAttributeDTO,
    ImportDataModelConstraintsDTO,
    ImportDataModelDTO,
    ImportEntityAssociationDTO,
    ImportEntityDTO,
    ImportValueSetDTO,
    ImportValueSetValueDTO,
    ImportValueSetWithValuesDTO,
    SingleDataModelExportDTO,
    ValueSetExportDTO,
)
from lif.mdr_dto.value_set_values_dto import CreateValuesWithValueSetDTO
from lif.mdr_dto.valueset_dto import CreateValueSetDTO, CreateValueSetWithValuesDTO
from lif.mdr_services.attribute_service import create_attribute, get_list_of_attributes_for_data_model
from lif.mdr_services.datamodel_constraints_service import (
    create_data_model_constraint,
    get_data_model_constraints_by_data_model_id,
)
from lif.mdr_services.datamodel_service import (
    check_unique_data_model_exists,
    create_datamodel,
    get_base_model_for_given_orglif,
    get_datamodel_by_id,
)
from lif.mdr_services.entity_association_service import (
    create_entity_association,
    get_entity_associations_by_data_model_id,
)
from lif.mdr_services.entity_attribute_association_service import (
    create_entity_attribute_association,
    get_entity_attribute_associations_by_data_model_id,
)
from lif.mdr_services.entity_service import create_entity, get_list_of_entities_for_data_model
from lif.mdr_services.transformation_service import get_transformations_by_data_model_id
from lif.mdr_services.value_set_values_service import get_list_of_values_for_value_set
from lif.mdr_services.valueset_service import create_value_set_with_values, get_paginated_value_sets_by_data_model_id
from lif.mdr_utils.logger_config import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import aliased
from sqlalchemy import or_

logger = get_logger(__name__)


async def export_datamodel(session: AsyncSession, id: int):
    data_model = await get_datamodel_by_id(session=session, id=id)
    (
        entity_list,
        attribute_list,
        value_set_list,
        transformations,
        entity_associations,
        entity_attribute_associations,
        data_model_constraints,
    ) = await get_export_dto(session=session, data_model_id=data_model.Id)
    data_model_dto = SingleDataModelExportDTO(
        DataModel=data_model,
        Entities=entity_list,
        Attributes=attribute_list,
        ValueSets=value_set_list,
        Transformations=transformations,
        EntityAssociation=entity_associations,
        EntityAttributeAssociation=entity_attribute_associations,
        DataModelConstraints=data_model_constraints,
    )

    base_model_dto: SingleDataModelExportDTO = None

    if data_model.Type == DataModelType.OrgLIF or data_model.Type == DataModelType.PartnerLIF:
        base_model = await get_base_model_for_given_orglif(session=session, extended_data_model_id=data_model.Id)
        (
            entity_list,
            attribute_list,
            value_set_list,
            transformations,
            entity_associations,
            entity_attribute_associations,
            data_model_constraints,
        ) = await get_export_dto(session=session, data_model_id=base_model.Id)
        base_model_dto = SingleDataModelExportDTO(
            DataModel=base_model,
            Entities=entity_list,
            Attributes=attribute_list,
            ValueSets=value_set_list,
            Transformations=transformations,
            EntityAssociation=entity_associations,
            EntityAttributeAssociation=entity_attribute_associations,
            DataModelConstraints=data_model_constraints,
        )

    if base_model_dto:
        return DataModelExportDTO(ExtendedDataModel=data_model_dto, BaseDataModel=base_model_dto)
    else:
        return DataModelExportDTO(ExtendedDataModel=None, BaseDataModel=data_model_dto)


async def get_export_dto(session: AsyncSession, data_model_id: int):
    # Get entities (get_list_of_entities_for_data_model has no check_base param)
    total_entity_count, entity_list = await get_list_of_entities_for_data_model(
        session=session, data_model_id=data_model_id, pagination=False
    )

    # Get Attributes
    total_attribute_count, list_of_attributes_dtos = await get_list_of_attributes_for_data_model(
        session=session, data_model_id=data_model_id, pagination=False, check_base=False
    )

    # Getting value set and its values
    total_value_set_count, value_set_list = await get_paginated_value_sets_by_data_model_id(
        session=session, data_model_id=data_model_id, pagination=False
    )
    list_value_set_export_dtos: list[ValueSetExportDTO] = []
    for value_set in value_set_list:
        total_values, values = await get_list_of_values_for_value_set(
            session=session, valueset_id=value_set.Id, pagination=False
        )
        value_set_export_dto = ValueSetExportDTO(ValueSet=value_set, Values=values)
        list_value_set_export_dtos.append(value_set_export_dto)

    # Getting all the transformation
    transformations = await get_transformations_by_data_model_id(session=session, data_model_id=data_model_id)

    # Getting Entity associations (get_entity_associations_by_data_model_id has no check_base param)
    entity_associations = await get_entity_associations_by_data_model_id(session=session, data_model_id=data_model_id)

    total_association, entity_attribute_associations = await get_entity_attribute_associations_by_data_model_id(
        session=session, data_model_id=data_model_id, pagination=False
    )

    total_constraints, data_model_constraints = await get_data_model_constraints_by_data_model_id(
        session=session, data_model_id=data_model_id, pagination=False
    )

    return (
        entity_list,
        list_of_attributes_dtos,
        list_value_set_export_dtos,
        transformations,
        entity_associations,
        entity_attribute_associations,
        data_model_constraints,
    )


async def export_multiple_datamodel(session: AsyncSession, ids: list[int]):
    data_model_list: List[SingleDataModelExportDTO] = []
    for id in ids:
        data_model = await get_datamodel_by_id(session=session, id=id)
        (
            entity_list,
            attribute_list,
            value_set_list,
            transformations,
            entity_associations,
            entity_attribute_associations,
        ) = await get_export_dto(session=session, data_model_id=data_model.Id)
        data_model_dto = SingleDataModelExportDTO(
            DataModel=data_model,
            Entities=entity_list,
            Attributes=attribute_list,
            ValueSets=value_set_list,
            Transformations=transformations,
            EntityAssociation=entity_associations,
            EntityAttributeAssociation=entity_attribute_associations,
        )
        data_model_list.append(data_model_dto)
    return data_model_list


def build_import_data_model_dto(
    data_model: DataModelDTO,
    entity_list: List[EntityDTO],
    attribute_list: List[AttributeDTO],
    value_set_list: List[ValueSetExportDTO],
    entity_associations: List[EntityAssociationDTO],
    entity_attribute_associations: List[EntityAttributeAssociationDTO],
    data_model_constraints: List[DataModelConstraintsDTO],
) -> ImportDataModelDTO:
    """Convert an ID-based export into the name-based ImportDataModelDTO that import_datamodel consumes.

    Every cross-row reference in the export (EntityId, AttributeId, ValueSetId, ParentEntityId, the
    constraint ElementId, …) is a primary key from the *source* database — a "DB artifact" that means
    nothing in another install. This rewrites each reference as the referenced row's name, the portable
    identity that import_datamodel resolves against the rows it freshly creates.

    Scope: a single data model (SourceSchema and other standalone models). OrgLIF/PartnerLIF extended
    models whose elements span a separate base model are not handled here — import_datamodel takes a
    single ImportDataModelDTO and the base/extended split needs its own design (follow-up).
    """
    entity_name_by_id = {e.Id: e.Name for e in entity_list}
    attribute_name_by_id = {a.Id: a.Name for a in attribute_list}
    value_set_name_by_id = {vs.ValueSet.Id: vs.ValueSet.Name for vs in value_set_list}
    # An attribute's owning entity is expressed only through the entity/attribute association table.
    entity_name_by_attribute_id = {
        eaa.AttributeId: entity_name_by_id.get(eaa.EntityId) for eaa in entity_attribute_associations
    }

    import_entities = [
        ImportEntityDTO(
            Name=e.Name,
            UniqueName=e.UniqueName,
            Description=e.Description,
            UseConsiderations=e.UseConsiderations,
            Required=e.Required,
            Array=e.Array,
            SourceModel=e.SourceModel,
            Notes=e.Notes,
            CreationDate=e.CreationDate,
            ActivationDate=e.ActivationDate,
            DeprecationDate=e.DeprecationDate,
            Contributor=e.Contributor,
            ContributorOrganization=e.ContributorOrganization,
            Extension=e.Extension,
            ExtensionNotes=e.ExtensionNotes,
            Tags=e.Tags,
        )
        for e in entity_list
    ]

    import_attributes = [
        ImportAttributeDTO(
            Name=a.Name,
            DataType=a.DataType or "string",
            EntityName=entity_name_by_attribute_id.get(a.Id),
            UniqueName=a.UniqueName,
            Description=a.Description,
            UseConsiderations=a.UseConsiderations,
            ValueSetName=value_set_name_by_id.get(a.ValueSetId) if a.ValueSetId else None,
            Required=a.Required,
            Array=a.Array,
            SourceModel=a.SourceModel,
            Notes=a.Notes,
            CreationDate=a.CreationDate,
            ActivationDate=a.ActivationDate,
            DeprecationDate=a.DeprecationDate,
            Contributor=a.Contributor,
            ContributorOrganization=a.ContributorOrganization,
            Extension=a.Extension,
            ExtensionNotes=a.ExtensionNotes,
        )
        for a in attribute_list
    ]

    import_value_sets = [
        ImportValueSetWithValuesDTO(
            ValueSet=ImportValueSetDTO(
                Name=vs.ValueSet.Name,
                Description=vs.ValueSet.Description,
                UseConsiderations=vs.ValueSet.UseConsiderations,
                Notes=vs.ValueSet.Notes,
                CreationDate=vs.ValueSet.CreationDate,
                ActivationDate=vs.ValueSet.ActivationDate,
                DeprecationDate=vs.ValueSet.DeprecationDate,
                Contributor=vs.ValueSet.Contributor,
                ContributorOrganization=vs.ValueSet.ContributorOrganization,
                Extension=vs.ValueSet.Extension,
                ExtensionNotes=vs.ValueSet.ExtensionNotes,
            ),
            Values=[
                ImportValueSetValueDTO(
                    Value=v.Value,
                    ValueName=v.ValueName,
                    Description=v.Description,
                    UseConsiderations=v.UseConsiderations,
                    Source=v.Source,
                    Notes=v.Notes,
                    CreationDate=v.CreationDate,
                    ActivationDate=v.ActivationDate,
                    DeprecationDate=v.DeprecationDate,
                    Contributor=v.Contributor,
                    ContributorOrganization=v.ContributorOrganization,
                    Extension=v.Extension,
                    ExtensionNotes=v.ExtensionNotes,
                    # OriginalValueId is intentionally dropped — it is a source-DB value id (artifact).
                )
                for v in vs.Values
            ],
        )
        for vs in value_set_list
    ]

    import_entity_associations: List[ImportEntityAssociationDTO] = []
    for ea in entity_associations:
        parent_name = entity_name_by_id.get(ea.ParentEntityId)
        child_name = entity_name_by_id.get(ea.ChildEntityId)
        if not parent_name or not child_name:
            logger.warning(f"Skipping entity association {ea.Id}: unresolved parent/child entity name")
            continue
        import_entity_associations.append(
            ImportEntityAssociationDTO(
                ParentEntityName=parent_name,
                ChildEntityName=child_name,
                Relationship=ea.Relationship,
                Placement=ea.Placement,
                Notes=ea.Notes,
                CreationDate=ea.CreationDate,
                ActivationDate=ea.ActivationDate,
                DeprecationDate=ea.DeprecationDate,
                Contributor=ea.Contributor,
                ContributorOrganization=ea.ContributorOrganization,
            )
        )

    element_name_by_type = {
        DatamodelElementType.Entity: entity_name_by_id,
        DatamodelElementType.Attribute: attribute_name_by_id,
        DatamodelElementType.ValueSet: value_set_name_by_id,
    }
    import_constraints: List[ImportDataModelConstraintsDTO] = []
    for c in data_model_constraints:
        element_name = element_name_by_type.get(c.ElementType, {}).get(c.ElementId)
        if not element_name:
            logger.warning(f"Skipping constraint {c.Id}: unresolved element for {c.ElementType}/{c.ElementId}")
            continue
        import_constraints.append(
            ImportDataModelConstraintsDTO(
                Name=c.Name,
                Description=c.Description,
                ForDataModelId=c.ForDataModelId,  # source-DB id; import_datamodel remaps it to the new model
                ElementType=c.ElementType,
                ElementName=element_name,
                ConstraintType=c.ConstraintType,
                Notes=c.Notes,
                CreationDate=c.CreationDate,
                ActivationDate=c.ActivationDate,
                DeprecationDate=c.DeprecationDate,
                Contributor=c.Contributor or "",
                ContributorOrganization=c.ContributorOrganization or "",
                Deleted=c.Deleted,
            )
        )

    import_data_model = CreateDataModelDTO(
        Name=data_model.Name,
        Description=data_model.Description,
        UseConsiderations=data_model.UseConsiderations,
        Type=data_model.Type,
        BaseDataModelId=None,  # source-DB id; intentionally dropped for portability
        Notes=data_model.Notes,
        DataModelVersion=data_model.DataModelVersion or "",
        ActivationDate=data_model.ActivationDate,
        DeprecationDate=data_model.DeprecationDate,
        Contributor=data_model.Contributor,
        ContributorOrganization=data_model.ContributorOrganization,
        State=data_model.State,
        Tags=data_model.Tags,
    )

    return ImportDataModelDTO(
        DataModel=import_data_model,
        Entities=import_entities,
        Attributes=import_attributes,
        ValueSets=import_value_sets,
        EntityAssociation=import_entity_associations,
        DataModelConstraints=import_constraints,
    )


async def export_datamodel_portable(session: AsyncSession, id: int) -> ImportDataModelDTO:
    """Export a data model as a portable, name-based ImportDataModelDTO ready to POST back to /import/."""
    data_model = await get_datamodel_by_id(session=session, id=id)
    (
        entity_list,
        attribute_list,
        value_set_list,
        _transformations,  # transformations are not part of ImportDataModelDTO yet (#771)
        entity_associations,
        entity_attribute_associations,
        data_model_constraints,
    ) = await get_export_dto(session=session, data_model_id=data_model.Id)
    return build_import_data_model_dto(
        data_model=data_model,
        entity_list=entity_list,
        attribute_list=attribute_list,
        value_set_list=value_set_list,
        entity_associations=entity_associations,
        entity_attribute_associations=entity_attribute_associations,
        data_model_constraints=data_model_constraints,
    )


async def import_datamodel(session: AsyncSession, data: ImportDataModelDTO):
    entity_name_id = {}
    value_set_name_id = {}
    attribute_name_id = {}

    # Create data model
    data_model = await create_datamodel(session=session, data=data.DataModel)

    # Create Value set with value
    for value_set_value in data.ValueSets:
        value_set = value_set_value.ValueSet
        value_set.DataModelId = data_model.Id
        value_set_dto = CreateValueSetDTO(**value_set.dict())
        list_of_values_dto: List[CreateValuesWithValueSetDTO] = []
        for values in value_set_value.Values:
            values_dto = CreateValuesWithValueSetDTO(**values.dict())
            list_of_values_dto.append(values_dto)
        value_set_with_values_dto = CreateValueSetWithValuesDTO(ValueSet=value_set_dto, Values=list_of_values_dto)
        created_value_set_with_values = await create_value_set_with_values(
            session=session, data=value_set_with_values_dto
        )
        value_set_name_id[value_set.Name] = created_value_set_with_values.Id

    # Create Entities
    for entity_data in data.Entities:
        # entity_data = entity.Entity
        entity_data.DataModelId = data_model.Id
        entity_dto = CreateEntityDTO(**entity_data.dict())
        created_entity = await create_entity(session=session, data=entity_dto)
        entity_name_id[entity_data.Name] = created_entity.Id
        # Create Attributes and Entity Attribute association
        # for attribute in entity.Attributes:
        #     attribute.DataModelId = data_model.Id
        #     attribute.EntityId = created_entity.Id
        #     if attribute.ValueSetName:
        #         value_set_id = value_set_name_id[attribute.ValueSetName]
        #     else:
        #         value_set_id = None
        #     attribute_dto = CreateAttributeDTO(**attribute.dict(), ValueSetId = value_set_id)
        #     created_attribute = await create_attribute(session=session, data=attribute_dto)

    # Create Attributes and Entity Attribute association
    for attribute in data.Attributes:
        attribute.DataModelId = data_model.Id
        # attribute.EntityId = created_entity.Id
        if attribute.ValueSetName:
            value_set_id = value_set_name_id[attribute.ValueSetName]
        else:
            value_set_id = None
        attribute_dto = CreateAttributeDTO(**attribute.dict(), ValueSetId=value_set_id)
        created_attribute = await create_attribute(session=session, data=attribute_dto)
        attribute_name_id[attribute.Name] = created_attribute.Id
        if attribute.EntityName:
            entity_id = entity_name_id[attribute.EntityName]
            association = CreateEntityAttributeAssociationDTO(
                EntityId=entity_id,
                AttributeId=created_attribute.Id,
                Contributor=attribute.Contributor,
                ContributorOrganization=attribute.ContributorOrganization,
            )
            await create_entity_attribute_association(session=session, data=association)

    # Create Entity Association
    for entity_association in data.EntityAssociation:
        parent_entity_id = entity_name_id[entity_association.ParentEntityName]
        child_entity_id = entity_name_id[entity_association.ChildEntityName]
        entity_association_dto = CreateEntityAssociationDTO(
            **entity_association.dict(), ParentEntityId=parent_entity_id, ChildEntityId=child_entity_id
        )
        # entity_association_dto.ParentEntityId = parent_entity_id
        # entity_association_dto.ChildEntityId = child_entity_id
        created_association = await create_entity_association(session=session, data=entity_association_dto)

    # Creating constraints
    skipped_constraints: list[dict] = []
    for constraint in data.DataModelConstraints:
        if constraint.ElementType == DatamodelElementType.Attribute:
            element_id = attribute_name_id.get(constraint.ElementName)
        elif constraint.ElementType == DatamodelElementType.Entity:
            element_id = entity_name_id.get(constraint.ElementName)
        elif constraint.ElementType == DatamodelElementType.ValueSet:
            element_id = value_set_name_id.get(constraint.ElementName)
        else:
            element_id = None

        # `is not None`, not truthiness: a resolved ElementId of 0 is a valid id, not "not found".
        if element_id is not None:
            # ElementName is the portable (name-based) reference; the create DTO wants the
            # resolved DB ElementId. ForDataModelId from the export is a source-DB artifact, so
            # remap it to the model we just created.
            constraint_dto = CreateDataModelConstraintsDTO(
                **constraint.dict(exclude={"ElementName", "ForDataModelId"}),
                ForDataModelId=data_model.Id,
                ElementId=element_id,
            )
            await create_data_model_constraint(session=session, data=constraint_dto)
        else:
            # Don't drop a constraint silently — a malformed/incomplete export (element name not
            # found among the imported attributes/entities/value sets) should be visible, both in
            # the logs and in the response so the caller knows what didn't come across.
            logger.warning(
                "Skipping constraint: %s element %r not found in the imported model",
                constraint.ElementType,
                constraint.ElementName,
            )
            skipped_constraints.append(
                {"element_type": str(constraint.ElementType), "element_name": constraint.ElementName}
            )

    return {"ok": True, "skipped_constraints": skipped_constraints}


async def clone_datamodel(session: AsyncSession, data: CreateCloneDTO):
    if (
        not data.data_model_name
        or not data.data_model_type
        or not data.data_model_version
        or not data.source_data_model_id
    ):
        raise HTTPException(status_code=400, detail="DataModel source mode id, name, type and version are required.")

    if await check_unique_data_model_exists(session, data.data_model_name, data.data_model_version) != None:
        raise HTTPException(status_code=400, detail=f"DataModel with name '{data.data_model_name}' already exists")

    base_data_model_id = None
    if data.data_model_type == DataModelType.OrgLIF or data.data_model_type == DataModelType.PartnerLIF:
        base_data_model_id = data.source_data_model_id

    new_data_model = DataModel(
        Name=data.data_model_name,
        Type=data.data_model_type,
        DataModelVersion=data.data_model_version,
        BaseDataModelId=base_data_model_id,
    )
    session.add(new_data_model)
    await session.commit()
    await session.refresh(new_data_model)

    entity_id_map = await clone_entities(session, data.source_data_model_id, new_data_model.Id)
    value_set_id_map = await clone_value_sets(session, data.source_data_model_id, new_data_model.Id)
    attribute_id_map = await clone_attributes(session, data.source_data_model_id, new_data_model.Id, value_set_id_map)

    logger.info(f"entity_id_map: {entity_id_map}")
    logger.info(f"value_set_id_map: {value_set_id_map}")
    logger.info(f"attribute_id_map: {attribute_id_map}")

    await clone_entity_attribute_association(session, entity_id_map, attribute_id_map, data.source_data_model_id)
    await clone_entity_association(session, entity_id_map, data.source_data_model_id)
    await clone_value_set_values(session, data.source_data_model_id, new_data_model.Id, value_set_id_map)

    transformation_group_id_map = await clone_transformation_group(
        session, data.source_data_model_id, new_data_model.Id
    )
    transformation_id_map = await clone_transformations(session, transformation_group_id_map)
    await clone_transformation_attributes(
        session=session, transformation_id_map=transformation_id_map, attribute_id_map=attribute_id_map
    )
    logger.info(f"transformation_group_id_map: {transformation_group_id_map}")
    logger.info(f"transformation_id_map: {transformation_id_map}")

    return new_data_model


async def clone_entities(session: AsyncSession, source_data_model_id: int, new_data_model_id: int):
    entity_id_map = {}
    # Fetch entities associated with the source data model
    entity_query = select(Entity).where(Entity.DataModelId == source_data_model_id, Entity.Deleted == False)
    result = await session.execute(entity_query)
    entities = result.scalars().all()

    # Clone each entity and associate it with the new data model
    for entity in entities:
        new_entity = Entity(
            Name=entity.Name,
            UniqueName=entity.UniqueName,
            Description=entity.Description,
            DataModelId=new_data_model_id,
            Notes=entity.Notes,
            Contributor=entity.Contributor,
            ContributorOrganization=entity.ContributorOrganization,
            Extension=entity.Extension,
            ExtensionNotes=entity.ExtensionNotes,
            Tags=entity.Tags,
        )
        session.add(new_entity)
        await session.commit()
        await session.refresh(new_entity)

        # Store the mapping between source and new entity IDs
        entity_id_map[entity.Id] = new_entity.Id

    return entity_id_map


async def clone_attributes(
    session: AsyncSession, source_data_model_id: int, new_data_model_id: int, value_set_id_map: dict[int, int]
):
    attribute_id_map = {}
    # Fetch attributes associated with the source entity
    attribute_query = select(Attribute).where(Attribute.DataModelId == source_data_model_id, Attribute.Deleted == False)
    result = await session.execute(attribute_query)
    attributes = result.scalars().all()

    # Clone each attribute and associate it with the new entity
    for attribute in attributes:
        new_attribute = Attribute(
            Name=attribute.Name,
            DataModelId=new_data_model_id,  # Assuming the same DataModel
            DataType=attribute.DataType,
            UniqueName=attribute.UniqueName,
            Notes=attribute.Notes,
            Contributor=attribute.Contributor,
            ContributorOrganization=attribute.ContributorOrganization,
            Extension=attribute.Extension,
            ExtensionNotes=attribute.ExtensionNotes,
            Tags=attribute.Tags,
        )
        if attribute.ValueSetId:
            new_attribute.ValueSetId = value_set_id_map[attribute.ValueSetId]
        session.add(new_attribute)
        await session.commit()
        await session.refresh(new_attribute)

        # Store the mapping between source and new entity IDs
        attribute_id_map[attribute.Id] = new_attribute.Id

    return attribute_id_map


async def clone_entity_attribute_association(
    session: AsyncSession, entity_id_map: dict[int, int], attribute_id_map: dict[int, int], source_data_model_id: int
):
    # Query for associations where the parent entity belongs to the given data model
    entity_query = (
        select(EntityAttributeAssociation)
        .join(Entity, Entity.Id == EntityAttributeAssociation.EntityId)
        .where(
            Entity.DataModelId == source_data_model_id,
            Entity.Deleted == False,
            EntityAttributeAssociation.Deleted == False,
        )
    )

    # Query for associations where the child entity belongs to the given data model
    attribute_query = (
        select(EntityAttributeAssociation)
        .join(Attribute, Attribute.Id == EntityAttributeAssociation.AttributeId)
        .where(
            Attribute.DataModelId == source_data_model_id,
            Attribute.Deleted == False,
            EntityAttributeAssociation.Deleted == False,
        )
    )

    # Combine the two queries using a union
    query = entity_query.union(attribute_query)

    result = await session.execute(query)
    entity_attribute_associations = result.fetchall()
    # entity_attribute_association_query = (select(EntityAttributeAssociation)
    #                    .join(Entity, Entity.Id == EntityAttributeAssociation.EntityId)
    #                    .join(Attribute, Attribute.Id == EntityAttributeAssociation.AttributeId)
    #                    .where(Attribute.DataModelId == source_data_model_id, Entity.DataModelId == source_data_model_id, EntityAttributeAssociation.Deleted == False))
    # result = await session.execute(entity_attribute_association_query)
    # entity_attribute_associations = result.scalars().all()
    for association in entity_attribute_associations:
        if association.EntityId in entity_id_map:
            entity_id = entity_id_map[association.EntityId]
        else:
            entity_id = association.EntityId

        if association.AttributeId in attribute_id_map:
            attribute_id = attribute_id_map[association.AttributeId]
        else:
            attribute_id = association.AttributeId
        logger.info(f"entity_id: {entity_id}")
        logger.info(f"attribute_id: {attribute_id}")
        new_association = EntityAttributeAssociation(
            EntityId=entity_id,
            AttributeId=attribute_id,
            Contributor=association.Contributor,
            ContributorOrganization=association.ContributorOrganization,
        )
        session.add(new_association)
        await session.commit()


async def clone_entity_association(session: AsyncSession, entity_id_map: dict[int, int], source_data_model_id: int):
    # Use aliased entities to avoid conflicts
    ParentEntity = aliased(Entity)
    ChildEntity = aliased(Entity)

    # Query for associations where the parent entity belongs to the given data model
    parent_query = (
        select(EntityAssociation)
        .join(ParentEntity, ParentEntity.Id == EntityAssociation.ParentEntityId)
        .where(ParentEntity.DataModelId == source_data_model_id, EntityAssociation.Deleted == False)
    )

    # Query for associations where the child entity belongs to the given data model
    child_query = (
        select(EntityAssociation)
        .join(ChildEntity, ChildEntity.Id == EntityAssociation.ChildEntityId)
        .where(ChildEntity.DataModelId == source_data_model_id, EntityAssociation.Deleted == False)
    )

    # Combine the two queries using a union
    query = parent_query.union(child_query)

    result = await session.execute(query)
    entity_associations = result.fetchall()

    for association in entity_associations:
        if association.ParentEntityId in entity_id_map:
            parent_entity_id = entity_id_map[association.ParentEntityId]
        else:
            parent_entity_id = association.ParentEntityId

        if association.ChildEntityId in entity_id_map:
            child_entity_id = entity_id_map[association.ChildEntityId]
        else:
            child_entity_id = association.ChildEntityId
        new_association = EntityAssociation(
            ParentEntityId=parent_entity_id,
            ChildEntityId=child_entity_id,
            Contributor=association.Contributor,
            ContributorOrganization=association.ContributorOrganization,
            Extension=association.Extension,
            ExtensionNotes=association.ExtensionNotes,
        )
        session.add(new_association)
        await session.commit()


async def clone_value_sets(session: AsyncSession, source_data_model_id: int, new_data_model_id: int):
    value_set_id_map = {}
    # Fetch value sets associated with the source data model
    value_set_query = select(ValueSet).where(ValueSet.DataModelId == source_data_model_id, ValueSet.Deleted == False)
    result = await session.execute(value_set_query)
    value_sets = result.scalars().all()

    for value_set in value_sets:
        new_value_set = ValueSet(
            Name=value_set.Name,
            DataModelId=new_data_model_id,
            Description=value_set.Description,
            Notes=value_set.Notes,
            Contributor=value_set.Contributor,
            ContributorOrganization=value_set.ContributorOrganization,
            Extension=value_set.Extension,
            ExtensionNotes=value_set.ExtensionNotes,
        )
        session.add(new_value_set)
        await session.commit()
        await session.refresh(new_value_set)
        value_set_id_map[value_set.Id] = new_value_set.Id

    return value_set_id_map


async def clone_value_set_values(session, source_data_model_id: int, new_data_model_id: int, value_set_id_map):
    # Fetch value sets associated with the source data model
    value_set_values_query = select(ValueSetValue).where(
        ValueSetValue.DataModelId == source_data_model_id, ValueSetValue.Deleted == False
    )
    result = await session.execute(value_set_values_query)
    value_set_values = result.scalars().all()

    for value in value_set_values:
        new_value_set_value = ValueSetValue(
            ValueSetId=value_set_id_map[value.ValueSetId],
            DataModelId=new_data_model_id,
            Description=value.Description,
            UseConsiderations=value.UseConsiderations,
            Value=value.Value,
            ValueName=value.ValueName,
            OriginalValueId=value.OriginalValueId,
            Source=value.Source,
            Notes=value.Notes,
            Contributor=value.Contributor,
            ContributorOrganization=value.ContributorOrganization,
            Extension=value.Extension,
            ExtensionNotes=value.ExtensionNotes,
        )
        session.add(new_value_set_value)
    await session.commit()


async def clone_transformation_group(session: AsyncSession, source_data_model_id: int, new_data_model_id: int):
    transformation_group_id_map = {}
    # Fetch entities associated with the source data model
    transformation_group_query = select(TransformationGroup).where(
        or_(
            TransformationGroup.SourceDataModelId == source_data_model_id,
            TransformationGroup.TargetDataModelId == source_data_model_id,
        ),
        TransformationGroup.Deleted == False,
    )
    result = await session.execute(transformation_group_query)
    transformation_groups = result.scalars().all()

    # Clone each entity and associate it with the new data model
    for group in transformation_groups:
        if group.SourceDataModelId == source_data_model_id:
            source_model_id = new_data_model_id
        else:
            source_model_id = group.SourceDataModelId

        if group.TargetDataModelId == source_data_model_id:
            target_model_id = new_data_model_id
        else:
            target_model_id = group.TargetDataModelId
        new_group = TransformationGroup(
            SourceDataModelId=source_model_id,
            TargetDataModelId=target_model_id,
            Name=group.Name,
            Description=group.Description,
            GroupVersion=group.GroupVersion,
            Notes=group.Notes,
            Contributor=group.Contributor,
            ContributorOrganization=group.ContributorOrganization,
            Tags=group.Tags,
            Extension=group.Extension,
            ExtensionNotes=group.ExtensionNotes,
        )
        session.add(new_group)
        await session.commit()
        await session.refresh(new_group)

        # Store the mapping between source and new entity IDs
        transformation_group_id_map[group.Id] = new_group.Id

    return transformation_group_id_map


async def clone_transformations(session: AsyncSession, transformation_group_id_map: dict[int, int]):
    transformation_id_map = {}
    for source_group_id, new_group_id in transformation_group_id_map.items():
        # Fetch entities associated with the source data model
        transformation_query = select(Transformation).where(
            Transformation.Deleted == False, Transformation.TransformationGroupId == source_group_id
        )
        result = await session.execute(transformation_query)
        transformations = result.scalars().all()

        # Clone each entity and associate it with the new data model
        for transformation in transformations:
            new_transformation = Transformation(
                TransformationGroupId=new_group_id,
                Name=transformation.Name,
                Description=transformation.Description,
                UseConsiderations=transformation.UseConsiderations,
                Alignment=transformation.Alignment,
                Expression=transformation.Expression,
                ExpressionLanguage=transformation.ExpressionLanguage,
                InputAttributesCount=transformation.InputAttributesCount,
                OutputAttributesCount=transformation.OutputAttributesCount,
                Notes=transformation.Notes,
                Contributor=transformation.Contributor,
                ContributorOrganization=transformation.ContributorOrganization,
                Extension=transformation.Extension,
                ExtensionNotes=transformation.ExtensionNotes,
            )
            session.add(new_transformation)
            await session.commit()
            await session.refresh(new_transformation)

            # Store the mapping between source and new entity IDs
            transformation_id_map[transformation.Id] = new_transformation.Id

        return transformation_id_map


async def clone_transformation_attributes(
    session: AsyncSession, transformation_id_map: dict[int, int], attribute_id_map: dict[int, int]
):
    for source_tr_id, new_tr_id in transformation_id_map.items():
        # Fetch entities associated with the source data model
        transformation_attribute_query = select(TransformationAttribute).where(
            TransformationAttribute.Deleted == False, TransformationAttribute.TransformationId == source_tr_id
        )
        result = await session.execute(transformation_attribute_query)
        transformation_attributes = result.scalars().all()

        # Clone each entity and associate it with the new data model
        for attribute in transformation_attributes:
            if attribute.AttributeId in attribute_id_map:
                attribute_id = attribute_id_map[attribute.AttributeId]
            else:
                attribute_id = attribute.AttributeId
            new_transformation_attribute = TransformationAttribute(
                AttributeId=attribute_id,
                TransformationId=new_tr_id,
                AttributeType=attribute.AttributeType,
                Notes=attribute.Notes,
                Contributor=attribute.Contributor,
                ContributorOrganization=attribute.ContributorOrganization,
                Extension=attribute.Extension,
                ExtensionNotes=attribute.ExtensionNotes,
            )
            session.add(new_transformation_attribute)
        await session.commit()
