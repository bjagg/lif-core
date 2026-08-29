from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from lif.mdr_dto.datamodel_dto import DataModelDTO
from lif.mdr_dto.import_export_dto import (
    CreateCloneDTO,
    DataModelExportDTO,
    ImportDataModelDTO,
    SingleDataModelExportDTO,
)
from lif.mdr_services import import_export_service
from lif.mdr_utils.database_setup import get_session
from lif.mdr_utils.logger_config import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = get_logger(__name__)


@router.get("/export/{data_model_id}", response_model=DataModelExportDTO)
async def export_data_model(data_model_id: int, session: AsyncSession = Depends(get_session)):
    data_model = await import_export_service.export_datamodel(session=session, id=data_model_id)
    return data_model


@router.get("/export/portable/{data_model_id}", response_model=ImportDataModelDTO)
async def export_data_model_portable(data_model_id: int, session: AsyncSession = Depends(get_session)):
    """Name-based export ready to POST straight back to /import/ on another install."""
    return await import_export_service.export_datamodel_portable(session=session, id=data_model_id)


@router.get("/export/multiple/", response_model=List[SingleDataModelExportDTO])
async def export_data_model(ids: List[int] = Query(...), session: AsyncSession = Depends(get_session)):
    data_model = await import_export_service.export_multiple_datamodel(session=session, ids=ids)
    return data_model


@router.post("/import/", response_model=Dict[Any, Any])
async def create_entity(data: ImportDataModelDTO, session: AsyncSession = Depends(get_session)):
    return await import_export_service.import_datamodel(session=session, data=data)


@router.post("/clone/", response_model=DataModelDTO)
async def create_entity(data: CreateCloneDTO, session: AsyncSession = Depends(get_session)):
    return await import_export_service.clone_datamodel(session=session, data=data)
