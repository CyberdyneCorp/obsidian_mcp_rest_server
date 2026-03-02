"""Table routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, File, Query, UploadFile, status
from fastapi.responses import Response

from app.api.dependencies import (
    CurrentUserDep,
    DocumentRepoDep,
    DocumentTableLinkRepoDep,
    RowRepoDep,
    TableRepoDep,
    VaultRepoDep,
)
from app.api.schemas.table import (
    ColumnResponse,
    RowCreate,
    RowListResponse,
    RowResponse,
    RowUpdate,
    TableCreate,
    TableListResponse,
    TableResponse,
    TableSummaryResponse,
    TableUpdate,
)
from app.application.dto.table_dto import (
    RowCreateDTO,
    RowUpdateDTO,
    TableCreateDTO,
    TableUpdateDTO,
)
from app.application.use_cases.table import (
    AppendCsvUseCase,
    CreateTableUseCase,
    DeleteTableUseCase,
    ExecuteQueryUseCase,
    ExportCsvUseCase,
    GetTableUseCase,
    ImportCsvUseCase,
    ListTablesUseCase,
    UpdateTableUseCase,
)
from app.application.use_cases.row import (
    CreateRowUseCase,
    DeleteRowUseCase,
    GetRowUseCase,
    ListRowsUseCase,
    UpdateRowUseCase,
)
from app.domain.exceptions import DomainException

router = APIRouter()
logger = logging.getLogger(__name__)


# Table endpoints
@router.get("/vaults/{slug}/tables", response_model=TableListResponse)
async def list_tables(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> TableListResponse:
    """List tables in a vault."""
    logger.debug(f"GET /vaults/{slug}/tables user={current_user.id}")
    use_case = ListTablesUseCase(vault_repo, table_repo)

    tables, total = await use_case.execute(
        current_user.id,
        slug,
        limit=limit,
        offset=offset,
    )

    return TableListResponse(
        tables=[
            TableSummaryResponse(
                id=t.id,
                name=t.name,
                slug=t.slug,
                description=t.description,
                column_count=t.column_count,
                row_count=t.row_count,
                updated_at=t.updated_at,
            )
            for t in tables
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/vaults/{slug}/tables/{table_slug}", response_model=TableResponse)
async def get_table(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
) -> TableResponse:
    """Get table by slug."""
    logger.debug(f"GET /vaults/{slug}/tables/{table_slug} user={current_user.id}")
    use_case = GetTableUseCase(vault_repo, table_repo)

    table = await use_case.execute(current_user.id, slug, table_slug)

    return TableResponse(
        id=table.id,
        name=table.name,
        slug=table.slug,
        description=table.description,
        columns=[
            ColumnResponse(
                name=col.name,
                type=col.type,
                required=col.required,
                unique=col.unique,
                default=col.default,
                description=col.description,
                reference_table=col.reference_table,
                reference_column=col.reference_column,
                array_type=col.array_type,
                formula=col.formula,
            )
            for col in table.columns
        ],
        row_count=table.row_count,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


@router.post(
    "/vaults/{slug}/tables",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_table(
    slug: str,
    data: TableCreate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
) -> TableResponse:
    """Create a new table."""
    logger.info(f"POST /vaults/{slug}/tables name={data.name} user={current_user.id}")
    use_case = CreateTableUseCase(vault_repo, table_repo)

    # Convert pydantic model to list of dicts
    columns = [col.model_dump() for col in data.columns]

    table = await use_case.execute(
        current_user.id,
        slug,
        TableCreateDTO(
            name=data.name,
            columns=columns,
            description=data.description,
            slug=data.slug,
        ),
    )

    return TableResponse(
        id=table.id,
        name=table.name,
        slug=table.slug,
        description=table.description,
        columns=[
            ColumnResponse(
                name=col.name,
                type=col.type,
                required=col.required,
                unique=col.unique,
                default=col.default,
                description=col.description,
                reference_table=col.reference_table,
                reference_column=col.reference_column,
                array_type=col.array_type,
                formula=col.formula,
            )
            for col in table.columns
        ],
        row_count=table.row_count,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


@router.patch("/vaults/{slug}/tables/{table_slug}", response_model=TableResponse)
async def update_table(
    slug: str,
    table_slug: str,
    data: TableUpdate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
) -> TableResponse:
    """Update a table."""
    logger.info(f"PATCH /vaults/{slug}/tables/{table_slug} user={current_user.id}")
    use_case = UpdateTableUseCase(vault_repo, table_repo)

    # Convert pydantic models to list of dicts if provided
    columns = [col.model_dump() for col in data.columns] if data.columns else None

    table = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        TableUpdateDTO(
            name=data.name,
            description=data.description,
            columns=columns,
        ),
    )

    return TableResponse(
        id=table.id,
        name=table.name,
        slug=table.slug,
        description=table.description,
        columns=[
            ColumnResponse(
                name=col.name,
                type=col.type,
                required=col.required,
                unique=col.unique,
                default=col.default,
                description=col.description,
                reference_table=col.reference_table,
                reference_column=col.reference_column,
                array_type=col.array_type,
                formula=col.formula,
            )
            for col in table.columns
        ],
        row_count=table.row_count,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


@router.delete(
    "/vaults/{slug}/tables/{table_slug}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_table(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
) -> None:
    """Delete a table."""
    logger.info(f"DELETE /vaults/{slug}/tables/{table_slug} user={current_user.id}")
    use_case = DeleteTableUseCase(vault_repo, table_repo)

    await use_case.execute(current_user.id, slug, table_slug)


# Row endpoints
@router.get("/vaults/{slug}/tables/{table_slug}/rows", response_model=RowListResponse)
async def list_rows(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    sort: str | None = Query(default=None, description="Column to sort by"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    q: str | None = Query(default=None, description="Full-text search query"),
) -> RowListResponse:
    """List rows in a table."""
    logger.debug(f"GET /vaults/{slug}/tables/{table_slug}/rows user={current_user.id}")
    use_case = ListRowsUseCase(vault_repo, table_repo, row_repo)

    rows, total = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        limit=limit,
        offset=offset,
        sort_column=sort,
        sort_order=order,
        search_query=q,
    )

    return RowListResponse(
        rows=[
            RowResponse(
                id=r.id,
                table_id=r.table_id,
                data=r.data,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/vaults/{slug}/tables/{table_slug}/rows/{row_id}",
    response_model=RowResponse,
)
async def get_row(
    slug: str,
    table_slug: str,
    row_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
) -> RowResponse:
    """Get a row by ID."""
    logger.debug(f"GET /vaults/{slug}/tables/{table_slug}/rows/{row_id} user={current_user.id}")
    use_case = GetRowUseCase(vault_repo, table_repo, row_repo)

    row = await use_case.execute(current_user.id, slug, table_slug, row_id)

    return RowResponse(
        id=row.id,
        table_id=row.table_id,
        data=row.data,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post(
    "/vaults/{slug}/tables/{table_slug}/rows",
    response_model=RowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_row(
    slug: str,
    table_slug: str,
    data: RowCreate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
) -> RowResponse:
    """Create a new row."""
    logger.info(f"POST /vaults/{slug}/tables/{table_slug}/rows user={current_user.id}")
    use_case = CreateRowUseCase(vault_repo, table_repo, row_repo)

    row = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        RowCreateDTO(data=data.data),
    )

    return RowResponse(
        id=row.id,
        table_id=row.table_id,
        data=row.data,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.patch(
    "/vaults/{slug}/tables/{table_slug}/rows/{row_id}",
    response_model=RowResponse,
)
async def update_row(
    slug: str,
    table_slug: str,
    row_id: UUID,
    data: RowUpdate,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
) -> RowResponse:
    """Update a row."""
    logger.info(f"PATCH /vaults/{slug}/tables/{table_slug}/rows/{row_id} user={current_user.id}")
    use_case = UpdateRowUseCase(vault_repo, table_repo, row_repo)

    row = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        row_id,
        RowUpdateDTO(data=data.data),
    )

    return RowResponse(
        id=row.id,
        table_id=row.table_id,
        data=row.data,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete(
    "/vaults/{slug}/tables/{table_slug}/rows/{row_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_row(
    slug: str,
    table_slug: str,
    row_id: UUID,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
) -> None:
    """Delete a row."""
    logger.info(f"DELETE /vaults/{slug}/tables/{table_slug}/rows/{row_id} user={current_user.id}")
    use_case = DeleteRowUseCase(vault_repo, table_repo, row_repo)

    await use_case.execute(current_user.id, slug, table_slug, row_id)


# CSV Import/Export endpoints
@router.post(
    "/vaults/{slug}/tables/import/csv",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_csv(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
    file: UploadFile = File(...),
    table_name: str | None = Query(default=None, description="Name for the new table"),
    delimiter: str = Query(default=",", description="CSV delimiter"),
    has_header: bool = Query(default=True, description="Whether CSV has header row"),
) -> TableResponse:
    """Import CSV file to create a new table."""
    logger.info(f"POST /vaults/{slug}/tables/import/csv file={file.filename} user={current_user.id}")
    use_case = ImportCsvUseCase(vault_repo, table_repo, row_repo)

    content = await file.read()

    # Use filename as table name if not provided
    name = table_name or (file.filename.rsplit(".", 1)[0] if file.filename else "Imported Table")

    table = await use_case.execute(
        current_user.id,
        slug,
        content,
        table_name=name,
        delimiter=delimiter,
        has_header=has_header,
    )

    return TableResponse(
        id=table.id,
        name=table.name,
        slug=table.slug,
        description=table.description,
        columns=[
            ColumnResponse(
                name=col.name,
                type=col.type,
                required=col.required,
                unique=col.unique,
                default=col.default,
                description=col.description,
                reference_table=col.reference_table,
                reference_column=col.reference_column,
                array_type=col.array_type,
                formula=col.formula,
            )
            for col in table.columns
        ],
        row_count=table.row_count,
        created_at=table.created_at,
        updated_at=table.updated_at,
    )


@router.post("/vaults/{slug}/tables/{table_slug}/import/csv")
async def append_csv(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
    file: UploadFile = File(...),
    delimiter: str = Query(default=",", description="CSV delimiter"),
    has_header: bool = Query(default=True, description="Whether CSV has header row"),
) -> dict:
    """Append CSV data to an existing table."""
    logger.info(f"POST /vaults/{slug}/tables/{table_slug}/import/csv file={file.filename} user={current_user.id}")
    use_case = AppendCsvUseCase(vault_repo, table_repo, row_repo)

    content = await file.read()

    imported, skipped = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        content,
        delimiter=delimiter,
        has_header=has_header,
    )

    return {
        "imported": imported,
        "skipped": skipped,
    }


@router.get("/vaults/{slug}/tables/{table_slug}/export/csv")
async def export_csv(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
    delimiter: str = Query(default=",", description="CSV delimiter"),
) -> Response:
    """Export table data as CSV."""
    logger.debug(f"GET /vaults/{slug}/tables/{table_slug}/export/csv user={current_user.id}")
    use_case = ExportCsvUseCase(vault_repo, table_repo, row_repo)

    csv_content, filename = await use_case.execute(
        current_user.id,
        slug,
        table_slug,
        delimiter=delimiter,
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# Document-Table Integration endpoints
@router.get("/vaults/{slug}/tables/{table_slug}/documents")
async def get_documents_referencing_table(
    slug: str,
    table_slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    document_repo: DocumentRepoDep,
    document_table_link_repo: DocumentTableLinkRepoDep,
) -> dict:
    """Get documents that reference this table."""
    logger.debug(f"GET /vaults/{slug}/tables/{table_slug}/documents user={current_user.id}")
    from app.domain.exceptions import VaultNotFoundError, TableNotFoundError

    # Get vault
    vault = await vault_repo.get_by_slug(current_user.id, slug)
    if not vault:
        raise VaultNotFoundError(slug=slug)

    # Get table
    table = await table_repo.get_by_slug(vault.id, table_slug)
    if not table:
        raise TableNotFoundError(slug=table_slug)

    # Get document links to this table
    links = await document_table_link_repo.get_by_table(table.id)

    # Get unique documents
    doc_ids = list(set(link.document_id for link in links))
    documents = []
    for doc_id in doc_ids:
        doc = await document_repo.get_by_id(doc_id)
        if doc:
            documents.append({
                "id": str(doc.id),
                "title": doc.title,
                "path": doc.path,
            })

    return {
        "documents": documents,
        "total": len(documents),
    }


# Query endpoint
@router.post("/vaults/{slug}/query")
async def execute_query(
    slug: str,
    current_user: CurrentUserDep,
    vault_repo: VaultRepoDep,
    table_repo: TableRepoDep,
    row_repo: RowRepoDep,
    query: dict,
) -> dict:
    """Execute a dataview-style query.

    Query format:
        {
            "query": "TABLE name, email FROM contacts WHERE status = 'active' SORT name ASC LIMIT 10"
        }

    Supported syntax:
        - TABLE col1, col2 FROM table_name
        - TABLE * FROM table_name
        - WHERE column = 'value'
        - WHERE column != 'value'
        - WHERE column > 10
        - WHERE column LIKE '%pattern%'
        - WHERE column IN ('a', 'b', 'c')
        - SORT column ASC|DESC
        - LIMIT n
        - OFFSET n
    """
    query_string = query.get("query", "")
    logger.debug(f"POST /vaults/{slug}/query query={query_string!r} user={current_user.id}")

    if not query_string:
        class MissingQueryError(DomainException):
            code = "MISSING_QUERY"
            http_status = 400

        raise MissingQueryError("Query string is required")

    use_case = ExecuteQueryUseCase(vault_repo, table_repo, row_repo)

    result = await use_case.execute(current_user.id, slug, query_string)

    return result
