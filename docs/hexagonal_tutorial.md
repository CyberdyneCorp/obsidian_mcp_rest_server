# Hexagonal Architecture Tutorial

A practical guide to implementing Hexagonal Architecture (Ports and Adapters) with FastAPI and Python for the AI Bridge Platform.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts](#2-core-concepts)
3. [Layer Structure](#3-layer-structure)
4. [Domain Layer](#4-domain-layer)
5. [Application Layer](#5-application-layer)
6. [Infrastructure Layer](#6-infrastructure-layer)
7. [API Layer](#7-api-layer)
8. [Dependency Injection](#8-dependency-injection)
9. [Practical Examples](#9-practical-examples)
10. [Testing Strategy](#10-testing-strategy)
11. [Best Practices](#11-best-practices)
12. [Common Mistakes](#12-common-mistakes)

---

## 1. Introduction

### What is Hexagonal Architecture?

Hexagonal Architecture (also known as Ports and Adapters) is an architectural pattern that isolates the core business logic from external concerns like databases, APIs, and frameworks.

```
                    ┌─────────────────────────────────────┐
                    │           Infrastructure            │
                    │  ┌─────────────────────────────┐    │
                    │  │        Application          │    │
                    │  │  ┌─────────────────────┐    │    │
    HTTP Request ───┼──┼─►│       Domain        │◄───┼────┼─── Database
                    │  │  │                     │    │    │
    WebSocket ──────┼──┼─►│   (Pure Business    │◄───┼────┼─── Redis
                    │  │  │      Logic)         │    │    │
    CLI ────────────┼──┼─►│                     │◄───┼────┼─── S3
                    │  │  └─────────────────────┘    │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
                              Ports & Adapters
```

### Why Hexagonal for AI Bridge Platform?

1. **Framework Independence** - Domain logic doesn't depend on FastAPI
2. **Database Independence** - Switch from PostgreSQL without changing business logic
3. **LLM Provider Independence** - Swap OpenAI for AminiLLM transparently
4. **Testability** - Test business logic without infrastructure
5. **MCP Tool Isolation** - Tool execution is an adapter, not core logic

### Key Principles

- **The Domain is the center** - All dependencies point inward
- **Ports define interfaces** - Abstract contracts for external communication
- **Adapters implement ports** - Concrete implementations for specific technologies
- **Dependency Inversion** - High-level modules don't depend on low-level modules

---

## 2. Core Concepts

### Ports

Ports are interfaces (abstract classes in Python) that define how the application communicates with the outside world.

**Inbound Ports (Driving):**
- Define what the application can do
- Implemented by Use Cases
- Called by adapters (API, CLI, etc.)

**Outbound Ports (Driven):**
- Define what the application needs
- Implemented by Infrastructure
- Called by Use Cases

```python
# Outbound Port - what the application needs
from abc import ABC, abstractmethod

class ChatRepository(ABC):
    @abstractmethod
    async def get_by_id(self, chat_id: str) -> Chat | None:
        pass

    @abstractmethod
    async def save(self, chat: Chat) -> Chat:
        pass
```

### Adapters

Adapters are implementations of ports for specific technologies.

**Inbound Adapters (Driving):**
- FastAPI routes
- CLI commands
- WebSocket handlers
- Message queue consumers

**Outbound Adapters (Driven):**
- PostgreSQL repository
- Redis cache
- S3 storage
- OpenAI/AminiLLM clients
- Aminichain blockchain client

```python
# Outbound Adapter - PostgreSQL implementation
class PostgresChatRepository(ChatRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chat_id: str) -> Chat | None:
        result = await self.session.execute(
            select(ChatModel).where(ChatModel.id == chat_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def save(self, chat: Chat) -> Chat:
        model = self._to_model(chat)
        self.session.add(model)
        await self.session.flush()
        return self._to_entity(model)
```

---

## 3. Layer Structure

### Directory Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry
│   ├── config.py                    # Configuration management
│   │
│   ├── domain/                      # Domain Layer (innermost)
│   │   ├── __init__.py
│   │   ├── entities/                # Domain entities
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── chat.py
│   │   │   ├── document.py
│   │   │   ├── folder.py
│   │   │   └── tool.py
│   │   ├── value_objects/           # Immutable value types
│   │   │   ├── __init__.py
│   │   │   ├── wallet_address.py
│   │   │   ├── permission.py
│   │   │   └── message_content.py
│   │   ├── exceptions.py            # Domain exceptions
│   │   ├── events.py                # Domain events
│   │   └── services.py              # Domain services
│   │
│   ├── application/                 # Application Layer
│   │   ├── __init__.py
│   │   ├── use_cases/               # Business operations
│   │   │   ├── __init__.py
│   │   │   ├── chat/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_thread.py
│   │   │   │   ├── send_message.py
│   │   │   │   └── attach_tool.py
│   │   │   ├── document/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_document.py
│   │   │   │   └── update_content.py
│   │   │   └── auth/
│   │   │       ├── __init__.py
│   │   │       └── verify_wallet.py
│   │   ├── interfaces/              # Port definitions
│   │   │   ├── __init__.py
│   │   │   ├── repositories.py      # Data access ports
│   │   │   ├── llm_provider.py      # LLM port
│   │   │   ├── storage.py           # File storage port
│   │   │   ├── blockchain.py        # Blockchain port
│   │   │   └── mcp_executor.py      # MCP tool execution port
│   │   └── dto/                     # Data transfer objects
│   │       ├── __init__.py
│   │       ├── chat_dto.py
│   │       └── document_dto.py
│   │
│   ├── infrastructure/              # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py        # Database setup
│   │   │   ├── models/              # SQLAlchemy models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── chat.py
│   │   │   │   └── document.py
│   │   │   └── repositories/        # Repository implementations
│   │   │       ├── __init__.py
│   │   │       ├── chat_repository.py
│   │   │       └── document_repository.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── openai_adapter.py
│   │   │   └── amini_adapter.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── s3_adapter.py
│   │   ├── blockchain/
│   │   │   ├── __init__.py
│   │   │   └── aminichain_adapter.py
│   │   └── mcp/
│   │       ├── __init__.py
│   │       └── tool_executor.py
│   │
│   └── api/                         # API Layer (Inbound Adapter)
│       ├── __init__.py
│       ├── dependencies.py          # FastAPI dependencies (DI)
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   └── error_handler.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── chats.py
│       │   ├── documents.py
│       │   └── tools.py
│       └── schemas/                 # Pydantic request/response
│           ├── __init__.py
│           ├── auth.py
│           ├── chat.py
│           └── document.py
```

### Dependency Flow

```
API Layer → Application Layer → Domain Layer
    ↓              ↓
Infrastructure Layer (implements Application interfaces)
```

**Rules:**
- Domain imports nothing from other layers
- Application imports only from Domain
- Infrastructure imports from Application (interfaces) and Domain (entities)
- API imports from Application (use cases) and Infrastructure (for DI)

---

## 4. Domain Layer

The Domain layer contains pure business logic with no external dependencies.

### Entities

Entities are objects with identity that encapsulate business rules.

```python
# app/domain/entities/chat.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from app.domain.entities.message import Message
from app.domain.exceptions import DomainError


@dataclass
class ChatThread:
    """Chat thread entity with business rules."""

    id: UUID
    user_id: UUID
    title: str
    folder_id: Optional[UUID] = None
    messages: List[Message] = field(default_factory=list)
    tool_ids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Business rules as methods

    def add_message(self, message: Message) -> None:
        """Add a message to the thread."""
        if message.thread_id != self.id:
            raise DomainError("Message does not belong to this thread")

        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def attach_tool(self, tool_id: UUID) -> None:
        """Attach a tool to the chat."""
        if tool_id in self.tool_ids:
            raise DomainError(f"Tool {tool_id} is already attached")

        self.tool_ids.append(tool_id)
        self.updated_at = datetime.utcnow()

    def detach_tool(self, tool_id: UUID) -> None:
        """Detach a tool from the chat."""
        if tool_id not in self.tool_ids:
            raise DomainError(f"Tool {tool_id} is not attached")

        self.tool_ids.remove(tool_id)
        self.updated_at = datetime.utcnow()

    def can_user_access(self, user_id: UUID) -> bool:
        """Check if user can access this chat."""
        return self.user_id == user_id

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def last_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    @staticmethod
    def create(user_id: UUID, title: str, folder_id: Optional[UUID] = None) -> "ChatThread":
        """Factory method to create a new chat thread."""
        return ChatThread(
            id=uuid4(),
            user_id=user_id,
            title=title,
            folder_id=folder_id,
        )
```

### Value Objects

Value objects are immutable objects defined by their attributes, not identity.

```python
# app/domain/value_objects/wallet_address.py
from dataclasses import dataclass
import re

from app.domain.exceptions import ValidationError


@dataclass(frozen=True)
class WalletAddress:
    """Ethereum wallet address value object."""

    value: str

    def __post_init__(self):
        if not self._is_valid_address(self.value):
            raise ValidationError(f"Invalid wallet address: {self.value}")

    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """Validate Ethereum address format."""
        pattern = r"^0x[a-fA-F0-9]{40}$"
        return bool(re.match(pattern, address))

    def to_checksum(self) -> str:
        """Convert to checksum address format."""
        # Implementation using Web3 or manual checksum
        return self.value  # Simplified

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WalletAddress):
            return False
        return self.value.lower() == other.value.lower()

    def __hash__(self) -> int:
        return hash(self.value.lower())
```

```python
# app/domain/value_objects/permission.py
from dataclasses import dataclass
from enum import Enum
from typing import Set


class PermissionLevel(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3


@dataclass(frozen=True)
class Permission:
    """User permission value object."""

    level: PermissionLevel
    tool_access: Set[str]
    max_documents: int
    max_chats: int
    rag_queries_per_day: int

    def can_access_tool(self, tool_id: str) -> bool:
        return tool_id in self.tool_access or self.level == PermissionLevel.ADMIN

    def can_create_document(self, current_count: int) -> bool:
        return current_count < self.max_documents or self.level == PermissionLevel.ADMIN

    def is_admin(self) -> bool:
        return self.level == PermissionLevel.ADMIN
```

### Domain Exceptions

```python
# app/domain/exceptions.py

class DomainError(Exception):
    """Base domain exception."""
    pass


class ValidationError(DomainError):
    """Validation failed."""
    pass


class EntityNotFoundError(DomainError):
    """Entity not found."""

    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class AccessDeniedError(DomainError):
    """Access denied."""
    pass


class QuotaExceededError(DomainError):
    """User quota exceeded."""

    def __init__(self, resource: str, limit: int):
        self.resource = resource
        self.limit = limit
        super().__init__(f"Quota exceeded for {resource}. Limit: {limit}")
```

### Domain Services

For business logic that doesn't belong to a single entity:

```python
# app/domain/services.py
from typing import List
from app.domain.entities.chat import ChatThread, Message
from app.domain.value_objects.permission import Permission


class ChatDomainService:
    """Domain service for chat-related business logic."""

    @staticmethod
    def can_send_message(
        chat: ChatThread,
        user_permission: Permission,
        daily_message_count: int
    ) -> bool:
        """Check if user can send a message."""
        if user_permission.is_admin():
            return True

        # Check daily limit (example business rule)
        daily_limit = 1000
        if daily_message_count >= daily_limit:
            return False

        return True

    @staticmethod
    def build_context_window(
        messages: List[Message],
        max_tokens: int = 4000
    ) -> List[Message]:
        """Build context window respecting token limit."""
        # Simple implementation - take most recent messages
        context = []
        total_tokens = 0

        for message in reversed(messages):
            message_tokens = len(message.content) // 4  # Rough estimate
            if total_tokens + message_tokens > max_tokens:
                break
            context.insert(0, message)
            total_tokens += message_tokens

        return context
```

---

## 5. Application Layer

The Application layer orchestrates use cases and defines ports.

### Port Interfaces

```python
# app/application/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat import ChatThread
from app.domain.entities.user import User


class ChatRepository(ABC):
    """Port for chat data access."""

    @abstractmethod
    async def get_by_id(self, chat_id: UUID) -> Optional[ChatThread]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: UUID, limit: int = 50) -> List[ChatThread]:
        pass

    @abstractmethod
    async def save(self, chat: ChatThread) -> ChatThread:
        pass

    @abstractmethod
    async def delete(self, chat_id: UUID) -> None:
        pass


class UserRepository(ABC):
    """Port for user data access."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_wallet(self, wallet_address: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass
```

```python
# app/application/interfaces/llm_provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional


@dataclass
class LLMMessage:
    role: str  # 'user', 'assistant', 'system'
    content: str


@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[List[dict]] = None
    usage: Optional[dict] = None


class LLMProvider(ABC):
    """Port for LLM interactions."""

    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Get a completion from the LLM."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion from the LLM."""
        pass
```

```python
# app/application/interfaces/blockchain.py
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.value_objects.wallet_address import WalletAddress
from app.domain.value_objects.permission import Permission


@dataclass
class NFTMetadata:
    token_id: int
    contract_address: str
    metadata: dict


class BlockchainProvider(ABC):
    """Port for blockchain interactions."""

    @abstractmethod
    async def verify_signature(
        self,
        message: str,
        signature: str,
        wallet_address: WalletAddress,
    ) -> bool:
        """Verify a wallet signature."""
        pass

    @abstractmethod
    async def get_nft_holdings(
        self,
        wallet_address: WalletAddress,
        contract_address: str,
    ) -> List[NFTMetadata]:
        """Get NFTs owned by wallet."""
        pass

    @abstractmethod
    async def extract_permissions(
        self,
        wallet_address: WalletAddress,
    ) -> Permission:
        """Extract permissions from NFT holdings."""
        pass
```

### Use Cases

Use cases orchestrate business operations:

```python
# app/application/use_cases/chat/send_message.py
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID

from app.domain.entities.chat import ChatThread, Message
from app.domain.entities.user import User
from app.domain.exceptions import EntityNotFoundError, AccessDeniedError
from app.domain.services import ChatDomainService
from app.application.interfaces.repositories import ChatRepository, UserRepository
from app.application.interfaces.llm_provider import LLMProvider, LLMMessage
from app.application.interfaces.mcp_executor import MCPExecutor


@dataclass
class SendMessageInput:
    chat_id: UUID
    user_id: UUID
    content: str


@dataclass
class SendMessageOutput:
    user_message: Message
    assistant_message: Message
    tool_calls: Optional[List[dict]] = None


class SendMessageUseCase:
    """Use case for sending a chat message."""

    def __init__(
        self,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        llm_provider: LLMProvider,
        mcp_executor: MCPExecutor,
    ):
        self.chat_repository = chat_repository
        self.user_repository = user_repository
        self.llm_provider = llm_provider
        self.mcp_executor = mcp_executor

    async def execute(self, input: SendMessageInput) -> SendMessageOutput:
        # 1. Load chat and user
        chat = await self.chat_repository.get_by_id(input.chat_id)
        if not chat:
            raise EntityNotFoundError("ChatThread", str(input.chat_id))

        user = await self.user_repository.get_by_id(input.user_id)
        if not user:
            raise EntityNotFoundError("User", str(input.user_id))

        # 2. Check access
        if not chat.can_user_access(input.user_id):
            raise AccessDeniedError("User cannot access this chat")

        # 3. Create user message
        user_message = Message.create(
            thread_id=chat.id,
            role="user",
            content=input.content,
        )
        chat.add_message(user_message)

        # 4. Build LLM context
        context = ChatDomainService.build_context_window(chat.messages)
        llm_messages = [
            LLMMessage(role=m.role, content=m.content)
            for m in context
        ]

        # 5. Get attached tools
        tools = await self._get_tool_schemas(chat.tool_ids)

        # 6. Call LLM
        response = await self.llm_provider.complete(
            messages=llm_messages,
            tools=tools if tools else None,
        )

        # 7. Execute tool calls if any
        tool_results = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = await self.mcp_executor.execute(
                    tool_id=tool_call["tool_id"],
                    input=tool_call["input"],
                    user_id=input.user_id,
                )
                tool_results.append(result)

        # 8. Create assistant message
        assistant_message = Message.create(
            thread_id=chat.id,
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls,
        )
        chat.add_message(assistant_message)

        # 9. Save chat
        await self.chat_repository.save(chat)

        return SendMessageOutput(
            user_message=user_message,
            assistant_message=assistant_message,
            tool_calls=response.tool_calls,
        )

    async def _get_tool_schemas(self, tool_ids: List[UUID]) -> List[dict]:
        """Get MCP tool schemas for LLM."""
        schemas = []
        for tool_id in tool_ids:
            schema = await self.mcp_executor.get_tool_schema(tool_id)
            if schema:
                schemas.append(schema)
        return schemas
```

```python
# app/application/use_cases/auth/verify_wallet.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
import secrets

from app.domain.entities.user import User
from app.domain.value_objects.wallet_address import WalletAddress
from app.domain.exceptions import ValidationError
from app.application.interfaces.repositories import UserRepository
from app.application.interfaces.blockchain import BlockchainProvider


@dataclass
class VerifyWalletInput:
    wallet_address: str
    message: str
    signature: str
    nonce: str


@dataclass
class VerifyWalletOutput:
    user: User
    access_token: str
    refresh_token: str
    expires_at: datetime


class VerifyWalletUseCase:
    """Use case for wallet-based authentication."""

    def __init__(
        self,
        user_repository: UserRepository,
        blockchain_provider: BlockchainProvider,
        token_service: "TokenService",  # Another application service
        nonce_store: "NonceStore",
    ):
        self.user_repository = user_repository
        self.blockchain_provider = blockchain_provider
        self.token_service = token_service
        self.nonce_store = nonce_store

    async def execute(self, input: VerifyWalletInput) -> VerifyWalletOutput:
        # 1. Validate wallet address
        wallet = WalletAddress(input.wallet_address)

        # 2. Verify nonce is valid and not expired
        if not await self.nonce_store.verify_and_consume(input.nonce, wallet):
            raise ValidationError("Invalid or expired nonce")

        # 3. Verify signature
        is_valid = await self.blockchain_provider.verify_signature(
            message=input.message,
            signature=input.signature,
            wallet_address=wallet,
        )
        if not is_valid:
            raise ValidationError("Invalid signature")

        # 4. Get or create user
        user = await self.user_repository.get_by_wallet(str(wallet))
        if not user:
            # Extract permissions from NFT
            permissions = await self.blockchain_provider.extract_permissions(wallet)

            user = User.create(
                wallet_address=wallet,
                permissions=permissions,
            )
            user = await self.user_repository.save(user)

        # 5. Generate tokens
        access_token = self.token_service.create_access_token(user)
        refresh_token = self.token_service.create_refresh_token(user)

        return VerifyWalletOutput(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
        )
```

### DTOs

Data Transfer Objects for input/output:

```python
# app/application/dto/chat_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID


@dataclass
class ChatThreadDTO:
    id: UUID
    title: str
    folder_id: Optional[UUID]
    message_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class MessageDTO:
    id: UUID
    role: str
    content: str
    tool_calls: Optional[List[dict]]
    created_at: datetime


@dataclass
class ChatDetailDTO:
    thread: ChatThreadDTO
    messages: List[MessageDTO]
    attached_tools: List[UUID]
```

---

## 6. Infrastructure Layer

The Infrastructure layer implements ports with specific technologies.

### Database Repository

```python
# app/infrastructure/database/repositories/chat_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.chat import ChatThread, Message
from app.application.interfaces.repositories import ChatRepository
from app.infrastructure.database.models.chat import ChatThreadModel, MessageModel


class PostgresChatRepository(ChatRepository):
    """PostgreSQL implementation of ChatRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chat_id: UUID) -> Optional[ChatThread]:
        result = await self.session.execute(
            select(ChatThreadModel)
            .options(selectinload(ChatThreadModel.messages))
            .where(ChatThreadModel.id == chat_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user(self, user_id: UUID, limit: int = 50) -> List[ChatThread]:
        result = await self.session.execute(
            select(ChatThreadModel)
            .where(ChatThreadModel.user_id == user_id)
            .order_by(ChatThreadModel.updated_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def save(self, chat: ChatThread) -> ChatThread:
        model = await self._get_or_create_model(chat)
        self._update_model(model, chat)

        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        return self._to_entity(model)

    async def delete(self, chat_id: UUID) -> None:
        result = await self.session.execute(
            select(ChatThreadModel).where(ChatThreadModel.id == chat_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)

    # Mapping methods

    def _to_entity(self, model: ChatThreadModel) -> ChatThread:
        """Convert SQLAlchemy model to domain entity."""
        return ChatThread(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            folder_id=model.folder_id,
            messages=[self._message_to_entity(m) for m in model.messages],
            tool_ids=model.tool_ids or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _message_to_entity(self, model: MessageModel) -> Message:
        return Message(
            id=model.id,
            thread_id=model.thread_id,
            role=model.role,
            content=model.content,
            tool_calls=model.tool_calls,
            created_at=model.created_at,
        )

    def _update_model(self, model: ChatThreadModel, entity: ChatThread) -> None:
        """Update model from entity."""
        model.title = entity.title
        model.folder_id = entity.folder_id
        model.tool_ids = entity.tool_ids
        model.updated_at = entity.updated_at

        # Handle messages
        existing_ids = {m.id for m in model.messages}
        for message in entity.messages:
            if message.id not in existing_ids:
                model.messages.append(MessageModel(
                    id=message.id,
                    thread_id=message.thread_id,
                    role=message.role,
                    content=message.content,
                    tool_calls=message.tool_calls,
                    created_at=message.created_at,
                ))

    async def _get_or_create_model(self, entity: ChatThread) -> ChatThreadModel:
        result = await self.session.execute(
            select(ChatThreadModel).where(ChatThreadModel.id == entity.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            model = ChatThreadModel(
                id=entity.id,
                user_id=entity.user_id,
                title=entity.title,
                folder_id=entity.folder_id,
                created_at=entity.created_at,
            )

        return model
```

### LLM Adapter

```python
# app/infrastructure/llm/openai_adapter.py
from typing import AsyncIterator, List, Optional
import openai
from openai import AsyncOpenAI

from app.application.interfaces.llm_provider import LLMProvider, LLMMessage, LLMResponse


class OpenAIAdapter(LLMProvider):
    """OpenAI implementation of LLMProvider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = self._format_tools(tools)

        response = await self.client.chat.completions.create(**kwargs)

        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "tool_id": tc.function.name,
                    "input": tc.function.arguments,
                }
                for tc in choice.message.tool_calls
            ]

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        kwargs = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": temperature,
            "stream": True,
        }

        if tools:
            kwargs["tools"] = self._format_tools(tools)

        stream = await self.client.chat.completions.create(**kwargs)

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _format_tools(self, tools: List[dict]) -> List[dict]:
        """Format tools for OpenAI API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]
```

```python
# app/infrastructure/llm/amini_adapter.py
from typing import AsyncIterator, List, Optional
import httpx

from app.application.interfaces.llm_provider import LLMProvider, LLMMessage, LLMResponse


class AminiLLMAdapter(LLMProvider):
    """AminiLLM implementation of LLMProvider."""

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    async def complete(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools

        response = await self.client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()

        data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            tool_calls=data["choices"][0]["message"].get("tool_calls"),
            usage=data.get("usage"),
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        async with self.client.stream("POST", "/v1/chat/completions", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data != "[DONE]":
                        import json
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
```

### SQLAlchemy Models

```python
# app/infrastructure/database/models/chat.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy import ForeignKey, String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY

from app.infrastructure.database.models.base import Base


class ChatThreadModel(Base):
    __tablename__ = "chat_threads"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255))
    folder_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    tool_ids: Mapped[Optional[List[UUID]]] = mapped_column(ARRAY(PG_UUID(as_uuid=True)), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages: Mapped[List["MessageModel"]] = relationship(back_populates="thread", cascade="all, delete-orphan")
    user: Mapped["UserModel"] = relationship(back_populates="chats")


class MessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    thread_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("chat_threads.id"))
    role: Mapped[str] = mapped_column(String(20))  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    thread: Mapped["ChatThreadModel"] = relationship(back_populates="messages")
```

---

## 7. API Layer

The API layer is an inbound adapter that exposes the application via HTTP.

### FastAPI Routes

```python
# app/api/routes/chats.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_current_user, get_send_message_use_case
from app.api.schemas.chat import (
    ChatThreadResponse,
    CreateChatRequest,
    SendMessageRequest,
    MessageResponse,
)
from app.domain.entities.user import User
from app.domain.exceptions import EntityNotFoundError, AccessDeniedError
from app.application.use_cases.chat.send_message import SendMessageUseCase, SendMessageInput

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: UUID,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    """Send a message to a chat thread."""
    try:
        input_data = SendMessageInput(
            chat_id=chat_id,
            user_id=current_user.id,
            content=request.content,
        )

        output = await use_case.execute(input_data)

        return MessageResponse(
            user_message=output.user_message,
            assistant_message=output.assistant_message,
            tool_calls=output.tool_calls,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CHAT_NOT_FOUND", "message": str(e)},
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCESS_DENIED", "message": str(e)},
        )


@router.get("/{chat_id}/stream")
async def stream_chat(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: "StreamMessageUseCase" = Depends(get_stream_message_use_case),
):
    """Stream chat responses via SSE."""
    async def event_generator():
        async for chunk in use_case.execute(chat_id, current_user.id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
```

### Pydantic Schemas

```python
# app/api/schemas/chat.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CreateChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    folder_id: Optional[UUID] = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    tool_calls: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatThreadResponse(BaseModel):
    id: UUID
    title: str
    folder_id: Optional[UUID]
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## 8. Dependency Injection

### FastAPI Dependencies

```python
# app/api/dependencies.py
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.repositories.chat_repository import PostgresChatRepository
from app.infrastructure.database.repositories.user_repository import PostgresUserRepository
from app.infrastructure.llm.openai_adapter import OpenAIAdapter
from app.infrastructure.llm.amini_adapter import AminiLLMAdapter
from app.application.interfaces.repositories import ChatRepository, UserRepository
from app.application.interfaces.llm_provider import LLMProvider
from app.application.use_cases.chat.send_message import SendMessageUseCase
from app.domain.entities.user import User


security = HTTPBearer()


# Database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Repositories
async def get_chat_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ChatRepository:
    return PostgresChatRepository(session)


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return PostgresUserRepository(session)


# LLM Provider
@lru_cache()
def get_llm_provider(
    settings: Settings = Depends(get_settings),
) -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIAdapter(
            api_key=settings.openai_api_key,
            model="gpt-4",
        )
    elif settings.llm_provider == "amini":
        return AminiLLMAdapter(
            endpoint=settings.amini_llm_endpoint,
            api_key=settings.amini_llm_api_key,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


# Use Cases
async def get_send_message_use_case(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> SendMessageUseCase:
    return SendMessageUseCase(
        chat_repository=chat_repository,
        user_repository=user_repository,
        llm_provider=llm_provider,
        mcp_executor=...,  # Inject MCP executor
    )


# Current User
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "Invalid token"},
        )

    user = await user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": "User not found"},
        )

    return user
```

---

## 9. Practical Examples

### Example: Complete Flow for Creating a Document

```python
# 1. Domain Entity
# app/domain/entities/document.py

@dataclass
class Document:
    id: UUID
    user_id: UUID
    title: str
    content: str
    folder_id: Optional[UUID]
    version: int
    created_at: datetime
    updated_at: datetime

    def update_content(self, content: str) -> None:
        if content == self.content:
            return

        self.content = content
        self.version += 1
        self.updated_at = datetime.utcnow()

    @staticmethod
    def create(user_id: UUID, title: str, folder_id: Optional[UUID] = None) -> "Document":
        return Document(
            id=uuid4(),
            user_id=user_id,
            title=title,
            content="",
            folder_id=folder_id,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
```

```python
# 2. Port Interface
# app/application/interfaces/repositories.py

class DocumentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        pass

    @abstractmethod
    async def save(self, document: Document) -> Document:
        pass
```

```python
# 3. Use Case
# app/application/use_cases/document/create_document.py

@dataclass
class CreateDocumentInput:
    user_id: UUID
    title: str
    folder_id: Optional[UUID] = None


class CreateDocumentUseCase:
    def __init__(
        self,
        document_repository: DocumentRepository,
        user_repository: UserRepository,
    ):
        self.document_repository = document_repository
        self.user_repository = user_repository

    async def execute(self, input: CreateDocumentInput) -> Document:
        # Check user exists and has permission
        user = await self.user_repository.get_by_id(input.user_id)
        if not user:
            raise EntityNotFoundError("User", str(input.user_id))

        doc_count = await self.document_repository.count_by_user(input.user_id)
        if not user.permissions.can_create_document(doc_count):
            raise QuotaExceededError("documents", user.permissions.max_documents)

        # Create document
        document = Document.create(
            user_id=input.user_id,
            title=input.title,
            folder_id=input.folder_id,
        )

        return await self.document_repository.save(document)
```

```python
# 4. Infrastructure Adapter
# app/infrastructure/database/repositories/document_repository.py

class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, doc_id: UUID) -> Optional[Document]:
        result = await self.session.execute(
            select(DocumentModel).where(DocumentModel.id == doc_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            user_id=document.user_id,
            title=document.title,
            content=document.content,
            folder_id=document.folder_id,
            version=document.version,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return document
```

```python
# 5. API Route
# app/api/routes/documents.py

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: CreateDocumentRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateDocumentUseCase = Depends(get_create_document_use_case),
):
    input_data = CreateDocumentInput(
        user_id=current_user.id,
        title=request.title,
        folder_id=request.folder_id,
    )

    document = await use_case.execute(input_data)

    return DocumentResponse.from_entity(document)
```

---

## 10. Testing Strategy

### Unit Testing Domain

```python
# tests/unit/domain/test_chat.py
import pytest
from uuid import uuid4

from app.domain.entities.chat import ChatThread, Message
from app.domain.exceptions import DomainError


class TestChatThread:
    def test_create_chat_thread(self):
        user_id = uuid4()
        chat = ChatThread.create(user_id=user_id, title="Test Chat")

        assert chat.user_id == user_id
        assert chat.title == "Test Chat"
        assert chat.message_count == 0

    def test_add_message(self):
        chat = ChatThread.create(user_id=uuid4(), title="Test")
        message = Message.create(thread_id=chat.id, role="user", content="Hello")

        chat.add_message(message)

        assert chat.message_count == 1
        assert chat.last_message == message

    def test_add_message_wrong_thread_raises(self):
        chat = ChatThread.create(user_id=uuid4(), title="Test")
        message = Message.create(thread_id=uuid4(), role="user", content="Hello")

        with pytest.raises(DomainError):
            chat.add_message(message)

    def test_attach_tool(self):
        chat = ChatThread.create(user_id=uuid4(), title="Test")
        tool_id = uuid4()

        chat.attach_tool(tool_id)

        assert tool_id in chat.tool_ids

    def test_attach_duplicate_tool_raises(self):
        chat = ChatThread.create(user_id=uuid4(), title="Test")
        tool_id = uuid4()
        chat.attach_tool(tool_id)

        with pytest.raises(DomainError):
            chat.attach_tool(tool_id)
```

### Unit Testing Use Cases

```python
# tests/unit/application/test_send_message.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.application.use_cases.chat.send_message import (
    SendMessageUseCase,
    SendMessageInput,
)
from app.domain.entities.chat import ChatThread
from app.domain.entities.user import User
from app.domain.exceptions import EntityNotFoundError, AccessDeniedError


@pytest.fixture
def mock_chat_repository():
    return AsyncMock()


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_llm_provider():
    return AsyncMock()


@pytest.fixture
def use_case(mock_chat_repository, mock_user_repository, mock_llm_provider):
    return SendMessageUseCase(
        chat_repository=mock_chat_repository,
        user_repository=mock_user_repository,
        llm_provider=mock_llm_provider,
        mcp_executor=AsyncMock(),
    )


class TestSendMessageUseCase:
    @pytest.mark.asyncio
    async def test_send_message_success(
        self, use_case, mock_chat_repository, mock_user_repository, mock_llm_provider
    ):
        # Arrange
        user_id = uuid4()
        chat_id = uuid4()

        user = User.create(wallet_address="0x123...", permissions=MagicMock())
        user.id = user_id

        chat = ChatThread.create(user_id=user_id, title="Test")
        chat.id = chat_id

        mock_user_repository.get_by_id.return_value = user
        mock_chat_repository.get_by_id.return_value = chat
        mock_llm_provider.complete.return_value = MagicMock(
            content="Hello!", tool_calls=None
        )

        # Act
        input_data = SendMessageInput(
            chat_id=chat_id, user_id=user_id, content="Hi"
        )
        result = await use_case.execute(input_data)

        # Assert
        assert result.user_message.content == "Hi"
        assert result.assistant_message.content == "Hello!"
        mock_chat_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_chat_not_found(
        self, use_case, mock_chat_repository
    ):
        mock_chat_repository.get_by_id.return_value = None

        input_data = SendMessageInput(
            chat_id=uuid4(), user_id=uuid4(), content="Hi"
        )

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(input_data)
```

### Integration Testing

```python
# tests/integration/test_chat_api.py
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_chat_and_send_message(
    async_client: AsyncClient,
    auth_headers: dict,
):
    # Create chat
    response = await async_client.post(
        "/api/v1/chats",
        json={"title": "Test Chat"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    chat_id = response.json()["id"]

    # Send message
    response = await async_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "Hello!"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "assistant_message" in response.json()
```

---

## 11. Best Practices

### DO:

1. **Keep domain pure** - No framework imports in domain layer
   ```python
   # Good
   from dataclasses import dataclass

   # Bad
   from sqlalchemy.orm import Mapped
   ```

2. **Use dependency injection everywhere**
   ```python
   # Good
   class SendMessageUseCase:
       def __init__(self, chat_repository: ChatRepository):
           self.chat_repository = chat_repository
   ```

3. **Define clear port interfaces**
   ```python
   # Good - specific, focused interface
   class ChatRepository(ABC):
       @abstractmethod
       async def get_by_id(self, id: UUID) -> Optional[Chat]: ...
   ```

4. **Map between layers explicitly**
   ```python
   # Good - explicit conversion
   def _to_entity(self, model: ChatModel) -> Chat:
       return Chat(id=model.id, ...)
   ```

5. **Handle errors in use cases**
   ```python
   # Good
   async def execute(self, input):
       chat = await self.repo.get_by_id(input.id)
       if not chat:
           raise EntityNotFoundError("Chat", input.id)
   ```

### DON'T:

1. **Don't leak infrastructure into domain**
   ```python
   # Bad - SQLAlchemy in domain
   class Chat:
       __tablename__ = "chats"
   ```

2. **Don't call repositories from domain**
   ```python
   # Bad - domain calling infrastructure
   class Chat:
       def save(self):
           repository.save(self)
   ```

3. **Don't share models across layers**
   ```python
   # Bad - returning SQLAlchemy model from use case
   return await self.session.execute(select(ChatModel))
   ```

4. **Don't put business logic in API layer**
   ```python
   # Bad - logic in route
   @router.post("/chats")
   async def create_chat(request):
       if len(request.title) > 100:  # Should be in domain
           raise HTTPException(...)
   ```

---

## 12. Common Mistakes

### Mistake 1: Anemic Domain Model

```python
# Bad - no behavior, just data
@dataclass
class Chat:
    id: UUID
    messages: List[Message]

# Service does all the work
class ChatService:
    def add_message(self, chat, message):
        chat.messages.append(message)
```

**Fix:** Put behavior in entities.

### Mistake 2: Leaky Abstractions

```python
# Bad - port exposes SQLAlchemy details
class ChatRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: UUID, session: AsyncSession) -> Chat:
        pass
```

**Fix:** Hide infrastructure details behind port.

### Mistake 3: Circular Dependencies

```
Domain → Application → Infrastructure
           ↑________________|
```

**Fix:** Use dependency inversion, infrastructure implements application interfaces.

### Mistake 4: Fat Use Cases

```python
# Bad - use case doing too much
class SendMessageUseCase:
    async def execute(self, input):
        # Validate user
        # Check permissions
        # Load chat
        # Build context
        # Call LLM
        # Execute tools
        # Save message
        # Send notification
        # Update analytics
        # ...
```

**Fix:** Split into smaller use cases or extract domain services.

---

## Summary

Hexagonal Architecture in AI Bridge Platform:

1. **Domain Layer** - Pure business logic, entities, value objects
2. **Application Layer** - Use cases, port interfaces, DTOs
3. **Infrastructure Layer** - Database, LLM, storage adapters
4. **API Layer** - FastAPI routes, schemas, middleware

Key benefits:
- **Testability** - Test business logic without infrastructure
- **Flexibility** - Swap LLM providers (OpenAI ↔ AminiLLM) without changing business logic
- **Maintainability** - Clear boundaries between concerns
- **Framework Independence** - Domain doesn't depend on FastAPI or SQLAlchemy

This architecture enables the platform to evolve independently at each layer while maintaining a stable, testable core.
